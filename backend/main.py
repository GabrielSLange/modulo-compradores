from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from Controllers import ping_controller

app = FastAPI(
    title="API do Meu Módulo",
    description="API independente com arquitetura MVC",
    version="1.0.0"
)

# Liberando o CORS para o frontend local conseguir fazer chamadas
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Na produção, mude para o IP do seu front
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrando nossos Controllers
app.include_router(ping_controller.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8080, reload=True)