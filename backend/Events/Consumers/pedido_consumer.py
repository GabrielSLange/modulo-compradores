import json
import logging
# pyrefly: ignore [missing-import]
from confluent_kafka import Consumer, KafkaException, KafkaError
from Config.env import get_env, get_env_list
from Data.database import SessionLocal
from Models.demanda_model import Demanda

logger = logging.getLogger(__name__)

EVENT_TYPE_PEDIDO_CRIADO = get_env("KAFKA_EVENT_PEDIDO_CRIADO", required=True)
KAFKA_SOURCE_PROPRIO = get_env("KAFKA_SOURCE") or get_env("SERVICE_NAME", required=True)
TOPICOS_PEDIDOS = get_env_list("KAFKA_TOPICOS_PEDIDOS", required=True)
KAFKA_BOOTSTRAP_SERVERS = get_env("KAFKA_BOOTSTRAP_SERVERS", required=True)
KAFKA_GROUP_ID_PEDIDOS = get_env("KAFKA_GROUP_ID_PEDIDOS", required=True)


def processar_evento_pedido(event_data: dict) -> None:
    """Processa um único evento Kafka de pedido. Idempotente.

    Extraído pra permitir testes diretos sem subir Kafka.
    """
    if event_data.get("eventType") != EVENT_TYPE_PEDIDO_CRIADO:
        return

    # Anti-loop: ignora pedido_criado publicado pela propria equipe 4
    # (caso do /promover, onde a gente eh quem cria o pedido).'
    if event_data.get("source") == KAFKA_SOURCE_PROPRIO:
        return

    payload = event_data.get("payload", {})
    id_demanda = payload.get("id_demanda")
    if not id_demanda:
        return

    with SessionLocal() as db:
        demanda = db.query(Demanda).filter(Demanda.id_demanda == id_demanda).first()
        if not demanda:
            return

        if demanda.is_pedido and demanda.status == "atendida":
            logger.info(f"Evento duplicado ignorado para demanda {id_demanda}")
            return

        demanda.is_pedido = True
        demanda.status = "atendida"
        db.commit()


def iniciar_consumidor_pedidos():
    conf = {
        'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
        'group.id': KAFKA_GROUP_ID_PEDIDOS,
        'auto.offset.reset': 'earliest'
    }

    consumer = Consumer(conf)
    consumer.subscribe(TOPICOS_PEDIDOS)

    try:
        while True:
            msg = consumer.poll(timeout=1.0)

            if msg is None:
                continue

            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                else:
                    logger.error(f"Kafka error: {msg.error()}")
                    continue

            try:
                event_data = json.loads(msg.value().decode('utf-8'))
                processar_evento_pedido(event_data)
            except json.JSONDecodeError as e:
                logger.error(f"JSONDecodeError: {e}")
            except Exception as e:
                logger.error(f"Exception processing message: {e}")

    except Exception as e:
        logger.error(f"Consumer loop exception: {e}")
    finally:
        consumer.close()
