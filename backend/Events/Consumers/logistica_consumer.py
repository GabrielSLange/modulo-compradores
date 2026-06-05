import json
import logging
# pyrefly: ignore [missing-import]
from confluent_kafka import Consumer, KafkaException, KafkaError
from Config.env import get_env, get_env_list
from Data.database import SessionLocal
from Models.demanda_model import Demanda

logger = logging.getLogger(__name__)

EVENT_TYPE_STATUS_ATUALIZADO = "logistica_status_atualizado"
TOPICOS_LOGISTICA = get_env_list("KAFKA_TOPICOS_LOGISTICA", required=True)
KAFKA_BOOTSTRAP_SERVERS = get_env("KAFKA_BOOTSTRAP_SERVERS", required=True)
KAFKA_GROUP_ID_LOGISTICA = get_env("KAFKA_GROUP_ID_LOGISTICA", required=True)


def processar_evento_logistica(event_data: dict) -> None:
    """Processa eventos de atualização de status da Logística.

    Atualiza o campo status_frete da demanda local correspondente.
    """
    if event_data.get("eventType") != EVENT_TYPE_STATUS_ATUALIZADO:
        return

    p = event_data.get("payload", {})
    # O pedido_id na Logística corresponde ao id_demanda no nosso microsserviço
    id_demanda = p.get("pedido_id") or p.get("solicitacao_id")
    novo_status = p.get("status")

    if not id_demanda or not novo_status:
        logger.warning("Evento logistica_status_atualizado recebido sem pedido_id/solicitacao_id ou status no payload.")
        return

    with SessionLocal() as db:
        demanda = db.query(Demanda).filter(Demanda.id_demanda == id_demanda).first()
        if not demanda:
            logger.debug(f"Demanda {id_demanda} não encontrada para atualizar status de frete.")
            return

        # Atualiza o status do frete localmente
        demanda.status_frete = str(novo_status).upper().strip()
        
        # Se foi entregue, garante que o status da demanda também esteja como atendida
        if demanda.status_frete == "ENTREGUE":
            demanda.status = "atendida"

        db.commit()
        logger.info(f"Status do frete do pedido {id_demanda} atualizado para {demanda.status_frete} via Kafka.")


def iniciar_consumidor_logistica():
    conf = {
        'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
        'group.id': KAFKA_GROUP_ID_LOGISTICA,
        'auto.offset.reset': 'earliest'
    }

    consumer = Consumer(conf)
    consumer.subscribe(TOPICOS_LOGISTICA)

    logger.info(f"Consumidor de Logística iniciado. Escutando tópicos: {TOPICOS_LOGISTICA}")

    try:
        while True:
            msg = consumer.poll(timeout=1.0)

            if msg is None:
                continue

            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                else:
                    logger.error(f"Erro no Kafka (logistica): {msg.error()}")
                    continue

            try:
                event_data = json.loads(msg.value().decode('utf-8'))
                processar_evento_logistica(event_data)
            except json.JSONDecodeError as e:
                logger.error(f"Erro de decodificação JSON no offset {msg.offset()}: {e}")
            except Exception as e:
                logger.error(f"Erro ao processar mensagem de logística: {e}")

    except Exception as e:
        logger.error(f"Exception no loop do consumidor de logística: {e}")
    finally:
        consumer.close()
