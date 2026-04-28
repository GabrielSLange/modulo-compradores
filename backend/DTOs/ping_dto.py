from pydantic import BaseModel

class PingResponseDTO(BaseModel):
    status: str
    message: str
    module: str