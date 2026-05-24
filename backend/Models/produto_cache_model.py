"""
produto_cache_model.py
======================
Cache local de produtos recebidos via Kafka do microsserviço SDI.Micro.Produto (Equipe 2).
Contém apenas os campos essenciais para o Módulo de Compradores.
"""

import uuid
from datetime import datetime, timezone

# pyrefly: ignore [missing-import]
from sqlalchemy import Column, String, Boolean, DateTime
from Data.database import Base


class ProdutoCache(Base):
    """
    Espelho local (cache) dos produtos publicados pelo catálogo (Equipe 2).

    Alimentado exclusivamente pelo consumidor Kafka que escuta o tópico
    'produto_cadastrado'. Não deve ser alterado manualmente via API deste módulo.
    """

    __tablename__ = "produto_cache"

    # Chave primária: mesmo UUID gerado pelo microsserviço de produtos
    id_produto = Column(String, primary_key=True)

    # Código único normalizado em maiúsculo (ex: "NOTE-001")
    codigo = Column(String(60), nullable=False, index=True)

    # Nome legível do produto
    nome = Column(String(150), nullable=False)

    # Reflete o campo 'ativo' do catálogo original
    ativo = Column(Boolean, nullable=False, default=True)

    # Controle de auditoria local — quando este registro foi sincronizado pela última vez
    sincronizado_em = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return (
            f"<ProdutoCache id={self.id_produto!r} "
            f"codigo={self.codigo!r} ativo={self.ativo}>"
        )
