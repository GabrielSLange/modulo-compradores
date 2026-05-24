import json
import logging
import uuid
from datetime import datetime, timezone

# pyrefly: ignore [missing-import]
from confluent_kafka import Producer
from Config.env import get_env, get_env_bool, get_env_int

logger = logging.getLogger(__name__)


class DemandaProducer:
    @staticmethod
    def _obter_produtor():
        servidor_kafka = get_env("KAFKA_BOOTSTRAP_SERVERS", required=True)
        timeout_ms = get_env_int("KAFKA_PUBLISH_TIMEOUT_MS", 5000)
        client_id = get_env("KAFKA_CLIENT_ID") or get_env("SERVICE_NAME", required=True)

        conf = {
            "bootstrap.servers": servidor_kafka,
            "client.id": client_id,
            "acks": "all",
            "enable.idempotence": True,
            "message.timeout.ms": timeout_ms,
        }
        return Producer(conf)

    @staticmethod
    def _kafka_habilitado() -> bool:
        return get_env_bool("KAFKA_ENABLED", True)

    @staticmethod
    def _falhar_ao_erro() -> bool:
        return get_env_bool("KAFKA_FAIL_ON_PUBLISH_ERROR", False)

    @staticmethod
    def _evento_permitido(event_type: str) -> bool:
        allowed = get_env("KAFKA_ALLOWED_EVENT_TYPES")
        if not allowed:
            return True

        eventos = [item.strip() for item in allowed.split(",") if item.strip()]
        return event_type in eventos

    @staticmethod
    def _delivery_report(err, msg) -> None:
        if err is not None:
            logger.error("Falha ao entregar evento Kafka: %s", err)
            return

        logger.info(
            "Evento Kafka publicado. Topic: %s Partition: %s Offset: %s EventType: %s Key: %s",
            msg.topic(),
            msg.partition(),
            msg.offset(),
            msg.topic(),
            msg.key().decode("utf-8") if msg.key() else None,
        )

    @staticmethod
    def _publicar(topico: str, chave: str, evento: dict) -> None:
        if not DemandaProducer._kafka_habilitado():
            logger.debug("Publicacao Kafka ignorada porque Kafka esta desabilitado. EventType: %s", topico)
            return

        if not DemandaProducer._evento_permitido(topico):
            logger.debug("Publicacao Kafka ignorada porque o evento nao esta permitido. EventType: %s", topico)
            return

        try:
            erros_entrega = []

            def delivery_report(err, msg) -> None:
                if err is not None:
                    erros_entrega.append(err)
                DemandaProducer._delivery_report(err, msg)

            producer = DemandaProducer._obter_produtor()
            producer.produce(
                topic=topico,
                key=str(chave),
                value=json.dumps(evento, default=str),
                callback=delivery_report,
            )
            producer.flush()

            if erros_entrega and DemandaProducer._falhar_ao_erro():
                raise RuntimeError(f"Falha ao entregar evento Kafka: {erros_entrega[0]}")
        except Exception:
            logger.exception("Falha ao publicar evento Kafka. EventType: %s CorrelationId: %s", topico, chave)
            if DemandaProducer._falhar_ao_erro():
                raise

    @staticmethod
    def _montar_evento(event_type: str, correlation_id: str, payload: dict) -> dict:
        source = get_env("KAFKA_SOURCE") or get_env("SERVICE_NAME", required=True)
        return {
            "eventId": str(uuid.uuid4()),
            "eventType": event_type,
            "eventVersion": "1.0",
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "source": source,
            "correlationId": correlation_id,
            "payload": payload,
        }

    @staticmethod
    def publicar_demanda_criada(id_demanda: str, dados_demanda: dict):
        topico = get_env("KAFKA_TOPIC_DEMANDA_CRIADA", required=True)
        payload = {"id_demanda": id_demanda, **dados_demanda}
        evento = DemandaProducer._montar_evento(topico, id_demanda, payload)
        DemandaProducer._publicar(topico, id_demanda, evento)

    @staticmethod
    def publicar_demanda_recorrente_gerada(id_nova_demanda: str, dados_demanda: dict):
        topico = get_env("KAFKA_TOPIC_DEMANDA_RECORRENTE_GERADA", required=True)
        payload = {"id_demanda": id_nova_demanda, **dados_demanda}
        evento = DemandaProducer._montar_evento(topico, id_nova_demanda, payload)
        DemandaProducer._publicar(topico, id_nova_demanda, evento)

    @staticmethod
    def publicar_pedido_criado(id_demanda: str, dados_pedido: dict):
        """Publica evento quando demanda eh promovida pra pedido.

        Source = modulo-compradores, pra que nosso proprio pedido_consumer
        possa ignorar (anti-loop). Equipes externas consomem normalmente.
        """
        topico = get_env("KAFKA_TOPIC_PEDIDO_CRIADO", required=True)
        evento = DemandaProducer._montar_evento(topico, id_demanda, dados_pedido)
        DemandaProducer._publicar(topico, id_demanda, evento)

    @staticmethod
    def publicar_pedido_atualizado(id_demanda: str, dados_pedido: dict):
        """Publica evento quando um pedido muda de status."""
        topico = get_env("KAFKA_TOPIC_PEDIDO_ATUALIZADO", required=True)
        evento = DemandaProducer._montar_evento(topico, id_demanda, dados_pedido)
        DemandaProducer._publicar(topico, id_demanda, evento)
