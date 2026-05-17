import os
import json
import logging
from confluent_kafka import Consumer, KafkaException, KafkaError
from Data.database import SessionLocal
from Models.demanda_model import Demanda

logger = logging.getLogger(__name__)


def processar_evento_pedido(event_data: dict) -> None:
    """Processa um único evento Kafka de pedido. Idempotente.

    Extraído pra permitir testes diretos sem subir Kafka.
    """
    if event_data.get("eventType") != "pedido_criado":
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
        'bootstrap.servers': os.getenv('KAFKA_BOOTSTRAP_SERVERS', '10.128.0.2:9092,10.128.0.3:9092,10.128.0.4:9092'),
        'group.id': 'modulo_compradores_pedidos',
        'auto.offset.reset': 'earliest'
    }

    consumer = Consumer(conf)
    consumer.subscribe(['sdi.pedidos.events'])

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
