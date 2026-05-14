import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./banco_local_teste.db")

# Se for PostgreSQL, adiciona o search_path nas opções de conexão
connect_args = {}
if SQLALCHEMY_DATABASE_URL.startswith("postgresql"):
    connect_args = {"options": "-c search_path=portal_b2b"}

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
