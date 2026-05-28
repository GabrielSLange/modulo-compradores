# Guia de Configuracao e Execucao - Modulo Distribuido

Este guia contém os passos necessários para configurar e rodar o ambiente de desenvolvimento do **Módulo de Compradores (Equipe 4)**.

---

## 🏗️ Visão Geral e Arquitetura

O sistema adota uma arquitetura de **Microsserviços** operando sob um **Gateway/Load Balancer oficial (Nginx)**. Todo o roteamento de APIs ocorre de forma relativa (ex: `/api/demandas`), eliminando a necessidade de IPs fixos hardcoded no frontend.

### Fluxo do Sistema
1. **Wishlist:** Intenções de compra preliminares, sem compromisso de dados completos.
2. **Demanda:** Intenção consolidada. O usuário preenche prioridade, quantidade e endereço.
3. **Pedido (Promoção):** Uma demanda é "promovida" a pedido quando há fornecedor apto no estoque (validação).
4. **Negociação e Status:** A demanda/pedido transita pelos status: `aberta` -> `em_negociacao` -> `atendida` ou `cancelada`.

### Integração Assíncrona (Kafka / Redpanda)
O módulo utiliza mensageria (Kafka/Redpanda) para garantir a comunicação distribuída. 
- **Consistência Eventual:** Mantemos projeções locais de Produtos para acesso rápido (evitando chamadas HTTP síncronas que dependam da Equipe 2). 
- **Eventos:** Publicamos eventos como `demanda_criada` e `pedido_criado` para notificar outras equipes.

## Pre-requisitos

Antes de comecar, certifique-se de ter instalado:
1. Python 3.10+
2. Node.js (LTS)
3. Git

---

## Passo 1: Clonar o Repositorio

Abra o terminal (PowerShell ou CMD) na pasta de sua preferencia e execute:

git clone https://github.com/GabrielSLange/modulo-compradores.git
cd modulo-compradores

### Configurando Variáveis de Ambiente

Crie o seu arquivo `.env` na raiz do projeto copiando o `.env.example`.
O projeto **já está configurado para apontar para o cluster Kafka compartilhado** oficial.
**Atenção:** Não envie o seu `.env` com senhas reais para o GitHub.

---

## Passo 2: Configurando o Backend (Python + FastAPI)

1. Entre na pasta do backend:
   cd backend

2. Crie o ambiente virtual (venv):
   python -m venv venv

3. Ative o ambiente virtual:
   .\\venv\\Scripts\\activate

4. Instale as dependencias necessarias:
   pip install fastapi uvicorn pydantic sqlalchemy confluent_kafka apscheduler PyJWT

5. Execute a API:
   python main.py

   A API estará rodando localmente na porta: `http://127.0.0.1:5004`
   O Swagger (documentação interativa) em: `http://127.0.0.1:5004/docs`

   *Nota:* O backend se conecta a um banco **Cloud SQL** (configurado via `.env`). O gerenciamento de dependências está preparado para produção e dockerização.

---

## Passo 3: Configurando o Frontend (React + Vite)

Abra um novo terminal (mantenha o do backend rodando) na raiz do projeto:

1. Entre na pasta do frontend:
   cd frontend

2. Instale os pacotes do Node:
   npm install

3. Inicie o servidor de desenvolvimento:
   npm run dev

   No ambiente de **desenvolvimento local**, o Vite subirá em `http://localhost:5173` e fará um proxy transparente para o backend. 
   
   **Atenção (Ambiente Dockerizado/Produção):** Na infraestrutura oficial, o frontend é servido via **Nginx (Gateway)**. As chamadas não utilizam IPs ou portas fixas. O roteamento é sempre relativo (`/api/demandas`, `/api/produtos`, `/api/usuarios`), sendo interceptado pelo Nginx que direciona o tráfego para os contêineres de backend apropriados na mesma rede Docker.

---

## 🐳 Docker e Infraestrutura

A aplicação está contêinerizada. A arquitetura esperada para integração inclui:
- **Dockerfile:** Presente em cada subprojeto para build das imagens (React para o front, FastAPI para o back).
- **Docker Compose:** Orquestra os contêineres conectando-os numa rede compartilhada oficial (onde o Nginx e outros microsserviços residem), permitindo a resolução interna de nomes e roteamento dinâmico.

---

## 🔐 Autenticação JWT Centralizada

- A autenticação é protegida e exige um **token JWT** nos cabeçalhos (`Authorization: Bearer <token>`).
- **Frontend:** O cliente captura o token de forma automatizada (ex: via Gateway/URL), guarda em cache e anexa em todas as chamadas HTTP protegidas.
- **Backend:** Extrai do token as informações do usuário e da empresa (`empresa_id`), garantindo isolamento de dados (Tenant Isolation) por rotas, sem receber IDs nos payloads.

---

## 📁 Organização do Projeto

A estrutura foi separada por responsabilidades:
- `/backend`: API construída em Python (FastAPI). Lida com regras de negócio, banco de dados (SQLAlchemy) e Kafka.
- `/frontend`: Interface React + Vite. Usa `React Query` para cache de dados e chamadas resilientes. Organizado pelo padrão *Feature-First* (`/features`, `/hooks`, `/services`).

---

## 🛠️ Comandos Úteis (PowerShell)

* Habilitar execução de scripts (se o `venv` não ativar):
  ```powershell
  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
  ```

* Parar a execução: `Ctrl + C` em qualquer um dos terminais.
