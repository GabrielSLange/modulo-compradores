from pydantic import BaseModel
from typing import Optional

class EnderecoResponseDTO(BaseModel):
    id_endereco: str
    id_empresa: str
    logradouro: str
    numero: Optional[str]
    complemento: Optional[str]
    bairro: Optional[str]
    cidade: str
    estado: str
    cep: str
    ativo: bool

    model_config = {
        "from_attributes": True
    }