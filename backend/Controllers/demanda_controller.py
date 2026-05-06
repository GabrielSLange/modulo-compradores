from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from Data.database import SessionLocal
from DTOs.Request.demanda_create_dto import DemandaCreateDTO
from DTOs.Response.demanda_response_dto import DemandaResponseDTO
from Services.demanda_service import DemandaService
from typing import List

router = APIRouter()

# Função de Injeção de Dependência para pegar a Sessão do Banco (Padrão FastAPI)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/demandas", response_model=DemandaResponseDTO, status_code=status.HTTP_201_CREATED)
def criar_nova_demanda(demanda_dto: DemandaCreateDTO, db: Session = Depends(get_db)):
    try:
        # Entrega o DTO e a conexão do banco para o Service trabalhar
        demanda_criada = DemandaService.criar_demanda(db, demanda_dto)
        return demanda_criada
    except Exception as e:
        # Se o Service estourar algum erro (ex: banco fora do ar), o Controller segura e devolve 500
        raise HTTPException(status_code=500, detail=f"Erro ao criar demanda: {str(e)}")
    
@router.get("/demandas", response_model=List[DemandaResponseDTO])
def listar_demandas(id_empresa: str, db: Session = Depends(get_db)):
    try:
        demandas = DemandaService.listar_demandas_da_empresa(db, id_empresa)
        return demandas
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar demandas: {str(e)}")