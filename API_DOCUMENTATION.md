# Documentação Oficial da API - Módulo de Compradores (Equipe 4)

Este documento detalha a arquitetura, endpoints, contratos de dados e integrações (Kafka) do Módulo de Compradores (Demandas, Wishlist e Pedidos) do Portal B2B. A documentação reflete o estado atual e exato da implementação tanto no backend (FastAPI) quanto no frontend (React).

---

## 🏗️ Arquitetura e Fluxos do Sistema

O módulo expõe uma API REST para o Frontend e consome/publica eventos assíncronos via Apache Kafka. 

### Diferença Central: Demanda x Pedido

- **Demanda:** É uma *intenção de compra* aberta ao mercado. O comprador informa o que precisa, mas ainda não há um compromisso firmado com um fornecedor específico.
- **Pedido:** É uma demanda *efetivada e validada*. Ocorre quando o sistema confirma (via serviço de estoque/fornecimento) que há um fornecedor apto a atender a necessidade. A partir desse momento, o ciclo de faturamento e entrega pode ser iniciado.

### Fluxos Principais

1. **Criação de Demanda:** 
   O comprador informa produto, quantidade, prioridade e endereço. 
   *Recorrência:* Pode ser definida como **recorrente** (diária, semanal, mensal). Uma rotina de background (Cron/Job) avalia periodicamente a tabela de recorrências e gera automaticamente novas demandas conforme o cronograma.
   *Efeito:* Salva no banco e publica evento `demanda_criada` no Kafka.

2. **Fluxo de Wishlist:**
   O comprador adiciona um produto à wishlist (intenção preliminar) de forma simplificada, não sendo obrigatório informar endereço, quantidade e preço máximo. Status inicial é `pendente`.
   A **conversão** da wishlist para demanda exige que os dados pendentes (endereço, quantidade > 0, prioridade) sejam fornecidos. Isso gera uma nova Demanda real e atualiza o item da wishlist para `convertido_em_demanda = true`.

3. **Fluxo de Demanda para Pedido (Promoção):**
   Uma demanda "aberta" pode ser promovida para "pedido".
   *Validação:* O `EstoqueService` consulta o banco `fornecimento_db` para garantir que há fornecedor apto a atender a quantidade desejada. Se sim, marca `is_pedido = true`. Se não, a transação falha (HTTP 422) e a demanda continua aberta.
   *Efeito:* Publica evento `pedido_criado` no Kafka com a indicação do `id_fornecedor_apto`.

4. **Atualização de Status:**
   As demandas (e pedidos) fluem pelos status: `aberta` -> `em_negociacao` -> `atendida` (ou `cancelada` a qualquer momento). 
   Se o status de um *pedido* for alterado, o sistema publica o evento `pedido_atualizado` no Kafka. Demandas simples (não promovidas) não emitem esse evento na mudança de status.

5. **Consistência Eventual (Produtos e Pedidos):**
   Consumidores Kafka rodam em background (Threads) para espelhar produtos cadastrados na tabela `produto_cache`. Essa estratégia permite alta disponibilidade no frontend (evitando dependência síncrona da Equipe 2) e permite a atualização assíncrona do status de pedidos notificados pela Equipe 7. O lag típico é de poucos milissegundos.

---

## 🔐 Autenticação, Autorização e Headers

**MUITO IMPORTANTE:** Todas as rotas protegidas exigem o envio do token no header `Authorization`.

- **Headers Obrigatórios:**
  - `Authorization: Bearer <seu_token_jwt>`
  - `Content-Type: application/json` (para métodos POST, PUT, PATCH)
  - `Accept: application/json`
- **Isolamento de Dados (Tenant):** 
  - O token deve obrigatoriamente conter as claims `sub` (ID do usuário) e `empresa_id` (ID da empresa compradora).
  - **Regra de Ouro:** Uma empresa compradora jamais terá acesso aos dados (demandas, pedidos, wishlist, endereços) de outra empresa. Os endpoints injetam o `empresa_id` implicitamente nas consultas e criações (Data/Tenant Isolation).
- **Comportamento de Erro:** 
  - Acesso sem token, token expirado ou sem as claims necessárias resulta em HTTP `401 Unauthorized`.
  - Tentativa de acesso a um recurso de outra empresa retorna `404 Not Found` (por questões de segurança) ou `403 Forbidden`.
- **Padrão no Frontend:** A camada HTTP base (`services/api.ts`) injeta automaticamente o cabeçalho `Authorization`. Requisições que retornam `401` limpam o token, forçando novo login. Os IDs de usuário e empresa NÃO devem ser enviados nos payloads.

### Formato Padrão de Erros e Validações

