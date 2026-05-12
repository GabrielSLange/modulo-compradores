# Módulo Equipe 4 — Demanda (Front-End)

Documentação técnica do front-end do microserviço **SDI.Micro.Demanda**, parte de um sistema B2B distribuído baseado em microserviços e Kafka.

---

## 1. Visão Geral

Este módulo é responsável pela interface de gestão de **Demandas** (intenções de compra), **Wishlist** (itens desejados) e **Endereços de Entrega** das empresas compradoras.

O front foi construído de forma **totalmente desacoplada** do back-end, tratando dados de outros bounded contexts (ex.: Produto, da Equipe 2) como **projeções locais** alimentadas por eventos Kafka. Isso significa que a UI precisa lidar com **consistência eventual** — um `id_produto` pode existir em uma demanda sem que os dados completos do produto já tenham sido sincronizados localmente.

> **Estado atual:** o back-end ainda não está disponível. Toda a camada de dados está coberta por **mocks em memória** com latência artificial e simulação de eventos do *Matching Engine* (Equipe 5). A integração real é uma troca direta na camada de mocks, sem mexer em componentes.

---

## 2. Stack Tecnológica

| Camada | Tecnologia |
|---|---|
| Linguagem | TypeScript |
| Framework | React 19 + TanStack Start (SSR) + Vite 7 |
| Roteamento | TanStack Router (file-based) |
| Estado server-side | TanStack Query (cache, polling, optimistic UI) |
| Estilização | Tailwind CSS v4 + design tokens em `src/styles.css` |
| Componentes | shadcn/ui (Radix Primitives) |
| Validação | Zod (com `superRefine` para regras condicionais) |
| Datas | date-fns |
| Ícones | lucide-react |
| Notificações | sonner (toasts) |

---

## 3. Arquitetura de Pastas

```text
src/
├── features/demanda/
│   ├── components/
│   │   ├── DemandasTab.tsx         # Listagem + filtros + ações
│   │   ├── WishlistTab.tsx         # Itens desejados + conversão em demanda
│   │   ├── EnderecosTab.tsx        # CRUD de endereços de entrega
│   │   ├── NovaDemandaDialog.tsx   # Formulário (Zod + superRefine)
│   │   ├── ProdutoCell.tsx         # Renderização da projeção de Produto
│   │   └── StatusBadge.tsx         # Badge visual por status
│   ├── hooks/
│   │   ├── useDemandas.ts          # query + mutations (create/updateStatus)
│   │   ├── useWishlist.ts          # query + add + convert
│   │   ├── useEnderecos.ts         # query + create
│   │   └── useProduto.ts           # leitura da projeção local
│   ├── mocks/
│   │   └── store.ts                # API simulada + tick do Matching Engine
│   └── types.ts                    # Tipos do domínio (espelham o DBML)
├── routes/
│   ├── __root.tsx                  # Shell + QueryClientProvider
│   └── index.tsx                   # Página principal com Tabs
└── styles.css                      # Design tokens (Midnight Green + Orange)
```

A pasta `features/demanda/` é **autocontida**: tudo que diz respeito ao domínio mora ali, facilitando extração futura para um pacote ou microfront.

---

## 4. Domínio e Entidades

Os tipos em `src/features/demanda/types.ts` espelham 1:1 o DBML do banco isolado do serviço:

- **`Demanda`** — intenção de compra. Pode ser **única** ou **recorrente**. Status: `aberta | em_negociacao | atendida | cancelada`.
- **`DemandaRecorrencia`** — `frequencia` (`diaria | semanal | mensal`), `data_inicio`, `data_fim?`, `dia_preferencial`.
- **`WishlistItem`** — item desejado, conversível em Demanda. Mantém `convertida_em_demanda` e `id_demanda_gerada`.
- **`EnderecoEntrega`** — endereço da empresa compradora, usado como destino da demanda.
- **`ProdutoProjecao`** — **projeção local** de Produto (Equipe 2). Alimentada por eventos Kafka. Pode estar ausente quando o evento ainda não foi consumido.

---

## 5. Estratégia de Consistência Eventual

Esta é a parte central da arquitetura.

### 5.1. Polling de eventos Kafka

Enquanto o WebSocket de eventos não existe, `useDemandas` usa `refetchInterval: 8000` para simular a reatividade do barramento:

```ts
useQuery({
  queryKey: ["demandas"],
  queryFn: () => mockApi.listDemandas(),
  refetchInterval: 8000,
  staleTime: 4000,
});
```

Quando o back estiver pronto, basta substituir por uma `subscription` WebSocket e `queryClient.setQueryData` no callback.

