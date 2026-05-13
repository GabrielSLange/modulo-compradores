from sqlalchemy import Column, String, Numeric, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from Data.database import Base # Importa a Base do seu "DbContext"
import uuid

class EnderecoEntrega(Base):
    __tablename__ = "endereco_entrega"

    id_endereco = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    id_empresa = Column(String, nullable=False)
    apelido = Column(String(50), nullable=True)
    logradouro = Column(String(200), nullable=False)
    numero = Column(String(20), nullable=True)
    complemento = Column(String(100), nullable=True)
    bairro = Column(String(100), nullable=True)
    cidade = Column(String(100), nullable=False)
    estado = Column(String(2), nullable=False)
    cep = Column(String(9), nullable=False)
    latitude = Column(Numeric(9, 6), nullable=True)
    longitude = Column(Numeric(9, 6), nullable=True)
    ativo = Column(Boolean, nullable=False, default=True)
    criado_em = Column(DateTime, nullable=False, server_default=func.now())
    atualizado_em = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    # Usamos string "Demanda" para evitar erro de importação circular no Python
    demandas = relationship("Demanda", back_populates="endereco")