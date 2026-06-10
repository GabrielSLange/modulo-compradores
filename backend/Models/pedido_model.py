from sqlalchemy import Column, String, Numeric
from Data.database import Base

class Pedido(Base):
    __tablename__ = "pedido"

    id = Column(String, primary_key=True)
    processo_id = Column(String, nullable=False)
    empresa_comprador_id = Column(String, nullable=False)
    empresa_fornecedor_id = Column(String, nullable=False)
    fornecimento_id = Column(String, nullable=False)
    valor_total = Column(Numeric(18, 4), nullable=False)
    status = Column(String(20), nullable=False, default="PENDENTE")