### 5.2. Projeção local de Produto (`ProdutoCell`)

O componente lida com **três estados** de forma elegante:

| Estado | Renderização |
|---|---|
| `loading` | `Skeleton` (cache local sendo lido) |
| sincronizado | nome + código + categoria + unidade |
| inexistente | fallback **"Produto não identificado"** + `id_produto` em monoespaço, com aviso de "aguardando sincronização" |

Isso permite que a UI continue funcional mesmo quando um evento `produto_criado` ainda não chegou no banco local do serviço de Demanda.

### 5.3. Tick do Matching Engine

`mockApi.tickStatus()` é chamado a cada `listDemandas` e, com 15% de chance, promove uma demanda `aberta → em_negociacao`. Isso simula eventos publicados pela **Equipe 5 (Matching Engine)** chegando via Kafka, dando vida ao polling.

---

## 6. UX Assíncrona

- **Optimistic UI** em `useCreateDemanda` e `useUpdateStatus`: a alteração aparece **imediatamente** na lista; em caso de erro da API, o `onError` faz **rollback** do cache para o snapshot anterior e dispara um toast.
- **Skeleton loaders** durante o primeiro fetch (tabela e células de produto).
- **Toasts (sonner)** explicitando o evento que seria publicado pelo back: `demanda_criada`, `demanda_cancelada`, `wishlist_item_adicionado`, `wishlist_convertida_em_demanda`. Útil também como contrato visível para os outros times.
- **Indicador de polling** no rodapé da tabela ("sincronizado a cada 8s").

---

## 7. Fluxos Principais

### 7.1. Criar Demanda

`NovaDemandaDialog.tsx` usa Zod com `superRefine`: os campos de recorrência (`frequencia`, `data_inicio`, `dia_preferencial`) só são obrigatórios quando `is_recorrente === true`. Isso evita validações falsas em demandas únicas.

### 7.2. Cancelar Demanda

Ação inline na linha da tabela com optimistic update. Linha some/atualiza imediatamente; rollback se a API falhar.

### 7.3. Wishlist → Demanda

`useConvertWishlist` exige escolha de `id_endereco_entrega`, cria uma nova Demanda usando `mockApi.createDemanda` (reaproveitando todo o fluxo, inclusive eventos), marca o item como convertido e invalida tanto a query de wishlist quanto a de demandas.

### 7.4. Endereços

CRUD simples para alimentar o `Select` de entrega no formulário de demanda.

---

## 8. Design System

- Paleta **Midnight Green + Orange CTA**, mantida em consistência com o módulo de Produto (padrão definido pelo professor para todos os times).
- Tokens definidos em `src/styles.css` em formato HSL: `--primary`, `--secondary`, `--accent`, `--muted`, `--shadow-card`, `--shadow-elevated`, etc.
- **Componentes não usam cores literais** (`bg-white`, `text-black`) — apenas tokens semânticos do Tailwind (`bg-card`, `text-primary`, `border-border`).
- **Dark mode** via toggle no header (classe `.dark` no `<html>`).

---

## 9. Como Integrar com o Back-End Real

A camada de mocks foi desenhada para minimizar atrito na integração:

1. Em `src/features/demanda/mocks/store.ts`, substituir cada método de `mockApi` por uma chamada `fetch` (ou axios) ao endpoint correspondente do microserviço de Demanda.
2. **Manter as mesmas assinaturas** — nenhum hook ou componente precisa mudar.
3. Adicionar interceptor de **JWT** no client HTTP (header `Authorization: Bearer ...`).
4. Trocar `refetchInterval` por **WebSocket subscription** nos eventos Kafka relevantes (`demanda_atualizada`, `produto_sincronizado`, etc.) e usar `queryClient.setQueryData` para reatividade real.
5. Para a projeção de Produto, ler do endpoint `/produtos/projecao/:id` que consulta a tabela local alimentada pelo consumer Kafka — o fallback "Produto não identificado" continua valendo.

---

## 10. Como Rodar

```bash
bun install
bun dev
```

A aplicação sobe em `http://localhost:8080` (configuração padrão do template). A página principal está em `src/routes/index.tsx` e organiza o módulo em três abas: **Demandas**, **Wishlist** e **Endereços**.

---

## 11. Próximos Passos

- Substituir mocks por API REST do back.
- Adicionar WebSocket para eventos Kafka em tempo real.
- Implementar tela de detalhes da demanda com histórico de propostas (Equipe 5).
- Internacionalização (i18n) caso necessário.
- Testes com Vitest + Testing Library nos hooks de optimistic UI.