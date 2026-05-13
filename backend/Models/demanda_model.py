from datetime import datetime, timezone

from sqlalchemy import Column, String, Numeric, Boolean, DateTime, Date, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from Data.database import Base
import uuid

class Demanda(Base):
    __tablename__ = "demanda"

    id_demanda = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    id_empresa_comprador = Column(String, nullable=False)
    id_usuario_criador = Column(String, nullable=False)
    id_produto = Column(String, nullable=False)
    id_endereco_destino = Column(String, ForeignKey("endereco_entrega.id_endereco"), nullable=False)
    quantidade_desejada = Column(Numeric(12, 3), nullable=False)
    preco_maximo = Column(Numeric(12, 2), nullable=True)
    prioridade = Column(String(10), nullable=False)
    is_recorrente = Column(Boolean, nullable=False, default=False)
    status = Column(String(20), nullable=False, default="aberta")
    observacoes = Column(Text, nullable=True)
    data_criacao = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    atualizado_em = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    # Relacionamentos usando o nome da classe em String
    endereco = relationship("EnderecoEntrega", back_populates="demandas")
    recorrencia = relationship("DemandaRecorrencia", back_populates="demanda", uselist=False)
    wishlist_items = relationship("WishlistItem", back_populates="demanda_gerada")