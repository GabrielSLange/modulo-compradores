from pydantic import BaseModel, Field
from datetime import date
from typing import Optional

class DemandaRecorrenciaCreateDTO(BaseModel):
    frequencia: str = Field(..., description="diaria, semanal ou mensal")
    quantidade_por_periodo: float = Field(..., gt=0, description="Quantidade gerada a cada ciclo")
    data_inicio: date = Field(..., description="Data de início da recorrência")
    data_fim: Optional[date] = Field(None, description="Data de fim da recorrência (opcional)")
    dia_preferencial: Optional[str] = Field(None, description="Ex: segunda-feira, 15")