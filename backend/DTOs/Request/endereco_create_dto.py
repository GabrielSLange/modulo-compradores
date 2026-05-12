from pydantic import BaseModel, Field
from typing import Optional

class EnderecoCreateDTO(BaseModel):
    id_empresa: str = Field(..., description="ID da empresa compradora")
    # O frontend chama de 'apelido' (ex: 'Matriz', 'Filial SP').
    # Não existe coluna no banco — descartado silenciosamente por enquanto.
    apelido: Optional[str] = Field(None, description="Apelido amigável do endereço (uso futuro)")
    logradouro: str = Field(..., max_length=200)
    numero: Optional[str] = Field(None, max_length=20)
    complemento: Optional[str] = Field(None, max_length=100)
    bairro: Optional[str] = Field(None, max_length=100)
    cidade: str = Field(..., max_length=100)
    # O frontend envia 'uf'; o banco armazena como 'estado'.
    # validation_alias aceita ambos os nomes no JSON de entrada.
    estado: str = Field(..., max_length=2, description="Sigla do Estado (Ex: SP)", validation_alias="uf")
    cep: str = Field(..., max_length=9)
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    model_config = {
        "populate_by_name": True,  # aceita tanto 'uf' quanto 'estado'
    }