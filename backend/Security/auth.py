import os
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

def get_token_payload(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    Decodifica o token JWT e retorna o payload.
    """
    token = credentials.credentials
    secret = os.getenv("JWT_SECRET")
    
    if not secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Configuração de Autenticação ausente no servidor (JWT_SECRET)."
        )

    try:
        return jwt.decode(
            token,
            secret,
            algorithms=["HS256"],
            audience=os.getenv("JWT_AUDIENCE", "portal-b2b"),
            issuer=os.getenv("JWT_ISSUER", "portal-autenticacao")
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expirado. Faça login novamente."
        )
    except jwt.PyJWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido."
        )

def get_current_empresa_id(payload: dict = Depends(get_token_payload)) -> str:
    empresa_id = payload.get("empresa_id")
    if not empresa_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token JWT não contém a claim obrigatória 'empresa_id'."
        )
    return str(empresa_id)

def get_current_usuario_id(payload: dict = Depends(get_token_payload)) -> str:
    usuario_id = payload.get("sub")
    if not usuario_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token JWT não contém a claim obrigatória 'sub' (ID do usuário)."
        )
    return str(usuario_id)
