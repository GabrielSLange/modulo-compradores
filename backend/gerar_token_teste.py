"""
Gera um JWT HS256 válido pra testar a API localmente via Swagger.

Uso:
    python gerar_token_teste.py

Lê JWT_SECRET, JWT_AUDIENCE e JWT_ISSUER do .env (na raiz do repo) ou
das variáveis de ambiente. Usa os IDs fixos do seed.py.
"""
import os
import sys
from datetime import datetime, timezone, timedelta

import jwt

# IDs do seed.py
ID_EMPRESA = "f47ac10b-58cc-4372-a567-0e02b2c3d479"
ID_USUARIO = "550e8400-e29b-41d4-a716-446655440000"


def _carregar_env_file(caminho: str) -> None:
    """Lê um .env simples (KEY=VALUE) sem depender de python-dotenv."""
    if not os.path.isfile(caminho):
        return
    with open(caminho, encoding="utf-8") as f:
        for linha in f:
            linha = linha.strip()
            if not linha or linha.startswith("#") or "=" not in linha:
                continue
            chave, _, valor = linha.partition("=")
            os.environ.setdefault(chave.strip(), valor.strip())


# Tenta carregar .env da raiz do repo (../.env) e do backend/.env
_carregar_env_file(os.path.join(os.path.dirname(__file__), "..", ".env"))
_carregar_env_file(os.path.join(os.path.dirname(__file__), ".env"))

JWT_SECRET = os.getenv("JWT_SECRET")
JWT_AUDIENCE = os.getenv("JWT_AUDIENCE", "portal-b2b")
JWT_ISSUER = os.getenv("JWT_ISSUER", "portal-autenticacao")

if not JWT_SECRET or JWT_SECRET.startswith("<"):
    print("ERRO: defina JWT_SECRET no .env (não pode ser placeholder).", file=sys.stderr)
    sys.exit(1)

agora = datetime.now(timezone.utc)
payload = {
    "sub": ID_USUARIO,
    "empresa_id": ID_EMPRESA,
    "aud": JWT_AUDIENCE,
    "iss": JWT_ISSUER,
    "iat": int(agora.timestamp()),
    "exp": int((agora + timedelta(hours=24)).timestamp()),
}

token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")

print("=" * 70)
print("Token JWT gerado (válido por 24h):")
print("=" * 70)
print(token)
print("=" * 70)
print(f"sub (id_usuario): {ID_USUARIO}")
print(f"empresa_id     : {ID_EMPRESA}")
print(f"aud / iss      : {JWT_AUDIENCE} / {JWT_ISSUER}")
print()
print("No Swagger (http://127.0.0.1:5004/docs):")
print("  1. Clique em 'Authorize' (canto superior direito)")
print("  2. Cole APENAS o token acima (sem 'Bearer ')")
print("  3. Confirme")
