# Módulo Equipe 4 — Demanda (Front-End)

Documentação técnica do front-end do microserviço **SDI.Micro.Demanda**, parte de um sistema B2B distribuído baseado em microserviços e Kafka.

---

## 1. Visão Geral

Este módulo é responsável pela interface de gestão de **Demandas** (intenções de compra), **Wishlist** (itens desejados) e **Endereços de Entrega** das empresas compradoras.

O front foi construído de forma **totalmente desacoplada** do back-end, tratando dados de outros bounded contexts (ex.: Produto, da Equipe 2) como **projeções locais** alimentadas por eventos Kafka. Isso significa que a UI precisa lidar com **consistência eventual** — um `id_produto` pode existir em uma demanda sem que os dados completos do produto já tenham sido sincronizados localmente.

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
├── components/
│   └── ui/
│       ├── async-select.tsx        # Select reutilizável com estados loading/error/empty
│       └── ...                     # Demais componentes shadcn/ui
│
├── features/
│   ├── types.ts                    # Tipos do domínio compartilhados entre todas as features
│   │
│   ├── demandas/
│   │   ├── components/
│   │   │   ├── DemandasTab.tsx         # Listagem + filtros (ID/produto) + ações
│   │   │   ├── NovaDemandaDialog.tsx   # Formulário de criação (Zod + superRefine)
│   │   │   ├── VisualizarDemandaDialog.tsx  # Detalhes completos de uma demanda
│   │   │   └── StatusBadge.tsx         # Badge visual por status
│   │   ├── hooks/
│   │   │   └── useDemandas.ts          # useQuery + useMutation (create/updateStatus) com optimistic UI
│   │   └── mocks/
│   │       └── store.ts                # Dados de seed para desenvolvimento local
│   │
│   ├── enderecos/
│   │   ├── components/
│   │   │   ├── EnderecosTab.tsx        # Tabela de endereços + ações de editar/excluir
│   │   │   └── EnderecoDialog.tsx      # Formulário de criação/edição de endereço
│   │   └── hooks/
│   │       └── useEnderecos.ts         # useQuery + mutations (create/update/delete)
│   │
│   ├── produtos/
│   │   ├── components/
│   │   │   └── ProdutoCell.tsx         # Renderização da projeção local de Produto
│   │   └── hooks/
│   │       └── useProduto.ts           # useQuery para listar projeções de produtos
│   │
│   └── wishlist/
│       ├── components/
│       │   └── WishlistTab.tsx         # Listagem + formulário de adição + conversão em demanda
│       └── hooks/
│           └── useWishlist.ts          # useQuery + mutations (add/convert)
│
├── services/
│   ├── api.ts              # Cliente HTTP genérico (fetch wrapper com JWT e ApiError)
│   ├── auth.ts             # Gerenciamento de token JWT (get/set/clear no localStorage)
│   ├── demandaService.ts   # Funções HTTP do domínio Demanda
│   ├── enderecoService.ts  # Funções HTTP do domínio Endereço
│   ├── produtoService.ts   # Funções HTTP do domínio Produto (projeção local)
│   └── wishlistService.ts  # Funções HTTP do domínio Wishlist
│
├── routes/
│   ├── __root.tsx          # Shell da aplicação + QueryClientProvider + Toaster
│   └── index.tsx           # Página principal com as três abas (Tabs)
│
└── styles.css              # Design tokens globais (Midnight Green + Orange CTA)
```

### Princípio de Organização: Feature-First

Cada feature é **autocontida**: componentes, hooks e lógica de UI ficam dentro da pasta da feature, enquanto a comunicação com a API é responsabilidade exclusiva da camada `services/`. Isso significa:

- **Components** só enxergam **hooks** — nunca chamam `services` diretamente.
- **Hooks** só enxergam **services** — nunca fazem `fetch` diretamente.
- **Services** só enxergam `api.ts` — nunca usam React.

---

## 4. Camada de Serviços (`src/services/`)

### 4.1. `api.ts` — Cliente HTTP

Wrapper genérico sobre `fetch`. Responsabilidades:
- Anexa `Content-Type: application/json` automaticamente.
- Injeta o JWT (quando existir) via header `Authorization: Bearer <token>`.
- Lança `ApiError` em respostas não-2xx, carregando o `status` HTTP e o payload do erro.
- Em `401`, chama `clearToken()` para forçar novo login.
- Usa rotas **sempre relativas** (`/api/...`) para que o Nginx/Gateway faça o proxy.

```ts
// Exemplo de uso
const demandas = await api.get<Demanda[]>("/api/demandas");
const nova = await api.post<Demanda>("/api/demandas", payload);
await api.patch(`/api/demandas/${id}/cancelar`);
await api.delete(`/api/demandas/enderecos/${id}`);
```

### 4.2. `auth.ts` — Gerenciamento de Token

Abstrai o acesso ao `localStorage` para o token JWT. Funções: `getToken()`, `setToken(t)`, `clearToken()`.

> **Atenção:** Enquanto a autenticação real não é implementada, os services injetam IDs mock diretamente (`MOCK_USUARIO_ID = "u-1"`, `MOCK_EMPRESA_ID = "emp-1"`). Quando o JWT for implementado, basta substituir por `getToken()` e decodificar os claims.

### 4.3. Services de Domínio

Cada arquivo de service encapsula as chamadas HTTP de um domínio e **traduz nomes de campo** quando necessário (ex.: o frontend usa `id_endereco_entrega` internamente, mas o backend espera `id_endereco_destino` — essa tradução ocorre em `criarDemanda()`).

| Arquivo | Rota base | Operações |
|---|---|---|
| `demandaService.ts` | `/api/demandas` | listar, criar, cancelar, atualizar status |
| `enderecoService.ts` | `/api/demandas/enderecos` | listar, criar, atualizar, excluir (soft delete) |
| `produtoService.ts` | `/api/demandas/produtos` | listar projeções locais |
| `wishlistService.ts` | `/api/demandas/wishlist` | listar, adicionar, converter em demanda |

---

## 5. Domínio e Entidades (`src/features/types.ts`)

Os tipos espelham o DBML do banco isolado do serviço:

- **`Demanda`** — intenção de compra. Pode ser **única** ou **recorrente**. Status: `aberta | em_negociacao | atendida | cancelada`. Usa `id_endereco_entrega` como referência ao endereço de destino.
- **`DemandaRecorrencia`** — `frequencia` (`diaria | semanal | mensal`), `data_inicio`, `data_fim?`, `dia_preferencial`.
- **`WishlistItem`** — item desejado, conversível em Demanda. Mantém `convertida_em_demanda` e `id_demanda_gerada`.
- **`EnderecoEntrega`** — endereço da empresa compradora, usado como destino da demanda.
- **`ProdutoProjecao`** — **projeção local** de Produto (Equipe 2). Alimentada por eventos Kafka. Pode estar ausente quando o evento ainda não foi consumido.

---

## 6. Estratégia de Consistência Eventual

### 6.1. Polling de eventos Kafka

Enquanto o WebSocket de eventos não existe, `useDemandas` usa `refetchInterval: 8000` para simular a reatividade do barramento:

```ts
useQuery({
  queryKey: ["demandas"],
  queryFn: () => listarDemandas(),
  refetchInterval: 8000,
  staleTime: 4000,
});
```

Quando o backend implementar WebSocket, basta substituir por uma `subscription` e chamar `queryClient.setQueryData(["demandas"], novaLista)` no callback.

### 6.2. Projeção local de Produto (`ProdutoCell`)

O componente lida com **três estados** de forma elegante:

| Estado | Renderização |
|---|---|
| `loading` | `Skeleton` (cache local sendo lido) |
| sincronizado | nome + código + categoria + unidade |
| inexistente | fallback **"Produto não identificado"** + `id_produto` em monoespaço |

---

## 7. Componentes Reutilizáveis (`src/components/ui/`)

### `AsyncSelect`

Componente wrapper sobre o `Select` do shadcn/ui que abstrai os estados assíncronos:

```tsx
<AsyncSelect
  value={form.watch("id_produto")}
  onValueChange={(v) => form.setValue("id_produto", v)}
  isLoading={isLoadingProdutos}
  isError={isErrorProdutos}
  options={produtos?.map((p) => ({ value: p.id, label: p.nome }))}
  placeholder="Selecione um produto"
  loadingMessage="Carregando produtos..."
  errorMessage="Erro ao carregar produtos"
  emptyMessage="Nenhum produto cadastrado"
