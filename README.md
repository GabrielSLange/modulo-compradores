# Guia de Configuracao e Execucao - Modulo Distribuido

Este guia contem os passos necessarios para configurar e rodar o ambiente de desenvolvimento (Backend e Frontend) em maquinas Windows.

## Pre-requisitos

Antes de comecar, certifique-se de ter instalado:
1. Python 3.10+
2. Node.js (LTS)
3. Git

---

## Passo 1: Clonar o Repositorio

Abra o terminal (PowerShell ou CMD) na pasta de sua preferencia e execute:

git clone <URL_DO_REPOSITORIO>
cd meu-modulo-distribuido

---

## Passo 2: Configurando o Backend (Python + FastAPI)

1. Entre na pasta do backend:
   cd backend

2. Crie o ambiente virtual (venv):
   python -m venv venv

3. Ative o ambiente virtual:
   .\\venv\\Scripts\\activate

4. Instale as dependencias necessarias:
   pip install fastapi uvicorn pydantic sqlalchemy confluent_kafka apscheduler

5. Execute a API:
   python main.py

   A API estara rodando em: http://127.0.0.1:5004
   O Swagger (documentacao) estara em: http://127.0.0.1:5004/docs

---

## Passo 3: Configurando o Frontend (React + Vite)

Abra um novo terminal (mantenha o do backend rodando) na raiz do projeto:

1. Entre na pasta do frontend:
   cd frontend

2. Instale os pacotes do Node:
   npm install

3. Inicie o servidor de desenvolvimento:
   npm run dev

   O frontend estara disponivel no endereco indicado no terminal (geralmente http://localhost:5173 Atualizar essa URL para seguir o padrão da Infra).

---

## Comandos Uteis (PowerShell)

* Habilitar execucao de scripts (se o venv nao ativar):
  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

* Parar a execucao: Ctrl + C em qualquer um dos terminais.
