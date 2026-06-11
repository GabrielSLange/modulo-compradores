# Fluxo de Integrações — Módulo de Demandas

Este documento apresenta o fluxo de comunicação do microsserviço **Demandas** (Módulo de Compradores / Nosso Módulo) com os outros módulos do portal B2B, focado no fluxo operacional e de negócios do sistema.

---

## 🗺️ Mapa de Fluxo do Sistema

O fluxograma abaixo mostra como as informações trafegam entre as equipes via API, Banco Compartilhado e Eventos no Barramento (Kafka):

```mermaid
flowchart TB
    %% Estilos Customizados para Aparência Premium
    classDef default fill:#fafafa,stroke:#ddd,stroke-width:1px,color:#444;
    classDef nosso fill:#e8f0fe,stroke:#1a73e8,stroke-width:2px,color:#185abc,font-weight:bold;
    classDef externo fill:#fef7e0,stroke:#ea8600,stroke-width:1px,color:#b06000;
    classDef barramento fill:#e6f4ea,stroke:#137333,stroke-width:2px,color:#137333;
    classDef banco fill:#f3e8ff,stroke:#6b21a8,stroke-width:2px,color:#6b21a8;

    %% Subgraphs para Organização
    subgraph Nosso["📂 Nosso Módulo (Compradores)"]
        Dem["📝 Gestão de Demandas & Pedidos<br/>(Interface & Regras)"]
        Cache["💾 Cache Local de Produtos<br/>(Visualização Rápida)"]
    end

    subgraph Externos["📂 Módulos de Outras Equipes"]
        Log["🚚 Logística (Equipe 8)<br/>- Cotações e Rastreamento"]
        Vend["💰 Vendas & Negociação (Equipe 9)<br/>- Lances e Acordo de Preço"]
        Prod["📦 Catálogo de Produtos (Equipe 2)<br/>- Cadastro Geral"]
    end

    subgraph Canais["⚙️ Barramento e Dados"]
        Kafka{{"⚡ Central de Mensagens (Kafka)"}}
        DB_Shared[("🗄️ Base de Vendas (portal_b2b)")]
    end

    %% Conexões do Fluxo
    
    %% Fluxo de APIs (Logística)
    Dem -->|1. Inicia Frete / Contrata| Log
    
    %% Fluxo de Banco (Estoque de Vendas)
    Dem -.->|Valida estoque no fornecedor| DB_Shared
    
    %% Eventos Produzidos (Para o Barramento)
    Dem ==>|Publica status de Demandas e Pedidos| Kafka
    
    %% Eventos Consumidos (Do Barramento)
    Kafka ===>|Lance Fechado / Acordo Ganho| Dem
    Kafka ===>|Status de Entrega Atualizado| Dem
    Kafka ===>|Novo Produto Cadastrado| Cache
    
    %% Outros alimentando o Barramento
    Vend -.->|Informa fechamento de lance| Kafka
    Log -.->|Informa movimentação de carga| Kafka
    Prod -.->|Informa novos cadastros| Kafka

    %% Vinculação de Classes de Estilo
    class Dem,Cache nosso;
    class Log,Vend,Prod externo;
    class Kafka barramento;
    class DB_Shared banco;
```

---

## ⏳ Linha do Tempo: Do Cadastro à Entrega

Este fluxograma sequencial ilustra a jornada completa de uma compra — desde o cadastro inicial do produto até a entrega final ao comprador — destacando as interações entre as diferentes equipes do sistema:

```mermaid
flowchart TD
    %% Estilos Customizados
    classDef default fill:#fafafa,stroke:#ddd,stroke-width:1px,color:#444;
    classDef nosso fill:#e8f0fe,stroke:#1a73e8,stroke-width:2px,color:#185abc,font-weight:bold;
    classDef externo fill:#fef7e0,stroke:#ea8600,stroke-width:1px,color:#b06000;

    subgraph Col_Esquerda ["📂 Nosso Módulo (Compradores)"]
        P2["Etapa 2: Intenção de Compra<br/>(Cadastra demanda local)"]
        P5["Etapa 5: Geração de Pedido<br/>(Promove demanda a pedido)"]
        P7["Etapa 7: Contratação de Frete<br/>(Escolhe e aprova na tela)"]
        P9["Etapa 9: Entrega Concluída<br/>(Pedido finalizado como atendido)"]
    end

    subgraph Col_Direita ["📂 Outros Módulos do Sistema"]
        P1["Etapa 1: Cadastro de Produto<br/>(Equipe 2 - Produtos)"]
        P3["Etapa 3: Negociação & Lances<br/>(Equipe 9 - Vendas)"]
        P4["Etapa 4: Fechamento de Acordo<br/>(Equipe 9 - Vendas)"]
        P6["Etapa 6: Cotação de Carga<br/>(Equipe 8 - Logística)"]
        P8["Etapa 8: Transporte & Rastreio<br/>(Equipe 8 - Logística)"]
    end

    %% Ligações em Zig-Zag com Labels Descritivos
    P1 -->|1. Evento: produto_cadastrado| P2
    P2 -->|2. Evento: demanda_criada| P3
    P3 -->|3. Propostas de fornecedores| P4
    P4 -->|4. Evento: negociacao_fechada| P5
    P5 -->|5. API: POST /demo-iniciar-cotacao| P6
    P6 -->|6. Retorna ofertas de frete| P7
    P7 -->|7. API: POST /demo-contratar-frete| P8
    P8 -->|8. Evento: status_atualizado| P9

    %% Vinculação de Estilos
    class P2,P5,P7,P9 nosso;
    class P1,P3,P4,P6,P8 externo;
```

---

## 🔄 Fluxo de Negócio das Integrações

O ciclo de vida de uma compra passa pelas seguintes interações com módulos externos:

### 1. Criação e Catalogação
* **Com o módulo de Produtos (Equipe 2):** 
  * Sempre que um produto é cadastrado ou atualizado no sistema, nosso módulo consome esse aviso e atualiza um cache de produtos local. Isso garante que a nossa tela sempre mostre os nomes corretos dos produtos sem lentidão.
  * Publicamos um evento no barramento toda vez que uma demanda de compra é criada ou cancelada para que os fornecedores possam ver o interesse do mercado.

### 2. Negociação de Preços
* **Com o módulo de Vendas & Negociação (Equipe 9):**
  * Quando um comprador aceita lances ou a negociação é fechada, o módulo de Vendas envia uma mensagem para o barramento.
  * Ao receber o aviso de negociação ganha, nosso módulo automaticamente promove a intenção de compra a um **Pedido** formalizado.

### 3. Validação e Cotação de Transporte
* **Com a Logística (Equipe 8) e Banco de Vendas:**
  * Para promoções manuais de pedidos, validamos diretamente no banco de dados de Vendas se o fornecedor parceiro ainda possui estoque físico disponível.
  * Assim que o pedido é gerado, nosso sistema faz uma chamada à API de Logística para disparar o processo de cotação de frete.
  * A Logística busca ofertas de transporte e devolve para a nossa tela uma lista com prazos e valores de transportadoras. O comprador escolhe a melhor opção e clica para contratar, notificando a Logística via API.

### 4. Rastreio e Finalização
* **Com a Logística (Equipe 8):**
  * À medida que a transportadora movimenta a mercadoria, a Logística publica atualizações de rastreamento no barramento.
  * Nosso módulo escuta e atualiza a tela do comprador em tempo real (ex.: mostrando status como "Em Trânsito"). Quando a carga é marcada como "Entregue", finalizamos o status do pedido local.