/>
```

Props:

| Prop | Tipo | Descrição |
|---|---|---|
| `value` | `string?` | Valor selecionado (controlado) |
| `onValueChange` | `(v: string) => void` | Callback de seleção |
| `isLoading` | `boolean?` | Exibe mensagem de loading e desabilita |
| `isError` | `boolean?` | Exibe mensagem de erro e desabilita |
| `options` | `{ value, label }[]?` | Lista de opções |
| `placeholder` | `string?` | Texto quando nenhuma opção está selecionada |
| `loadingMessage` | `string?` | Texto exibido durante o carregamento |
| `errorMessage` | `string?` | Texto exibido em caso de erro |
| `emptyMessage` | `string?` | Texto quando não há opções disponíveis |

> **Nota de implementação:** O componente usa `key={value || "__empty__"}` para forçar remontagem quando o formulário é resetado para `""`, evitando o warning do React sobre componentes alternando entre controlled/uncontrolled.

---

## 8. UX Assíncrona

- **Optimistic UI** em `useCreateDemanda` e `useUpdateStatus`: a alteração aparece **imediatamente** na lista; em caso de erro da API, o `onError` faz **rollback** do cache para o snapshot anterior e dispara um toast de erro.
- **Skeleton loaders** durante o primeiro fetch (tabela e células de produto).
- **Toasts (sonner)** explicitando o evento publicado: `demanda_criada`, `demanda_cancelada`, `wishlist_item_adicionado`, `wishlist_convertida_em_demanda`.
- **Botão de refresh manual** com ícone animado (spin) + toast de confirmação enquanto o refetch acontece.
- **Indicador de polling** no rodapé da tabela de demandas.

---

## 9. Fluxos Principais

### 9.1. Criar Demanda

1. Usuário clica em **"Nova demanda"** → `NovaDemandaDialog` abre.
2. Formulário Zod com `superRefine`: campos de recorrência (`frequencia`, `data_inicio`, `dia_preferencial`) só são obrigatórios quando `is_recorrente === true`.
3. Ao submeter, `useCreateDemanda` (hook) chama `criarDemanda` (service), que injeta os IDs mock e traduz `id_endereco_entrega → id_endereco_destino` antes de enviar ao backend.
4. **Optimistic UI**: a nova demanda aparece imediatamente na tabela. Ao confirmar da API, a query é invalidada e os dados reais substituem o otimismo.
5. `onSuccess` do `mutate` fecha o dialog e reseta o formulário.

### 9.2. Cancelar Demanda

Ação inline na linha da tabela. Usa `PATCH /api/demandas/{id}/cancelar` com optimistic update — a linha é atualizada imediatamente; rollback automático se a API falhar.

### 9.3. Visualizar Demanda

O ícone de olho (`Eye`) abre `VisualizarDemandaDialog`, que busca o endereço correspondente na lista já cacheada via `useEnderecos` — sem requisição adicional.

### 9.4. Buscar Demandas

O campo de busca filtra **ao mesmo tempo** por ID da demanda e por nome/código do produto (usando os dados já cacheados de `useProdutos`). Filtragem é feita com `useMemo` no cliente — sem round-trip ao servidor.

### 9.5. Wishlist → Demanda

1. Usuário clica em **"Converter"** na linha da wishlist.
2. Dialog solicita o endereço de entrega.
3. `useConvertWishlist` chama `POST /api/demandas/wishlist/{id}/converter` com `{ id_endereco_destino, quantidade_desejada, prioridade }`.
4. Ao converter, a query de wishlist e de demandas são invalidadas simultaneamente.

### 9.6. CRUD de Endereços

- **Criar:** `EnderecoDialog` sem prop `endereco` — formulário em branco.
- **Editar:** `EnderecoDialog` com prop `endereco` — formulário pré-preenchido via `useEffect` ao abrir.
- **Excluir:** Botão de lixeira com confirmação inline. Usa soft delete no backend (`ativo = false`).

---

## 10. Design System

- Paleta **Midnight Green + Orange CTA**, definida como padrão entre os times.
- Tokens definidos em `src/styles.css` em formato HSL: `--primary`, `--secondary`, `--accent`, `--muted`, `--shadow-card`, `--shadow-elevated`, etc.
- **Componentes não usam cores literais** (`bg-white`, `text-black`) — apenas tokens semânticos (`bg-card`, `text-primary`, `border-border`).
- **Dark mode** via toggle no header (classe `.dark` no `<html>`).

---

## 11. Como Rodar

```bash
# Instalar dependências
npm install

