from sqlalchemy import Column, Boolean, Numeric
from sqlalchemy.dialects.postgresql import UUID
from Data.fornecimento_database import FornecimentoBase


class Fornecimento(FornecimentoBase):
    __tablename__ = "fornecimento"
    __table_args__ = {"schema": "portal_b2b"}

    id = Column(UUID(as_uuid=True), primary_key=True)
    empresa_fornecedor_id = Column(UUID(as_uuid=True), nullable=False)
    produto_id = Column(UUID(as_uuid=True), nullable=False)
    endereco_origem_id = Column(UUID(as_uuid=True), nullable=True)
    preco_unitario = Column(Numeric(18, 4), nullable=False)
    quantidade_disponivel = Column(Numeric(18, 4), nullable=False)
    ativo = Column(Boolean, nullable=False, default=True)
