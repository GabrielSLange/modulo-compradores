from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from Data.database import SessionLocal
from DTOs.Request.demanda_create_dto import DemandaCreateDTO
from DTOs.Response.demanda_response_dto import DemandaResponseDTO
from Services.demanda_service import DemandaService
from Security.auth import get_current_empresa_id, get_current_usuario_id

router = APIRouter()

# Função de Injeção de Dependência para pegar a Sessão do Banco (Padrão FastAPI)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=DemandaResponseDTO, status_code=status.HTTP_201_CREATED)
def criar_nova_demanda(
    demanda_dto: DemandaCreateDTO, 
    db: Session = Depends(get_db),
    id_empresa: str = Depends(get_current_empresa_id),
    id_usuario: str = Depends(get_current_usuario_id)
):
    try:
        # Entrega o DTO e a conexão do banco para o Service trabalhar
        demanda_criada = DemandaService.criar_demanda(db, demanda_dto, id_empresa, id_usuario)
        return demanda_criada
    except ValueError as e:
        # Erros de regra de negócio geram 400 Bad Request
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Erros inesperados geram 500 Internal Server Error
        raise HTTPException(status_code=500, detail=f"Erro interno ao criar demanda: {str(e)}")

@router.get("/", response_model=List[DemandaResponseDTO])
def listar_demandas(
    db: Session = Depends(get_db),
    id_empresa: str = Depends(get_current_empresa_id)
):
    try:
        demandas = DemandaService.listar_demandas_da_empresa(db, id_empresa)
        return demandas
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar demandas: {str(e)}")

@router.patch("/{id_demanda}/status", response_model=DemandaResponseDTO)
def atualizar_status_demanda(
    id_demanda: str, 
    payload: dict, 
    db: Session = Depends(get_db),
    id_empresa: str = Depends(get_current_empresa_id)
):
    try:
        novo_status = payload.get("status")
        if not novo_status:
            raise HTTPException(status_code=400, detail="O campo 'status' é obrigatório no corpo da requisição")
        
        return DemandaService.atualizar_status(db, id_demanda, novo_status, id_empresa)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar status da demanda: {str(e)}")

@router.patch("/{id_demanda}/cancelar", response_model=DemandaResponseDTO)
def cancelar_demanda(
    id_demanda: str, 
    db: Session = Depends(get_db),
    id_empresa: str = Depends(get_current_empresa_id)
):
    try:
        return DemandaService.atualizar_status(db, id_demanda, "cancelada", id_empresa)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao cancelar demanda: {str(e)}")