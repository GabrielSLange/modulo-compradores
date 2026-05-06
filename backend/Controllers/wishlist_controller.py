from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from Data.database import SessionLocal
from DTOs.Request.wishlist_create_dto import WishlistCreateDTO, WishlistConverterDTO
from DTOs.Response.wishlist_response_dto import WishlistResponseDTO
from DTOs.Response.demanda_response_dto import DemandaResponseDTO
from Services.wishlist_service import WishlistService

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/wishlist", response_model=WishlistResponseDTO, status_code=status.HTTP_201_CREATED)
def adicionar_na_wishlist(dto: WishlistCreateDTO, db: Session = Depends(get_db)):
    try:
        return WishlistService.adicionar_item(db, dto)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao adicionar na wishlist: {str(e)}")

@router.get("/wishlist/{id_empresa}", response_model=List[WishlistResponseDTO])
def listar_wishlist(id_empresa: str, db: Session = Depends(get_db)):
    try:
        return WishlistService.listar_itens_pendentes(db, id_empresa)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar wishlist: {str(e)}")

@router.post("/wishlist/{id_item}/converter", response_model=DemandaResponseDTO)
def converter_wishlist_para_demanda(
    id_item: str, 
    id_usuario: str, 
    dto: WishlistConverterDTO, 
    db: Session = Depends(get_db)
):
    try:
        # Retorna o modelo de Demanda e não de Wishlist!
        demanda_gerada = WishlistService.converter_em_demanda(db, id_item, id_usuario, dto)
        return demanda_gerada
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao converter em demanda: {str(e)}")