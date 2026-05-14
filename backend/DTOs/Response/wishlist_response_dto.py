from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID

class WishlistResponseDTO(BaseModel):
    id: UUID = Field(validation_alias="id_item")
    id_produto: UUID
    quantidade_desejada: Optional[float] = None
    preco_maximo: Optional[float] = None
    prioridade: Optional[str] = None
    observacao: Optional[str] = Field(None, validation_alias="observacoes")
    convertido_em_demanda: bool
    id_demanda_gerada: Optional[UUID] = None
    data_criacao: datetime

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }