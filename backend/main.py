import logging
from threading import Thread

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from Controllers import ping_controller, demanda_controller, endereco_controller, wishlist_controller, produto_cache_controller
from Jobs.recorrencia_job import iniciar_scheduler
from Events.Consumers.produto_consumer import iniciar_consumidor_produtos
from Events.Consumers.pedido_consumer import iniciar_consumidor_pedidos
from Events.Consumers.negociacao_consumer import iniciar_consumidor_negociacoes

# Importações para o banco de dados local
from Data.database import engine, SQLALCHEMY_DATABASE_URL, Base
from Models import (
    endereco_entrega_model,
    demanda_model,
    demanda_recorrencia_model,
    wishlist_item_model,
    produto_cache_model,  # Registra o modelo no Base para auto-criação da tabela
)


from contextlib import asynccontextmanager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[INFO] A iniciar os Jobs de background...")
    iniciar_scheduler()

    # ----------------------------------------------------------------
    # Inicia o consumidor Kafka de produtos em uma Thread daemon.
    # daemon=True garante que a thread encerra automaticamente quando
    # o processo principal (uvicorn) for encerrado.
    # ----------------------------------------------------------------
    thread_kafka_produtos = Thread(
        target=iniciar_consumidor_produtos,
        name="kafka-produto-consumer",
        daemon=True,
    )
    thread_kafka_produtos.start()
    print("[INFO] Consumidor Kafka de Produtos iniciado em background.")

    thread_kafka_pedidos = Thread(
        target=iniciar_consumidor_pedidos,
        name="kafka-pedido-consumer",
        daemon=True,
    )
    thread_kafka_pedidos.start()
    print("[INFO] Consumidor Kafka de Pedidos iniciado em background.")

    thread_kafka_negociacoes = Thread(
        target=iniciar_consumidor_negociacoes,
        name="kafka-negociacao-consumer",
        daemon=True,
    )
    thread_kafka_negociacoes.start()
    print("[INFO] Consumidor Kafka de Negociações iniciado em background.")

    yield
    # Ao encerrar o servidor, a thread daemon é finalizada automaticamente.

app = FastAPI(
    title="Módulo de Demanda - Portal B2B",
    description="Microsserviço responsável pelo registro de intenções de compra",
    version="1.0.0",
    lifespan=lifespan,
    root_path="/api/demandas" # Esta linha resolve o erro do Swagger no servidor
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
    print("[OK] Banco SQLite local criado para testes!")

app.include_router(ping_controller.router)
app.include_router(demanda_controller.router, tags=["Demandas"])
app.include_router(endereco_controller.router, tags=["Endereços"])
app.include_router(wishlist_controller.router, tags=["Wishlist"])
app.include_router(produto_cache_controller.router, tags=["Produtos (Cache Kafka)"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=5004, reload=True)