from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID  # Importação adicionada para corrigir o NameError

from Data.database import SessionLocal
from Models.produto_cache_model import ProdutoCache

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class ProdutoProjecaoDTO(BaseModel):
    """
    Projeção local do produto — espelha o tipo ProdutoProjecao do frontend.
    Alimentada exclusivamente pelo consumidor Kafka (tópico produto_cadastrado).
    """
    id: UUID = Field(validation_alias="id_produto")
    codigo: str
    nome: str
    # categoria e unidade não existem no ProdutoCache local —
    # retornamos placeholder até o contrato Kafka incluir esses campos.
    categoria: str = "N/D"
    unidade: str = "UN"
    sincronizado_em: Optional[datetime] = None

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }


@router.get(
    "/produtos/projecao",
    response_model=List[ProdutoProjecaoDTO],
)
@router.get(
    "/produtos/projecao/{id_produto}",
    response_model=ProdutoProjecaoDTO,
)
def get_produto_projecao(
    id_produto: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Retorna a projeção local de produto(s) a partir do cache Kafka.
    - Sem id_produto: retorna todos os produtos do cache.
    - Com id_produto: retorna o produto específico (404 se não encontrado).
    Alimentado exclusivamente pelo consumidor Kafka (tópicos de produtos).
    """
    if id_produto is None:
        produtos = db.query(ProdutoCache).all()
        return [ProdutoProjecaoDTO.model_validate(p) for p in produtos]

    # Tratamento para evitar erro de sintaxe UUID caso o frontend envie a string "null"
    if id_produto == "null":
         raise HTTPException(
            status_code=400,
            detail="ID de produto inválido (recebido string 'null')."
        )

    produto = db.query(ProdutoCache).filter(ProdutoCache.id_produto == id_produto).first()
    if not produto:
        raise HTTPException(
            status_code=404,
            detail="Produto não encontrado no cache local do Módulo de Compradores."
        )

    return ProdutoProjecaoDTO.model_validate(produto)