from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID

class DemandaResponseDTO(BaseModel):
    id: UUID = Field(validation_alias="id_demanda")
    id_empresa_comprador: UUID
    id_usuario_criador: UUID
    id_produto: UUID
    id_endereco_entrega: Optional[UUID] = Field(validation_alias="id_endereco_destino", default=None)
    quantidade_desejada: float
    prioridade: str
    status: str
    is_recorrente: bool
    is_pedido: bool
    observacao: Optional[str] = Field(None, validation_alias="observacoes")
    data_criacao: Optional[datetime] = None
    atualizado_em: Optional[datetime] = None

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }