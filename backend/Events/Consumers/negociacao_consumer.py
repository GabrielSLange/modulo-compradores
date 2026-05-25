import json
import logging

# pyrefly: ignore [missing-import]
from confluent_kafka import Consumer, KafkaError
from Config.env import get_env, get_env_list
from Data.database import SessionLocal
from Models.demanda_model import Demanda

logger = logging.getLogger(__name__)

# Defaults sensatos: se a var nao estiver no .env, o consumer ainda sobe.
# (Sao nomes de topico/grupo, nao segredos.)
EVENT_TYPE_NEGOCIACAO_FECHADA = get_env("KAFKA_EVENT_NEGOCIACAO_FECHADA", "negociacao_fechada")
TOPICOS_NEGOCIACAO = get_env_list("KAFKA_TOPICOS_NEGOCIACAO", ["negociacao_fechada"])
KAFKA_GROUP_ID_NEGOCIACAO = get_env("KAFKA_GROUP_ID_NEGOCIACAO", "modulo_compradores_negociacao")
KAFKA_BOOTSTRAP_SERVERS = get_env("KAFKA_BOOTSTRAP_SERVERS", required=True)

# Em modo "direto" nao ha leilao, entao vencedor_lance_id vem null MESMO tendo
# dado certo (venda direta automatica). Por isso "direto" sempre conta como fechado.
MODO_DIRETO = "direto"


def _negocio_fechou(modo: str | None, vencedor_lance_id: str | None) -> bool:
    """Decide se a negociacao virou pedido.

    Regra extraida do negociacao-service (_calcular_vencedor), NAO da conversa do
    grupo (que estava incompleta):
      - modo "direto"               -> venda direta automatica, SEMPRE fecha (vencedor_lance_id null)
      - leilao COM vencedor         -> fecha
      - leilao SEM vencedor (null)  -> NAO fecha (expirou sem lances)
    """
    if modo == MODO_DIRETO:
        return True
    return vencedor_lance_id is not None


def _motivo_recusa(motivo_fechamento: str | None) -> str:
    """Mensagem amigavel pro front exibir quando a negociacao nao virou pedido."""
    if motivo_fechamento == "expirado":
        return "Leilao encerrado sem lances vencedores."
    return f"Negociacao encerrada sem vencedor (motivo: {motivo_fechamento or 'desconhecido'})."


def processar_evento_negociacao(event_data: dict) -> None:
    """Processa um evento negociacao_fechada. Idempotente.

    Extraido pra permitir teste direto sem subir Kafka.
    """
    if event_data.get("eventType") != EVENT_TYPE_NEGOCIACAO_FECHADA:
        return

    payload = event_data.get("payload", {})
    id_demanda = payload.get("demanda_id")
    if not id_demanda:
        # Sem demanda_id nao ha como ligar o evento a uma demanda nossa.
        # RISCO CONHECIDO: confirmar com a Negociacao se demanda_id vem sempre preenchido.
        logger.warning(
            "negociacao_fechada sem demanda_id (processo_id=%s). Ignorando.",
            payload.get("processo_id"),
        )
        return

    modo = payload.get("modo")
    vencedor_lance_id = payload.get("vencedor_lance_id")
    motivo_fechamento = payload.get("motivo_fechamento")

    with SessionLocal() as db:
        demanda = db.query(Demanda).filter(Demanda.id_demanda == id_demanda).first()
        if not demanda:
            logger.info("Demanda %s nao encontrada para negociacao_fechada.", id_demanda)
            return

        if _negocio_fechou(modo, vencedor_lance_id):
            if demanda.is_pedido and demanda.status == "atendida":
                logger.info("negociacao_fechada duplicada (atendida) p/ demanda %s.", id_demanda)
                return
            demanda.is_pedido = True
            demanda.status = "atendida"
            demanda.motivo = None
            logger.info("Demanda %s atendida via negociacao (modo=%s).", id_demanda, modo)
        else:
            if demanda.status == "negado":
                logger.info("negociacao_fechada duplicada (negado) p/ demanda %s.", id_demanda)
                return
            demanda.status = "negado"
            demanda.motivo = _motivo_recusa(motivo_fechamento)
            logger.info(
                "Demanda %s negada (motivo_fechamento=%s).", id_demanda, motivo_fechamento
            )

        db.commit()


def iniciar_consumidor_negociacao():
    consumer = Consumer({
        "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
        "group.id": KAFKA_GROUP_ID_NEGOCIACAO,
        "auto.offset.reset": "earliest",
        "enable.auto.commit": False,
    })

    try:
        consumer.subscribe(TOPICOS_NEGOCIACAO)
        logger.info("Consumidor de Negociacao iniciado. Escutando: %s", TOPICOS_NEGOCIACAO)

        while True:
            msg = consumer.poll(timeout=1.0)

            if msg is None:
                continue

            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                logger.error("Erro no Kafka: %s", msg.error())
                continue

            try:
                event_data = json.loads(msg.value().decode("utf-8"))
                processar_evento_negociacao(event_data)
                consumer.commit(message=msg)  # so confirma o offset apos processar com sucesso
            except json.JSONDecodeError as exc:
                # Payload quebrado nao adianta reprocessar: confirma e segue.
                logger.error("JSON invalido no offset %d: %s", msg.offset(), exc)
                consumer.commit(message=msg)
            except Exception as exc:
                # NAO confirma o offset: deixa reprocessar no proximo restart
                # em vez de perder o evento por uma falha transitoria (ex: banco fora).
                logger.error("Erro ao processar negociacao_fechada: %s", exc)

    except KeyboardInterrupt:
        logger.info("Consumidor de Negociacao encerrado manualmente.")
    finally:
        consumer.close()
