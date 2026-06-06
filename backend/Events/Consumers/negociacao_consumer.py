import json
import logging
from decimal import Decimal
# pyrefly: ignore [missing-import]
from confluent_kafka import Consumer, KafkaException, KafkaError
from sqlalchemy import text
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

    Mapeia os campos reais enviados pela equipe de Negociação/Vendas
    para promover a demanda a pedido na nossa base de dados.
    """
    if event_data.get("eventType") != EVENT_TYPE_NEGOCIACAO_FECHADA:
        return

    p = event_data.get("payload", {})
    demanda_id = p.get("demanda_id")
    if not demanda_id:
        logger.warning("Evento negociacao_fechada recebido sem demanda_id no payload.")
        return

    # Extrai e converte os campos conforme tipos corretos (Decimal strings para float)
    id_fornecedor = p.get("empresa_fornecedor_id")
    preco_final = float(p.get("valor_unitario_final")) if p.get("valor_unitario_final") is not None else None
    valor_total = float(p.get("valor_total")) if p.get("valor_total") is not None else None
    quantidade = float(p.get("quantidade")) if p.get("quantidade") is not None else None
    fornecimento_id = p.get("fornecimento_id")
    motivo_fechamento = p.get("motivo_fechamento")

    # Se a negociação foi fechada sem fornecedor vencedor (venda não concluída, ex: expirado, cancelado pelo admin, etc.)
    if not id_fornecedor:
        with SessionLocal() as db:
            demanda = db.query(Demanda).filter(Demanda.id_demanda == demanda_id).first()
            if demanda:
                # Mantém a quantidade original e retorna o status para "aberta"
                demanda.status = "aberta"
                db.commit()
                logger.info(f"Negociação da demanda {demanda_id} fechada sem sucesso (Motivo: {motivo_fechamento}). Status revertido para 'aberta'.")
            else:
                logger.warning(f"Demanda {demanda_id} não encontrada para reverter status pós-fechamento sem sucesso.")
        return

    with SessionLocal() as db:
        demanda = db.query(Demanda).filter(Demanda.id_demanda == demanda_id).first()
        if not demanda:
            logger.warning(f"Demanda {demanda_id} não encontrada no banco de dados local.")
            return

        if demanda.is_pedido and demanda.id_fornecedor:
            logger.info(f"Demanda {demanda_id} já foi promovida a pedido. Ignorando evento.")
            return

        # Se a quantidade fechada for diferente da quantidade original, atualiza no banco
        if quantidade is not None and float(demanda.quantidade_desejada) != quantidade:
            demanda.quantidade_desejada = quantidade

        # Busca o CEP de origem da transportadora na base de fornecimento
        cep_origem = None
        
        with FornecimentoSessionLocal() as fornecimento_db:
            if fornecimento_id:
                try:
                    from Models.fornecimento_model import Fornecimento
                    fornecimento = fornecimento_db.query(Fornecimento).filter(Fornecimento.id == fornecimento_id).first()
                    if fornecimento and fornecimento.endereco_origem_id:
                        # Busca o CEP no cadastro compartilhado de endereços do portal_b2b
                        result = fornecimento_db.execute(
                            text("SELECT cep FROM portal_b2b.endereco WHERE id = :id"),
                            {"id": fornecimento.endereco_origem_id}
                        ).first()
                        if result:
                            cep_origem = result[0]
                            if cep_origem:
                                cep_origem = str(cep_origem).replace("-", "").replace(" ", "")
                except Exception as exc:
                    logger.warning(f"Erro ao buscar CEP de origem no banco de dados para o fornecimento {fornecimento_id}: {exc}")

            # Fallback caso não seja possível consultar o CEP do fornecedor
            if not cep_origem:
                cep_origem = "74000000"

            try:
                DemandaService.promover_para_pedido(
                    db=db,
                    fornecimento_db=fornecimento_db,
                    id_demanda=demanda_id,
                    id_empresa_comprador=demanda.id_empresa_comprador,
                    id_fornecedor=id_fornecedor,
                    preco_final=preco_final,
                    valor_total=valor_total,
                    tipo_transporte="RODOVIARIO",
                    peso_carga=None,  # Será calculado no Service como fallback (Qtd * 1kg)
                    cep_origem=cep_origem,
                    cep_destino=None, # Será extraído no Service a partir do EnderecoEntrega da demanda
                )
                logger.info(f"Demanda {demanda_id} promovida a pedido automaticamente via negociacao_fechada.")
            except Exception as e:
                logger.error(f"Erro ao promover demanda {demanda_id} para pedido via evento Kafka: {e}")


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