# Rodar em modo de desenvolvimento
npm run dev
```

A aplicação sobe em `http://localhost:3000` e conecta ao backend em `http://localhost:8080`. A página principal está em `src/routes/index.tsx` e organiza o módulo em três abas: **Demandas**, **Wishlist** e **Endereços**.

> **Pré-requisito:** O backend Python (`backend/main.py`) deve estar rodando na porta `8080` para que as chamadas de API funcionem.

---

## 12. Substituindo os Mocks de Autenticação

Atualmente, os services injetam IDs fixos de usuário e empresa:

```ts
// demandaService.ts
const MOCK_USUARIO_ID = "u-1";
const MOCK_EMPRESA_ID = "emp-1";
```

Quando a autenticação JWT for implementada, o passo a passo é:

1. Em `auth.ts`, implemente `setToken(token)` após o login.
2. Em cada service, substitua as constantes mock por:
   ```ts
   import { getToken } from "./auth";
   // Decodifique o JWT para extrair id_usuario e id_empresa dos claims
   ```
3. O `api.ts` já injeta o header `Authorization: Bearer <token>` automaticamente — nenhuma mudança necessária no cliente HTTP.

---

## 13. Próximos Passos

- [ ] Substituir polling (`refetchInterval`) por WebSocket para eventos Kafka em tempo real.
- [ ] Implementar autenticação JWT real e remover constantes mock dos services.
- [ ] Adicionar tela de histórico de propostas por demanda (integração com Equipe 5).
- [ ] Testes com Vitest + Testing Library nos hooks de optimistic UI.
- [ ] Internacionalização (i18n) caso necessário.