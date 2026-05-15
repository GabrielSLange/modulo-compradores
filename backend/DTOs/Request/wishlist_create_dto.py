from pydantic import BaseModel, Field
from typing import Optional

class WishlistCreateDTO(BaseModel):
    id_produto: str = Field(..., description="ID do produto")
    quantidade_desejada: Optional[float] = Field(None, gt=0)
    preco_maximo: Optional[float] = Field(None)
    prioridade: Optional[str] = Field(None, description="baixa, media ou alta")
    observacoes: Optional[str] = Field(None, validation_alias="observacao")

# DTO especial para a conversão
class WishlistConverterDTO(BaseModel):
    id_endereco_destino: str = Field(..., description="Endereço é obrigatório para virar Demanda")
    quantidade_desejada: float = Field(..., gt=0, description="Caso não tenha sido preenchido antes, agora é obrigatório")
    prioridade: str = Field(..., description="baixa, media ou alta")