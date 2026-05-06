from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class WishlistResponseDTO(BaseModel):
    id_item: str
    id_produto: str
    quantidade_desejada: Optional[float]
    preco_maximo: Optional[float]
    prioridade: Optional[str]
    observacoes: Optional[str]
    convertido_em_demanda: bool
    id_demanda_gerada: Optional[str]
    criado_em: datetime

    model_config = {
        "from_attributes": True
    }