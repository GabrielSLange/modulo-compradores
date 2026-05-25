import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# This engine connects to the shared portal_b2b PostgreSQL instance owned by the
# supply module team.  It uses a dedicated env-var so the primary DATABASE_URL
# (which may point to a local SQLite during development) is never confused with
# this connection.
FORNECIMENTO_DATABASE_URL = os.getenv(
    "FORNECIMENTO_DATABASE_URL",
    "postgresql://svc_portal_b2b:@34.29.84.207:5432/portal_b2b",
)

fornecimento_engine = create_engine(
    FORNECIMENTO_DATABASE_URL,
    connect_args={"options": "-c search_path=portal_b2b"},
    pool_pre_ping=True,
)

FornecimentoSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=fornecimento_engine,
)

FornecimentoBase = declarative_base()
