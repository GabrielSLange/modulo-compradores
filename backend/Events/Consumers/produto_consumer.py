"""
produto_consumer.py
===================
Consumidor Kafka para o Módulo de Compradores (Equipe 4).

Inscreve-se no tópico 'produto_cadastrado' publicado pelo microsserviço
SDI.Micro.Produto (Equipe 2) e mantém a tabela local 'produto_cache' atualizada.

Formato do envelope esperado (conforme README da Equipe 2):
{
    "eventId":      "uuid",
    "eventType":    "produto_cadastrado" | "produto_atualizado" | "produto_status_alterado",
    "eventVersion": "1.0",
    "timestamp":    "2026-04-28T14:00:00Z",
    "source":       "produtos-service",
    "correlationId": "uuid",
    "payload": {
        "id":     "uuid",
        "codigo": "NOTE-001",
        "nome":   "Notebook Dell Inspiron",
        "ativo":  true,
        ...  (demais campos ignorados propositalmente)
    }
}
"""

import json
import logging
import os

from confluent_kafka import Consumer, KafkaError, KafkaException

from Data.database import SessionLocal
from Models.produto_cache_model import ProdutoCache

# ---------------------------------------------------------------------------
# Configuração de logging
# ---------------------------------------------------------------------------
logger = logging.getLogger("produto_consumer")

# ---------------------------------------------------------------------------
# Constantes / variáveis de ambiente
# ---------------------------------------------------------------------------
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
KAFKA_TOPIC_PRODUTOS = os.getenv("KAFKA_TOPIC_PRODUTOS", "produto_cadastrado")
KAFKA_GROUP_ID = os.getenv("KAFKA_GROUP_ID_COMPRADORES", "modulo-compradores-grupo")

# Eventos de produto que este consumidor processa
EVENTO_CADASTRADO = "produto_cadastrado"
EVENTO_ATUALIZADO = "produto_atualizado"
EVENTO_STATUS_ALTERADO = "produto_status_alterado"


# ---------------------------------------------------------------------------
# Funções de persistência
# ---------------------------------------------------------------------------

def _upsert_produto(payload: dict) -> None:
    """
    Insere ou atualiza o ProdutoCache com base no payload recebido.
    Extrai apenas os campos que o módulo de compradores precisa.
    """
    id_produto = payload.get("id")
    if not id_produto:
        logger.warning("⚠️  Payload sem campo 'id' — mensagem ignorada: %s", payload)
        return

    codigo = payload.get("codigo", "")
    nome = payload.get("nome", "")
    ativo = payload.get("ativo", True)

    db = SessionLocal()
    try:
        produto = db.query(ProdutoCache).filter(
            ProdutoCache.id_produto == id_produto
        ).first()

        if produto is None:
            # Produto novo — insere
            produto = ProdutoCache(
                id_produto=id_produto,
                codigo=codigo,
                nome=nome,
                ativo=ativo,
            )
            db.add(produto)
            logger.info("✅ Produto inserido no cache: id=%s codigo=%s", id_produto, codigo)
        else:
            # Produto existente — atualiza campos relevantes
            produto.codigo = codigo
            produto.nome = nome
            produto.ativo = ativo
            logger.info("🔄 Produto atualizado no cache: id=%s codigo=%s ativo=%s", id_produto, codigo, ativo)

        db.commit()

    except Exception as exc:
        db.rollback()
        logger.error(
            "❌ Erro ao persistir produto no cache (id=%s): %s",
            id_produto, exc, exc_info=True
        )
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Loop principal do consumidor
# ---------------------------------------------------------------------------

def iniciar_consumidor_produtos() -> None:
    """
    Cria o Consumer Kafka e entra em loop infinito processando mensagens
    do tópico de produtos.

    Esta função é bloqueante — deve ser chamada a partir de uma Thread separada.
    """
    consumer_config = {
        "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
        "group.id": KAFKA_GROUP_ID,
        # Começa do início caso o grupo seja novo; mantém offset em caso contrário
        "auto.offset.reset": "earliest",
        # Commit manual para garantir que só confirmamos após processar
        "enable.auto.commit": False,
    }

    consumer = Consumer(consumer_config)
    consumer.subscribe([KAFKA_TOPIC_PRODUTOS])

    logger.info(
        "🎧 Consumidor Kafka iniciado | tópico='%s' | broker='%s'",
        KAFKA_TOPIC_PRODUTOS, KAFKA_BOOTSTRAP_SERVERS,
    )

    try:
        while True:
            # Aguarda até 1 segundo por uma mensagem nova
            msg = consumer.poll(timeout=1.0)

            if msg is None:
                # Nenhuma mensagem disponível no momento — continua o loop
                continue

            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    # Chegou ao fim da partição — comportamento normal
                    logger.debug(
                        "📭 Fim da partição %s [%d] offset %d",
                        msg.topic(), msg.partition(), msg.offset()
                    )
                else:
                    # Erro real do Kafka
                    raise KafkaException(msg.error())
                continue

            # ---------------------------------------------------------------
            # Mensagem recebida — processamento
            # ---------------------------------------------------------------
            try:
                raw_value = msg.value()
                if raw_value is None:
                    logger.warning("⚠️  Mensagem com valor nulo recebida — ignorada.")
                    consumer.commit(message=msg)
                    continue

                envelope = json.loads(raw_value.decode("utf-8"))
                event_type = envelope.get("eventType", "")
                payload = envelope.get("payload", {})

                logger.debug(
                    "📨 Evento recebido: eventType='%s' eventId='%s'",
                    event_type, envelope.get("eventId")
                )

                if event_type in (EVENTO_CADASTRADO, EVENTO_ATUALIZADO, EVENTO_STATUS_ALTERADO):
                    _upsert_produto(payload)
                else:
                    # Evento de outro domínio (categoria, transporte, etc.) — ignora silenciosamente
                    logger.debug("⏭️  Evento '%s' ignorado (não é de produto).", event_type)

                # Confirma offset somente após processamento bem-sucedido
                consumer.commit(message=msg)

            except json.JSONDecodeError as exc:
                logger.error(
                    "❌ Mensagem malformada (JSON inválido) no offset %d: %s",
                    msg.offset(), exc
                )
                # Faz commit mesmo assim para não ficar preso na mensagem inválida
                consumer.commit(message=msg)

            except Exception as exc:
                logger.error(
                    "❌ Erro inesperado ao processar mensagem (offset=%d): %s",
                    msg.offset(), exc, exc_info=True
                )
                # Commit para avançar — log já registrou o problema
                consumer.commit(message=msg)

    except KeyboardInterrupt:
        logger.info("🛑 Consumidor Kafka encerrado manualmente.")
    finally:
        consumer.close()
        logger.info("🔒 Consumer Kafka fechado.")
