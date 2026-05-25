from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session
from Models.fornecimento_model import Fornecimento


class EstoqueValidationResult:
    def __init__(self, valido: bool, id_fornecedor_apto: Optional[UUID] = None):
        self.valido = valido
        self.id_fornecedor_apto = id_fornecedor_apto


class EstoqueService:
    @staticmethod
    def validar_estoque(
        fornecimento_db: Session,
        id_produto: UUID,
        quantidade_desejada: float,
    ) -> EstoqueValidationResult:
        fornecedor_apto = (
            fornecimento_db.query(Fornecimento)
            .filter(
                Fornecimento.produto_id == id_produto,
                Fornecimento.quantidade_disponivel >= quantidade_desejada,
                Fornecimento.ativo.is_(True),
            )
            .first()
        )

        if fornecedor_apto:
            return EstoqueValidationResult(
                valido=True,
                id_fornecedor_apto=fornecedor_apto.empresa_fornecedor_id,
            )

        return EstoqueValidationResult(valido=False)