Falhas de validação de payload (ex: `quantidade_desejada` negativa) ou regras de negócio retornam HTTP `400 Bad Request` ou `422 Unprocessable Entity` com o seguinte formato JSON padrão do FastAPI:
```json
{
  "detail": "Mensagem descritiva do erro explicando o motivo da falha."
}
```

---

## 🌐 Endpoints da API REST

A API do backend mapeia as rotas diretamente na raiz. Através do Gateway ou Proxy (como o vite proxy do frontend), elas costumam ser chamadas com o prefixo `/api/demandas`.

### 1. Demandas e Pedidos

Gerencia o ciclo de vida das intenções de compra e pedidos.

#### `POST /`
Cria uma nova demanda.
- **Body:**
  ```json
  {
    "id_produto": "uuid-do-produto",
    "id_endereco_destino": "uuid-do-endereco", // Frontend pode enviar "id_endereco_entrega", mas o serviço mapeia
    "quantidade_desejada": 10.5,
    "preco_maximo": 1500.00, // Opcional
    "prioridade": "media",   // "baixa", "media" ou "alta"
    "observacao": "Detalhes...", // Opcional
    "is_recorrente": false,
    "recorrencia": {         // Obrigatório se is_recorrente = true
      "frequencia": "semanal",
      "quantidade_por_periodo": 10.5,
      "data_inicio": "2024-01-01",
      "data_fim": "2024-12-31", // Opcional
      "dia_preferencial": "segunda-feira"
    }
  }
  ```
- **Response (201 Created):** Retorna o `DemandaResponseDTO`.

#### `GET /`
Lista todas as demandas da empresa autenticada.
- **Query Params:** `is_pedido` (Opcional, boolean) – Filtra se busca apenas demandas (`false`) ou apenas pedidos (`true`).
- **Response (200 OK):** Retorna um array de `DemandaResponseDTO`.

#### `PATCH /{id_demanda}/status`
Atualiza o status de uma demanda ou pedido existente.
- **Body:**
  ```json
  {
    "status": "em_negociacao" // "aberta", "em_negociacao", "atendida", "cancelada"
  }
  ```
- **Response (200 OK):** Retorna o `DemandaResponseDTO` atualizado.
- **Nota:** Se `is_pedido` for `true`, dispara o evento `pedido_atualizado` no Kafka.

#### `PATCH /{id_demanda}/cancelar`
Cancela uma demanda (atualiza o status para `cancelada`).
- **Response (200 OK):** Retorna o `DemandaResponseDTO` atualizado.

#### `PATCH /{id_demanda}/promover`
Promove uma demanda aberta a pedido. O serviço checa disponibilidade no banco de estoque `fornecimento_db`.
- **Validações e Erros:** 
  - `400 Bad Request` ou `422 Unprocessable Entity`: Demanda não encontrada, ou cancelada, ou nenhum fornecedor com estoque apto.
  - `503 Service Unavailable`: Falha de conexão com serviço de estoque.
- **Response (200 OK):** Retorna o `DemandaResponseDTO` com `is_pedido = true`.
- **Nota:** Dispara evento `pedido_criado` se houver fornecedor apto.

---

### 2. Endereços de Entrega

Gerencia os locais de recebimento de mercadorias.

#### `POST /enderecos`
Cadastra um novo endereço de entrega.
- **Body:**
  ```json
  {
    "apelido": "Sede Principal", // Opcional
    "logradouro": "Avenida Paulista",
    "numero": "1000",            // Opcional
    "complemento": "Andar 5",    // Opcional
    "bairro": "Bela Vista",      // Opcional
    "cidade": "São Paulo",
    "uf": "SP",                  // ou "estado"
    "cep": "01310-100",
    "latitude": -23.561,         // Opcional
    "longitude": -46.656         // Opcional
  }
  ```
- **Response (201 Created):** Retorna o `EnderecoResponseDTO`.

#### `GET /enderecos`
Lista todos os endereços ativos da empresa.
- **Response (200 OK):** Array de `EnderecoResponseDTO`.

#### `PUT /enderecos/{id_endereco}`
Atualiza os dados de um endereço.
- **Body:** Mesmo schema da criação.
- **Response (200 OK):** Retorna o endereço atualizado.
- **Erro:** `404 Not Found` caso o endereço não exista ou não pertença à empresa.

#### `DELETE /enderecos/{id_endereco}`
Deleta logicamente (soft delete) o endereço.
- **Response (204 No Content).**
- **Erro:** `404 Not Found` caso o endereço não seja da empresa.

---

### 3. Wishlist (Lista de Desejos)

Armazena intenções preliminares de compra.

