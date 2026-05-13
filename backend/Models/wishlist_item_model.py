from datetime import datetime, timezone
from sqlalchemy import Column, String, Numeric, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from Data.database import Base
import uuid

class WishlistItem(Base):
    __tablename__ = "wishlist_item"

    id_item = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    id_empresa = Column(String, nullable=False)
    id_usuario = Column(String, nullable=False)
    id_produto = Column(String, nullable=False)
    quantidade_desejada = Column(Numeric(12, 3), nullable=True)
    preco_maximo = Column(Numeric(12, 2), nullable=True)
    prioridade = Column(String(10), nullable=True)
    observacoes = Column(Text, nullable=True)
    convertido_em_demanda = Column(Boolean, nullable=False, default=False)
    id_demanda_gerada = Column(String, ForeignKey("demanda.id_demanda"), nullable=True)
    data_criacao = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    atualizado_em = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    demanda_gerada = relationship("Demanda", back_populates="wishlist_items")