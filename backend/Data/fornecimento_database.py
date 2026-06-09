import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# This engine connects to the shared portal_b2b PostgreSQL instance owned by the
# supply module team.  It uses a dedicated env-var so the primary DATABASE_URL
# (which may point to a local SQLite during development) is never confused with
# this connection.
DATABASE_URL = os.getenv("DATABASE_URL", "") or "sqlite:///./banco_local_teste.db"


connect_args = {}
if DATABASE_URL.startswith("postgresql"):
    connect_args = {
        "options": "-c search_path=portal_b2b -c statement_timeout=8000",
        "connect_timeout": 5,
    }

fornecimento_engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
    pool_timeout=6,
)

FornecimentoSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=fornecimento_engine,
)

FornecimentoBase = declarative_base()
