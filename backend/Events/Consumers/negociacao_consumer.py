import json
import logging
# pyrefly: ignore [missing-import]
from confluent_kafka import Consumer, KafkaException, KafkaError
from Config.env import get_env, get_env_list
from Data.database import SessionLocal
from Data.fornecimento_database import FornecimentoSessionLocal
from Models.demanda_model import Demanda
from Services.demanda_service import DemandaService

logger = logging.getLogger(__name__)

EVENT_TYPE_NEGOCIACAO_FECHADA = get_env("KAFKA_EVENT_NEGOCIACAO_FECHADA", required=True)
TOPICOS_NEGOCIACAO = get_env_list("KAFKA_TOPICOS_NEGOCIACAO", required=True)
KAFKA_BOOTSTRAP_SERVERS = get_env("KAFKA_BOOTSTRAP_SERVERS", required=True)
KAFKA_GROUP_ID_NEGOCIACAO = get_env("KAFKA_GROUP_ID_NEGOCIACAO", required=True)


def processar_evento_negociacao(event_data: dict) -> None:
    """Processa um único evento Kafka de negociação fechada.

    Se o evento for válido, promove a demanda associada a pedido automaticamente.
    """
    if event_data.get("eventType") != EVENT_TYPE_NEGOCIACAO_FECHADA:
        return

    payload = event_data.get("payload", {})
    id_demanda = payload.get("id_demanda")
    if not id_demanda:
        logger.warning("Evento negociacao_fechada recebido sem id_demanda no payload.")
        return

    with SessionLocal() as db:
        demanda = db.query(Demanda).filter(Demanda.id_demanda == id_demanda).first()
        if not demanda:
            logger.warning(f"Demanda {id_demanda} não encontrada no banco de dados local.")
            return

        if demanda.is_pedido:
            logger.info(f"Demanda {id_demanda} já foi promovida a pedido. Ignorando evento.")
            return

        with FornecimentoSessionLocal() as fornecimento_db:
            try:
                DemandaService.promover_para_pedido(
                    db=db,
                    fornecimento_db=fornecimento_db,
                    id_demanda=id_demanda,
                    id_empresa_comprador=demanda.id_empresa_comprador
                )
                logger.info(f"Demanda {id_demanda} promovida a pedido automaticamente via Kafka (negociacao_fechada).")
            except Exception as e:
                logger.error(f"Erro ao promover demanda {id_demanda} para pedido via evento Kafka: {e}")


def iniciar_consumidor_negociacoes():
    conf = {
        'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
        'group.id': KAFKA_GROUP_ID_NEGOCIACAO,
        'auto.offset.reset': 'earliest'
    }

    consumer = Consumer(conf)
    consumer.subscribe(TOPICOS_NEGOCIACAO)

    logger.info(f"Consumidor de Negociações iniciado. Escutando tópicos: {TOPICOS_NEGOCIACAO}")

    try:
        while True:
            msg = consumer.poll(timeout=1.0)

            if msg is None:
                continue

            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                else:
                    logger.error(f"Erro no Kafka (negociacoes): {msg.error()}")
                    continue

            try:
                event_data = json.loads(msg.value().decode('utf-8'))
                processar_evento_negociacao(event_data)
            except json.JSONDecodeError as e:
                logger.error(f"Erro de decodificação JSON no offset {msg.offset()}: {e}")
            except Exception as e:
                logger.error(f"Erro ao processar mensagem de negociação: {e}")

    except Exception as e:
        logger.error(f"Exception no loop do consumidor de negociações: {e}")
    finally:
        consumer.close()
