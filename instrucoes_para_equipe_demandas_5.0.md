# Guia de Integração — Demandas com Logística (Equipe 8)

**Versão:** 5.0 (Fluxo Descentralizado — Pós-Auditoria de Pre-Deployment)  
**Autor:** Equipe 8 — Logística (`logistica-service`)  
**Última revisão:** Alinhado com a auditoria SRE de pré-deployment e com o Guia Oficial de Integração da infraestrutura.

---

# 1. Visão Geral: Fluxo de Frete Manual

A escolha de frete não é automática. A Equipe 8 (Logística) é responsável por gerar as cotações e orquestrar a entrega física, mas a Equipe de Demandas é a responsável oficial por decidir qual cotação de frete será contratada para cada pedido.

## Fluxo

1. A Logística recebe o evento de pedido e gera cotações reais com as transportadoras.
2. A solicitação de frete entra no status `COTADO` e a Logística pausa o fluxo.
3. A Equipe de Demandas consome a API REST da Logística para visualizar as cotações disponíveis.
4. A Equipe de Demandas seleciona a cotação desejada enviando um `POST` para a Logística.
5. A Logística retoma o fluxo, atualiza o status para `SELECIONADO`, publica o evento `frete_selecionado` no Kafka e inicia a simulação de rastreio até o status `ENTREGUE`.

---

# 2. Autenticação (JWT Obrigatório)

A API é protegida via JWT (JSON Web Token). Para consumir qualquer rota REST da Logística, a aplicação de Demandas deve possuir um token assinado pela chave secreta do Portal B2B.

## Método preferencial — Query String

```http
http://34.8.17.245/api/logistica/solicitacoes?jwt=SEU_TOKEN_AQUI
```

## Método alternativo — Header HTTP

```http
Authorization: Bearer SEU_TOKEN_AQUI
```

Em ambiente Docker local de desenvolvimento, o frontend (`logistica-front`) injeta automaticamente um token mock quando o hostname detectado é `localhost` ou `127.0.0.1`.

Esse mecanismo é restrito ao ambiente local e nunca é ativado em produção.

---

# 3. Consumo da API REST

Todas as rotas listadas são internas ao microsserviço. O gateway da infraestrutura aplica o prefixo `/api/logistica` antes de encaminhar ao container.

## A. Visualizar as Cotações Disponíveis

### Rota

```http
GET /solicitacoes/{solicitacao_id}/cotacoes
```

### Exemplo

```http
GET http://34.8.17.245/api/logistica/solicitacoes/{solicitacao_id}/cotacoes
```

### Resposta (HTTP 200)

```json
[
  {
    "id": "c0746b1c-7708-410a-8d19-90b9b3e1f579",
    "solicitacao_id": "2e5f5fec-d840-4d87-9e75-b43ea56d31b8",
    "transportadora_id": "b32bd9f2-6122-4c84-b721-b284aec606e1",
    "valor": 2204.90,
    "prazo": 7,
    "data_cotacao": "2025-06-05T14:00:00Z"
  },
  {
    "id": "a9317b2b-4221-420a-8c11-10c9b3e1f981",
    "solicitacao_id": "2e5f5fec-d840-4d87-9e75-b43ea56d31b8",
    "transportadora_id": "c13cd9f2-7122-5c84-a721-c284aec606e2",
    "valor": 2626.44,
    "prazo": 4,
    "data_cotacao": "2025-06-05T14:00:01Z"
  }
]
```

A interface de Demandas deve exibir valor, prazo e transportadora.

## B. Contratar o Frete Escolhido

### Rota

```http
POST /demo-contratar-frete
```

### Exemplo

```http
POST http://34.8.17.245/api/logistica/demo-contratar-frete
```

### Payload

```json
{
  "solicitacao_id": "2e5f5fec-d840-4d87-9e75-b43ea56d31b8",
  "cotacao_id": "c0746b1c-7708-410a-8d19-90b9b3e1f579"
}
```

### Resposta

Retorna o objeto `SolicitacaoFrete` atualizado com status `SELECIONADO`.

Fluxo posterior:

```text
SELECIONADO -> EM_TRANSITO -> ENTREGUE
```

### Códigos de erro

| Código | Significado |
|----------|------------|
| 400 | solicitacao_id ou cotacao_id ausentes ou inválidos |
| 404 | Solicitação ou cotação não encontrada |
| 409 | Solicitação já processada ou pedido já possui frete contratado |

---

# 4. Tópicos Kafka

## Tópicos publicados pela Logística

| Tópico | Quando é emitido |
|---------|-----------------|
| solicitacao_frete_criada | Ao criar uma nova solicitação de cotação |
| cotacoes_frete_disponiveis | Após gerar as 3 cotações das transportadoras |
| frete_selecionado | Após a contratação confirmada |
| logistica_status_atualizado | A cada transição de status de rastreio |

## Tópico publicado por Demandas

| Tópico | Quando publicar |
|---------|----------------|
| frete_contratado | Alternativa assíncrona ao POST `/demo-contratar-frete` |

### Envelope padrão dos eventos

```json
{
  "eventId": "uuid",
  "eventType": "nome_do_topico",
  "eventVersion": "1.0",
  "timestamp": "ISO8601",
  "source": "nome-do-servico",
  "correlationId": "uuid",
  "payload": {}
}
```

### Configuração Kafka

```env
KAFKA_BOOTSTRAP_SERVERS=10.128.0.2:9092,10.128.0.3:9092,10.128.0.4:9092
```

---

# 5. Endereços e Portas Oficiais

## Integração e Produção

| Recurso | URL |
|----------|-----|
| Frontend Logística | http://34.8.17.245/logistica/ |
| API Health | http://34.8.17.245/api/logistica/health |
| API Swagger | http://34.8.17.245/api/logistica/docs |
| Kafka UI | http://34.29.84.207:8080 |

## Desenvolvimento Local

### Subir containers

```bash
docker compose up --build -d
```

| Recurso | URL |
|----------|-----|
| Frontend Logística | http://localhost:8088/logistica/ |
| API Health | http://localhost:5008/health |
| API Swagger | http://localhost:5008/docs |

### Portas oficiais

- Backend: `5008`
- Frontend: `8088`

### Arquivo `.env`

```env
SERVICE_NAME=logistica-service
PORT=5008
DATABASE_URL=postgresql://svc_portal_b2b:senha_portal_b2b@136.114.235.212:5432/portal_b2b
DB_SCHEMA=portal_b2b
KAFKA_BOOTSTRAP_SERVERS=10.128.0.2:9092,10.128.0.3:9092,10.128.0.4:9092
ROOT_PATH=/api/logistica
```

---

# 6. Requisitos do Ambiente Docker

### Criar rede

```bash
docker network create portal-b2b-network
```

### Observações

- O arquivo `.env` nunca deve ser commitado.
- Utilize sempre o `.env.example` como base.
- Dúvidas sobre integração, UUIDs ou payloads devem ser alinhadas diretamente com a Equipe 8.
