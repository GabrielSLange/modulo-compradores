from fastapi import APIRouter
from Services.ping_service import PingService
from DTOs.ping_dto import PingResponseDTO

router = APIRouter()
ping_service = PingService()

@router.get("/api/ping", response_model=PingResponseDTO, tags=["Health Check"])
def ping():
    return ping_service.get_health_status()