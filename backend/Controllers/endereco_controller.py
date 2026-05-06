from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from Data.database import SessionLocal
from DTOs.Request.endereco_create_dto import EnderecoCreateDTO
from DTOs.Response.endereco_response_dto import EnderecoResponseDTO
from Services.endereco_service import EnderecoService

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/enderecos", response_model=EnderecoResponseDTO, status_code=status.HTTP_201_CREATED)
def criar_endereco(endereco_dto: EnderecoCreateDTO, db: Session = Depends(get_db)):
    try:
        return EnderecoService.criar_endereco(db, endereco_dto)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao criar endereço: {str(e)}")

@router.get("/enderecos/{id_empresa}", response_model=List[EnderecoResponseDTO])
def listar_enderecos(id_empresa: str, db: Session = Depends(get_db)):
    try:
        return EnderecoService.listar_enderecos_da_empresa(db, id_empresa)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar endereços: {str(e)}")

@router.delete("/enderecos/{id_endereco}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_endereco(id_endereco: str, id_empresa: str, db: Session = Depends(get_db)):
    """
    Exclui um endereço (Soft Delete).
    O id_empresa é passado via Query Parameter para garantir que o usuário não delete o endereço de outra pessoa.
    """
    try:
        sucesso = EnderecoService.deletar_endereco_soft(db, id_endereco, id_empresa)
        if not sucesso:
            raise HTTPException(status_code=404, detail="Endereço não encontrado ou não pertence a esta empresa.")
        return # 204 No Content não retorna corpo JSON
    except HTTPException:
        raise # Repassa o erro 404 sem mascarar
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao deletar endereço: {str(e)}")