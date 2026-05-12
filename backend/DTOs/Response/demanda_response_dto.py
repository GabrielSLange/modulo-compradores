from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class DemandaResponseDTO(BaseModel):
    # validation_alias: Pydantic v2 usa este para ler atributos do ORM (from_attributes=True).
    # O nome do campo (id, criado_em, etc.) é o que aparece no JSON de saída.
    id: str = Field(validation_alias="id_demanda")
    id_empresa_comprador: str
    id_usuario_criador: str
    id_produto: str
    id_endereco_entrega: Optional[str] = Field(validation_alias="id_endereco_destino", default=None)
    quantidade_desejada: float
    prioridade: str
    status: str
    is_recorrente: bool
    criado_em: Optional[datetime] = Field(validation_alias="data_criacao", default=None)
    atualizado_em: Optional[datetime] = None

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }