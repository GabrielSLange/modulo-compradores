from pydantic import BaseModel

class DemandaResponseDTO(BaseModel):
    id_demanda: str
    id_produto: str
    quantidade_desejada: float
    prioridade: str
    status: str
    is_recorrente: bool
    
    model_config = {
        "from_attributes": True
    }