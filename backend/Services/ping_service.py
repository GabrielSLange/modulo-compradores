from DTOs.ping_dto import PingResponseDTO

class PingService:
    def get_health_status(self) -> PingResponseDTO:
        # Aqui no futuro entrará a lógica de verificar banco, kafka, etc.
        return PingResponseDTO(
            status="online",
            message="A API do nosso módulo está viva e respirando!",
            module="Meu Modulo Independente"
        )