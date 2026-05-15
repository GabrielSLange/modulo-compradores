from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID

class EnderecoResponseDTO(BaseModel):
    id: UUID = Field(validation_alias="id_endereco")
    id_empresa: UUID
    apelido: Optional[str] = None
    logradouro: str
    numero: Optional[str] = None
    complemento: Optional[str] = None
    bairro: Optional[str] = None
    cidade: str
    uf: str = Field(validation_alias="estado")
    cep: str
    ativo: bool
    data_criacao: Optional[datetime] = None
    atualizado_em: Optional[datetime] = None

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }
