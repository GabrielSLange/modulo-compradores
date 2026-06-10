from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError
from typing import List, Optional

from Data.database import SessionLocal
from Data.fornecimento_database import FornecimentoSessionLocal
from DTOs.Request.demanda_create_dto import DemandaCreateDTO
from DTOs.Response.demanda_response_dto import DemandaResponseDTO
from Services.demanda_service import DemandaService
from Security.auth import get_current_empresa_id, get_current_usuario_id, security
from fastapi.security import HTTPAuthorizationCredentials

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_fornecimento_db():
    db = FornecimentoSessionLocal()
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
    is_pedido: Optional[bool] = None,
    db: Session = Depends(get_db),
    id_empresa: str = Depends(get_current_empresa_id)
):
    try:
        demandas = DemandaService.listar_demandas_da_empresa(db, id_empresa, is_pedido)
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

@router.patch("/{id_demanda}/promover", response_model=DemandaResponseDTO)
def promover_demanda_para_pedido(
    id_demanda: str,
    db: Session = Depends(get_db),
    fornecimento_db: Session = Depends(get_fornecimento_db),
    id_empresa: str = Depends(get_current_empresa_id),
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    try:
        token = credentials.credentials
        return DemandaService.promover_para_pedido(db, fornecimento_db, id_demanda, id_empresa, token=token)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except OperationalError:
        raise HTTPException(
            status_code=503,
            detail="Serviço de estoque temporariamente indisponível. Tente novamente em instantes."
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao promover demanda para pedido: {str(e)}")


@router.get("/{id_demanda}/cotacoes", response_model=list)
def obter_cotacoes_frete(
    id_demanda: str,
    db: Session = Depends(get_db),
    id_empresa: str = Depends(get_current_empresa_id),
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """
    Proxy REST para listar as cotações de frete disponíveis para a demanda/pedido.
    Propaga o JWT do usuário logado para a API de Logística.
    """
    from Models.demanda_model import Demanda
    demanda = db.query(Demanda).filter(
        Demanda.id_demanda == id_demanda,
        Demanda.id_empresa_comprador == id_empresa
    ).first()
    
    if not demanda:
        raise HTTPException(status_code=404, detail="Demanda não encontrada ou acesso negado.")
        
    try:
        token = credentials.credentials
        return DemandaService.obter_cotacoes_logistica(id_demanda, token)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter cotações de frete: {str(e)}")


@router.post("/{id_demanda}/contratar-frete", response_model=DemandaResponseDTO)
def contratar_frete(
    id_demanda: str,
    payload: dict,
    db: Session = Depends(get_db),
    id_empresa: str = Depends(get_current_empresa_id),
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """
    Proxy REST para contratar uma cotação de frete selecionada.
    Atualiza localmente os campos de frete no banco da demanda.
    """
    cotacao_id = payload.get("cotacao_id")
    if not cotacao_id:
        raise HTTPException(status_code=400, detail="O campo 'cotacao_id' é obrigatório no corpo da requisição.")
        
    try:
        token = credentials.credentials
        return DemandaService.contratar_frete_logistica(db, id_demanda, id_empresa, cotacao_id, token)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao contratar frete: {str(e)}")


@router.post("/{id_demanda}/simular-pedido", response_model=DemandaResponseDTO)
def simular_pedido(
    id_demanda: str,
    payload: dict = {},
    db: Session = Depends(get_db),
    id_empresa: str = Depends(get_current_empresa_id),
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """
    Endpoint de simulação/teste: força a promoção de uma demanda para pedido,
    registra o ID na tabela de pedidos e dispara a solicitação de frete na Logística.
    Bypassa validações externas de estoque.
    """
    try:
        token = credentials.credentials
        return DemandaService.simular_pedido_teste(db, id_demanda, id_empresa, payload, token)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao simular pedido: {str(e)}")