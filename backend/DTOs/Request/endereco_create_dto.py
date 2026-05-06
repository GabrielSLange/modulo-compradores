from pydantic import BaseModel, Field
from typing import Optional

class EnderecoCreateDTO(BaseModel):
    id_empresa: str = Field(..., description="ID da empresa compradora")
    logradouro: str = Field(..., max_length=200)
    numero: Optional[str] = Field(None, max_length=20)
    complemento: Optional[str] = Field(None, max_length=100)
    bairro: Optional[str] = Field(None, max_length=100)
    cidade: str = Field(..., max_length=100)
    estado: str = Field(..., max_length=2, description="Sigla do Estado (Ex: SP)")
    cep: str = Field(..., max_length=9)
    latitude: Optional[float] = None
    longitude: Optional[float] = None