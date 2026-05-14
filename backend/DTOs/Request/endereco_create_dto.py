from pydantic import BaseModel, Field
from typing import Optional

class EnderecoCreateDTO(BaseModel):
    id_empresa: str = Field(..., description="ID da empresa compradora")
    apelido: Optional[str] = Field(None, description="Apelido amigavel do endereco")
    logradouro: str = Field(..., max_length=200)
    numero: Optional[str] = Field(None, max_length=20)
    complemento: Optional[str] = Field(None, max_length=100)
    bairro: Optional[str] = Field(None, max_length=100)
    cidade: str = Field(..., max_length=100)
    estado: str = Field(..., max_length=2, validation_alias="uf")
    cep: str = Field(..., max_length=9)
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    model_config = {
        "populate_by_name": True,
    }