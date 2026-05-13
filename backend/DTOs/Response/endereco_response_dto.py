from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class EnderecoResponseDTO(BaseModel):
    # validation_alias: lê model.id_endereco e serializa como "id"
    id: str = Field(validation_alias="id_endereco")
    id_empresa: str
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

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }