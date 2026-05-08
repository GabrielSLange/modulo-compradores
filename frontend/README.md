## 🛒 Portal B2B — Frontend (Módulo de Demanda)

Este projeto contempla o desenvolvimento do frontend para o módulo da **Equipe 4 — Demanda**, parte integrante de um ecossistema B2B distribuído. A aplicação foi construída em **React com TypeScript**, focando no desacoplamento de serviços e na resiliência necessária para lidar com a consistência eventual do ecossistema **Kafka**.

## 🏗️ Contexto do Projeto

O sistema é baseado em microsserviços onde cada equipe é responsável por seu próprio banco de dados e contexto. O módulo de **Demanda** gerencia a necessidade formal de compra das empresas compradoras, tratando dados de produtos e usuários como projeções locais.

## 🧱 Funcionalidades Principais (Equipe 4)

* **Gestão de Demandas:** Registro de necessidades de compra únicas ou recorrentes.
* **Demandas Recorrentes:** Configuração de frequência (diária, semanal, mensal), datas de vigência e geração automática.
* **Wishlist (Lista de Desejos):** Funcionalidade de intenção de compra informal com opção de conversão para demanda real.
* **Endereços de Entrega:** Cadastro independente de locais de entrega para o comprador, isolado dos endereços globais da Equipe 1.
* **Ciclo de Vida:** Acompanhamento dos status: `aberta`, `em_negociacao`, `atendida` e `cancelada`.



## 📡 Integração e Eventual Consistency
A comunicação entre os serviços é **event-driven**, obrigatória via Kafka.
* **Eventos Publicados:** O frontend interage com a API que publica eventos como `demanda_criada`, `demanda_recorrente_gerada` e `wishlist_item_adicionado`.
* **Projeções de Dados:** Informações de **Produtos** (Equipe 2) e **Empresas** (Equipe 1) são consumidas via API local da Equipe 4, que atua como um cache alimentado por eventos.

## 🛠️ Tecnologias e Requisitos
* **React + TypeScript:** Para garantir a integridade dos dados e tipos do DBML.
* **React Query:** Utilizado para polling de status e gerenciamento de cache assíncrono.
* **Optimistic UI:** Implementação de atualizações otimizadas para melhorar a experiência do usuário em um ambiente assíncrono.

## 🚀 Como Executar
1. **Instalação de Dependências:**
```bash
npm install

```

2. **Configuração de Variáveis de Ambiente:**
Crie um arquivo `.env` na raiz do projeto apontando para a URL da API da Equipe 4.
3. **Execução em Desenvolvimento:**
```bash
npm run dev

```

4. **Build para Produção:**
```bash
npm run build

```



## 📋 Regras de Domínio Aplicadas
* **RN-DEM-02:** Diferenciação clara entre demandas únicas e recorrentes.
* **RN-DEM-03:** Obrigatoriedade de dados de recorrência quando o flag `is_recorrente` está ativo.
* **RN-INT-04:** Responsabilidade total do serviço pelos seus próprios dados de entrega e demandas.