from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class WishlistResponseDTO(BaseModel):
    # validation_alias: lê model.id_item e serializa como "id"
    id: str = Field(validation_alias="id_item")
    id_produto: str
    quantidade_desejada: Optional[float] = None
    preco_maximo: Optional[float] = None
    prioridade: Optional[str] = None
    observacoes: Optional[str] = None
    convertido_em_demanda: bool
    id_demanda_gerada: Optional[str] = None
    criado_em: datetime  # coluna já se chama criado_em no model

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }