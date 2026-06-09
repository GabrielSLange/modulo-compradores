from datetime import datetime, timezone
from sqlalchemy import Column, String, Numeric, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func, expression
from Data.database import Base
import uuid

class Demanda(Base):
    __tablename__ = "demanda"

    id_demanda = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    id_empresa_comprador = Column(String, nullable=False)
    id_usuario_criador = Column(String, nullable=False)
    id_produto = Column(String, nullable=False)
    id_fornecimento = Column(String, nullable=True)
    id_solicitacao_frete = Column(String, nullable=True)
    
    # nullable=True adicionado para aceitar a demanda sem endereço do seed.py
    id_endereco_destino = Column(String, ForeignKey("endereco_entrega.id_endereco"), nullable=True)
    
    quantidade_desejada = Column(Numeric(12, 3), nullable=False)
    preco_maximo = Column(Numeric(12, 2), nullable=True)
    prioridade = Column(String(10), nullable=False)
    is_recorrente = Column(Boolean, nullable=False, default=False)
    is_pedido = Column(Boolean, nullable=False, default=False, server_default=expression.false())
    status = Column(String(20), nullable=False, default="aberta")
    observacoes = Column(Text, nullable=True)
    data_criacao = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    atualizado_em = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    # Campos para Integração Logística e Negociação
    tipo_transporte = Column(String(50), nullable=True, default="RODOVIARIO")
    peso_carga = Column(Numeric(12, 2), nullable=True)
    cep_origem = Column(String(9), nullable=True)
    cep_destino = Column(String(9), nullable=True)
    id_fornecedor = Column(String, nullable=True)
    preco_final = Column(Numeric(12, 2), nullable=True)
    valor_total = Column(Numeric(12, 2), nullable=True)

    # Campos de contratação do frete (Logística)
    id_frete_selecionado = Column(String, nullable=True)
    valor_frete = Column(Numeric(12, 2), nullable=True)
    status_frete = Column(String(30), nullable=True, default="PENDENTE")

    endereco = relationship("EnderecoEntrega", back_populates="demandas")
    recorrencia = relationship("DemandaRecorrencia", back_populates="demanda", uselist=False)
    wishlist_items = relationship("WishlistItem", back_populates="demanda_gerada")