#### `POST /wishlist`
Adiciona um item à wishlist.
- **Body:**
  ```json
  {
    "id_produto": "uuid-do-produto",
    "quantidade_desejada": 5, // Opcional
    "preco_maximo": 1200.0,   // Opcional
    "prioridade": "baixa",    // Opcional
    "observacao": "Apenas cotando" // Opcional
  }
  ```
- **Response (201 Created):** Retorna o `WishlistResponseDTO`.

#### `GET /wishlist`
Lista itens pendentes da wishlist da empresa.
- **Response (200 OK):** Array de `WishlistResponseDTO`.

#### `POST /wishlist/{id_item}/converter`
Converte um item de wishlist numa Demanda real, exigindo os dados faltantes.
- **Body:**
  ```json
  {
    "id_endereco_destino": "uuid-endereco", // Frontend pode enviar "id_endereco_entrega"
    "quantidade_desejada": 10,
    "prioridade": "media"
  }
  ```
- **Response (200 OK):** Retorna o modelo recém-gerado `DemandaResponseDTO`. (Nota: status devolve um modelo de demanda, não de wishlist).

---

### 4. Cache de Produtos (Projeção)

Endpoints exclusivos de leitura (`Read-Model`) mantidos pelo consumer Kafka, utilizados pelo frontend (ex: listagens, exibição de nome/código sem depender da Equipe 2 síncrona).

#### `GET /produtos/projecao`
Retorna todos os produtos presentes no cache local.
- **Response (200 OK):** Array de `ProdutoProjecaoDTO`.

#### `GET /produtos/projecao/{id_produto}`
Busca detalhes de um produto específico.
- **Response (200 OK):** Retorna um objeto `ProdutoProjecaoDTO` contendo `id`, `codigo`, `nome`, `categoria`, `unidade`, `sincronizado_em`.
- **Erros:**
  - `400 Bad Request` se receber a string literal `"null"`.
  - `404 Not Found` se o produto não constar no cache local.

---

## 🔗 Integração Kafka (Mensageria)

O módulo utiliza Kafka para a comunicação assíncrona entre domínios.

### 📥 Eventos Consumidos (Background Jobs)

As rotinas de consumidor rodam em threads assíncronas no contexto do FastAPI (iniciadas no `lifespan`). 
Em caso de falhas transitórias, os consumers implementam retentativas lógicas. Em caso de falha permanente, as mensagens não processadas podem ser direcionadas a uma fila de mensagens mortas (DLQ - Dead Letter Queue) para auditoria, não travando o consumo.

- **Consumer de Produtos (`produto_consumer`):** Escuta tópico de produtos e reflete os dados (nome, código) na tabela `produto_cache`. Apenas consome eventos sem impactar as demandas já criadas.
- **Consumer de Pedidos (`pedido_consumer`):** Escuta criação/atualização de pedidos (da Equipe 7) para atualizar o status da demanda associada no banco de compradores.

### 📤 Eventos Produzidos

Os produtores publicam eventos para notificar o ecossistema B2B. O payload sempre viaja no formato JSON serializado:

1. **`demanda_criada`:** Disparado ao criar uma demanda manual, converter wishlist ou via job de demandas recorrentes (`DemandaProducer.publicar_demanda_criada`). 
   *Payload Real:* Inclui `id_demanda`, `id_produto`, `quantidade_desejada`, `preco_maximo`, `prioridade`, e timestamp de criação.
2. **`pedido_criado`:** Disparado pelo processo de promoção. 
   *Payload Real:* Informa a efetivação da demanda contendo o `id_demanda`, `id_produto`, quantidade e o `id_fornecedor_apto` checado no banco da equipe de fornecimento.
3. **`pedido_atualizado`:** Disparado sempre que o status de uma demanda já promovida (`is_pedido=true`) muda de estado (ex: para `atendida` ou `em_negociacao`).

---

## 🖥️ Integração e Modelos no Frontend

O frontend gerencia estados globais e interações por meio de hooks (`TanStack Query`) e chamadas através dos Services no diretório `src/services`.

- A classe/objeto `api.ts` serve como proxy para as chamadas e injeta automaticamente o Bearer Token.
- Requisições não-sucesso retornam um `ApiError` formatado.
- Os mapeamentos de nomes de propriedades DTO, como `id_endereco_entrega` (front) para `id_endereco_destino` (back), são realizados dinamicamente nos Services, garantindo transparência para os componentes React.
- Telas/Tabs segmentam visualmente as Demandas das Wishlists e as Demandas normais dos Pedidos Efetivados, aproveitando a flag `is_pedido`.
- O frontend é tolerante a falhas na projeção de produtos: se o ID do produto da demanda não existir no cache local (`/produtos/projecao`), ele trata a falha graciosamente.
