from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from Controllers import ping_controller, demanda_controller, endereco_controller, wishlist_controller
from Jobs.recorrencia_job import iniciar_scheduler

# Importações para o banco de dados local
from Data.database import engine, SQLALCHEMY_DATABASE_URL, Base
from Models import endereco_entrega_model, demanda_model, demanda_recorrencia_model, wishlist_item_model


from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 A iniciar os Jobs de background...")
    iniciar_scheduler()
    yield

app = FastAPI(
    title="Módulo de Demanda - Portal B2B",
    description="Microsserviço responsável pelo registro de intenções de compra",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gatilho de desenvolvimento: Cria as tabelas SÓ se for SQLite (Testes Locais)
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    Base.metadata.create_all(bind=engine)
    print("📦 Banco SQLite local criado para testes!")

app.include_router(ping_controller.router)
app.include_router(demanda_controller.router, tags=["Demandas"])
app.include_router(endereco_controller.router, tags=["Endereços"])
app.include_router(wishlist_controller.router, tags=["Wishlist"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=5004, reload=True)