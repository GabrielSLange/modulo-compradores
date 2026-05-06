import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Lê a URL do banco do arquivo .env (se não achar, usa um sqlite temporário para testes locais)
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./banco_local_teste.db")

# Cria o "motor" de conexão
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Cria a fábrica de sessões (equivalente ao tempo de vida de um DbContext)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Esta é a classe mágica que TODAS as suas models vão herdar
Base = declarative_base()