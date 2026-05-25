import json
import logging
# pyrefly: ignore [missing-import]
from confluent_kafka import Consumer, KafkaError, KafkaException
from Config.env import get_env, get_env_list
from Data.database import SessionLocal
from Models.produto_cache_model import ProdutoCache

logger = logging.getLogger("produto_consumer")

KAFKA_BOOTSTRAP_SERVERS = get_env("KAFKA_BOOTSTRAP_SERVERS", required=True)
GROUP_ID = get_env("KAFKA_GROUP_ID_COMPRADORES", required=True)

TOPICOS_PRODUTOS = get_env_list("KAFKA_TOPICOS_PRODUTOS", required=True)

def _upsert_produto(payload: dict):
    db = SessionLocal()
    try:
        id_produto = payload.get("id")
        codigo = payload.get("codigo")
        nome = payload.get("nome")
        ativo = payload.get("ativo", True)

        if not id_produto or not codigo or not nome:
            logger.warning("Payload incompleto. Ignorando evento. Payload: %s", payload)
            return

        produto_existente = db.query(ProdutoCache).filter(ProdutoCache.id_produto == id_produto).first()

        if produto_existente:
            produto_existente.codigo = codigo
            produto_existente.nome = nome
            produto_existente.ativo = ativo
        else:
            novo_produto = ProdutoCache(
                id_produto=id_produto,
                codigo=codigo,
                nome=nome,
                ativo=ativo
            )
            db.add(novo_produto)

        db.commit()
    except Exception as exc:
        db.rollback()
        logger.error("Erro ao salvar produto no banco local: %s", exc)
        raise
    finally:
        db.close()

def iniciar_consumidor_produtos():
    consumer = Consumer({
        "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
        "group.id": GROUP_ID,
        "auto.offset.reset": "earliest",
        "enable.auto.commit": False, 
    })

    try:
        consumer.subscribe(TOPICOS_PRODUTOS)
        logger.info("Consumidor de Produtos iniciado. Escutando: %s", TOPICOS_PRODUTOS)

        while True:
            msg = consumer.poll(timeout=1.0)

            if msg is None:
                continue
            
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                else:
                    logger.error("Erro no Kafka: %s", msg.error())
                    continue

            try:
                valor_str = msg.value().decode("utf-8")
                envelope = json.loads(valor_str)
                
                event_type = envelope.get("eventType")
                payload = envelope.get("payload", {})

                if event_type in TOPICOS_PRODUTOS:
                    _upsert_produto(payload)

                consumer.commit(message=msg)

            except json.JSONDecodeError as exc:
                logger.error("JSON invalido recebido no offset %d: %s", msg.offset(), exc)
                consumer.commit(message=msg)

            except Exception as exc:
                # NAO confirma o offset: erro transitorio (ex: banco fora) deve poder
                # reprocessar no proximo restart em vez de perder o evento silenciosamente.
                logger.error("Erro ao processar mensagem do Kafka: %s", exc)

    except KeyboardInterrupt:
        logger.info("Consumidor encerrado manualmente.")
    finally:
        consumer.close()
