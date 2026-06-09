from sqlalchemy import Column, String
from Data.database import Base

class Pedido(Base):
    __tablename__ = "pedido"

    id = Column(String, primary_key=True)
    status = Column(String(30), nullable=False)
