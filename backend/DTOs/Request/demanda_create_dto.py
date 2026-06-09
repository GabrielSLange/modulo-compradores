from pydantic import BaseModel, Field
from typing import Optional
# Importando o DTO de recorrência que acabamos de separar
from DTOs.Request.demanda_recorrencia_create_dto import DemandaRecorrenciaCreateDTO

class DemandaCreateDTO(BaseModel):
    id_produto: str = Field(..., description="ID do produto (Equipe 2)")
    id_fornecimento: Optional[str] = Field(None, description="ID do fornecimento")
    id_endereco_destino: str = Field(..., description="ID do endereço de entrega")
    quantidade_desejada: float = Field(..., gt=0, description="Quantidade deve ser maior que zero")
    preco_maximo: Optional[float] = Field(None, description="Preço máximo aceito (opcional)")
    prioridade: str = Field(..., description="baixa, media ou alta")
    observacoes: Optional[str] = Field(None, validation_alias="observacao")
    is_recorrente: bool = Field(default=False, description="Define se a demanda é recorrente")
    recorrencia: Optional[DemandaRecorrenciaCreateDTO] = Field(None, description="Dados da recorrência se is_recorrente for true")