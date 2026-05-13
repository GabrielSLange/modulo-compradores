from datetime import datetime, timezone
from sqlalchemy import Column, String, Numeric, Boolean, DateTime, Date, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from Data.database import Base
import uuid

class DemandaRecorrencia(Base):
    __tablename__ = "demanda_recorrencia"

    id_recorrencia = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    id_demanda = Column(String, ForeignKey("demanda.id_demanda"), nullable=False, unique=True)
    frequencia = Column(String(10), nullable=False)
    quantidade_por_periodo = Column(Numeric(12, 3), nullable=False)
    data_inicio = Column(Date, nullable=False)
    data_fim = Column(Date, nullable=True)
    dia_preferencial = Column(String(20), nullable=True)
    ativa = Column(Boolean, nullable=False, default=True)
    data_criacao = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    atualizado_em = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    demanda = relationship("Demanda", back_populates="recorrencia")