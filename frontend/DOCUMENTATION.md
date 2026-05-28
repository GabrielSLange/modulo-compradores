# Módulo Equipe 4 — Demanda (Front-End)

Documentação técnica do front-end do microserviço **SDI.Micro.Demanda**, responsável pela interface de gestão de Demandas (intenções de compra), Pedidos, Wishlist e Endereços de Entrega das empresas compradoras.

O front-end foi projetado de forma **totalmente desacoplada** do back-end, adotando a filosofia **Feature-First** para organizar componentes e lógicas por domínio, além de empregar **consistência eventual** para exibir dados de outros módulos (como os dados de Produtos da Equipe 2, que vêm através de projeções atualizadas via Kafka).

---

## 1. Stack Tecnológica

| Camada | Tecnologia |
|---|---|
| Linguagem | TypeScript |
| Framework | React 19 + Vite |
| Roteamento | TanStack Router (file-based) |
| Gerenciamento de Estado | TanStack Query (cache, refetching, optimistic UI) |
| Estilização | Tailwind CSS v4 + design tokens globais |
| Componentes | shadcn/ui (Radix Primitives) |
| Validação de Formulários | Zod e React Hook Form |
| Datas | date-fns |
| Ícones | lucide-react |
| Notificações | sonner (toasts) |

---

## 2. Arquitetura e Estrutura de Pastas

A arquitetura do projeto segue a divisão **Feature-First**. O código relacionado a uma parte específica do domínio fica confinado em seu diretório de "feature", não misturando as responsabilidades lógicas entre domínios diferentes.

```text
src/
├── components/
│   ├── theme-provider.tsx          # Provider para Dark/Light mode
│   └── ui/                         # Componentes genéricos de UI (shadcn/ui + AsyncSelect)
│
├── features/                       # Módulos de domínio da aplicação
│   ├── tipos genéricos
│   │   └── types.ts                # Definições de interfaces base e DTOs mapeados no frontend
│   ├── demandas/
│   │   ├── components/             # DemandasTab, NovaDemandaDialog, StatusBadge, etc.
│   │   └── hooks/                  # useDemandas (queries e optimistic mutations)
│   ├── enderecos/
│   │   ├── components/             # EnderecosTab, EnderecoDialog
│   │   └── hooks/                  # useEnderecos
│   ├── produtos/
│   │   ├── components/             # ProdutoCell (projeção assíncrona)
│   │   └── hooks/                  # useProduto
│   └── wishlist/
│       ├── components/             # WishlistTab
│       └── hooks/                  # useWishlist
│
├── services/                       # Camada de abstração HTTP (Comunicação estrita via api.ts)
│   ├── api.ts                      # Cliente base (injetor de JWT, tratador de ApiError)
│   ├── auth.ts                     # Persistência de token no LocalStorage
│   ├── demandaService.ts           # Endpoints do domínio Demandas
│   ├── enderecoService.ts          # Endpoints do domínio Endereços
│   ├── produtoService.ts           # Endpoints de leitura da projeção de Produtos
│   └── wishlistService.ts          # Endpoints do domínio Wishlist
│
├── routes/                         # Definições de roteamento do TanStack Router
│   ├── __root.tsx                  # Root layout, injetor de Providers e interceptador de JWT
│   └── index.tsx                   # Rota "/" que orquestra as Tabs (Demandas, Pedidos, Wishlist, Endereços)
│
└── styles.css                      # Estilos globais e tokens de cores
```

---

## 3. Autenticação JWT

A aplicação utiliza JWT (JSON Web Tokens) e depende exclusivamente do backend para decodificar e ler as *claims* de identificação do usuário e da empresa. Nenhum ID do usuário é enviado manualmente nos corpos de requisição (`payloads`).

- **Recepção do Token:** Ao navegar para o portal, a URL pode conter um parâmetro de busca `?jwt=<token>`. O layout raiz `__root.tsx` captura isso no momento em que a aplicação é montada, invoca o `setToken` (salvando no LocalStorage) e remove o parâmetro silenciosamente alterando a URL via `window.history.replaceState`.
- **Injeção nas Requisições:** O wrapper `api.ts` lê automaticamente o LocalStorage (`getToken()`). Se houver um token válido, o cabeçalho `Authorization: Bearer <token>` é anexado na request.
- **Expiração / Erro de Autorização:** Se qualquer chamada retornar o HTTP status `401 Unauthorized`, o cliente `api.ts` automaticamente invoca `clearToken()`, invalidando a sessão no frontend de forma imediata.

---

## 4. Comunicação e Integração de APIs

A camada de interface gráfica (`components`) nunca chama requisições nativas de HTTP ou conhece URLs de endpoints. O fluxo é totalmente unidirecional através das camadas do frontend:

1. A **UI (Components)** despacha intenções através de chamadas aos **Hooks (React Query)**.
2. Os **Hooks (`useDemandas`, etc.)** organizam cache, _optimistic updates_ (Interface Otimista) e invalidações de query, fazendo a ponte final disparando métodos dos **Services**.
3. Os **Services (`demandaService.ts`)** possuem a assinatura dos métodos (por exemplo: `criarDemanda(payload)`), preparam o corpo da requisição e adaptam dados legados — ex: o formulário envia `id_endereco_entrega`, e o serviço converte para a chave `id_endereco_destino` que o backend exige.
4. Por fim, o **`api.ts`** dispara o `fetch` acoplando `headers` necessários.

### Otimismo na Interface (Optimistic Updates)

Para melhoria de UX, ações interativas não bloqueiam a tela esperando a resposta do backend. Hooks de mutação (como `useCreateDemanda`, `useUpdateStatus`, `useFormalizarPedido`) injetam os dados de estado esperado diretamente no cache local do TanStack Query na fase `onMutate`. 
- Caso a API do servidor retorne sucesso, o backend consolida os dados e a query sofre refetch transparente (`invalidateQueries`).
- Caso a API apresente falha (ex: `422 Estoque insuficiente` ao formalizar pedido), o hook reverte magicamente (`rollback`) a lista local para seu estado anterior salvo na memória (`ctx.prev`) e o componente `Sonner` projeta a mensagem de erro. **Nota:** No otimismo de criação, o objeto virtual criado pode utilizar UUIDs mockados (`u-1`) antes da consolidação do backend, porém esse objeto simulado nunca trafega para o backend.

---

## 5. Fluxos Visuais: As Quatro Abas (Tabs)

A Home principal (`index.tsx`) divide a aplicação em quatro abas fundamentais. A tabela de listagens compartilha lógicas de paginação e pagina no front-end, fatiando de `10` a `15` itens por vez.

### 5.1. Aba: Demandas
Exibe as **intenções de compra** não finalizadas. Utiliza o componente interno `<DemandasTab />` (passando o prop padrão de falsidade para `isPedido`).
- **Nova Demanda:** Aciona um dialog que, através do `Zod`, só obriga as datas de periodicidade se a checkbox "Demanda Recorrente" for marcada (`superRefine`).
- **Busca Conjunta:** Permite filtrar via barra de pesquisa buscando no ID alfanumérico da própria demanda ou consultando no nome do produto em _cache local_.
- **Ações:** "Visualizar detalhes", "Cancelar", ou "Formalizar Pedido". 
  - **Formalização em Pedido (Validação de Estoque):** A promoção de uma demanda a pedido **não é incondicional**. Ela só ocorre se o serviço de estoque confirmar que existe fornecedor apto a suprir a `quantidade_desejada`. Se não houver, a API retorna `422` e o frontend intercepta o erro (`useDemandas.ts`), exibindo o alerta "Estoque insuficiente" e mantendo a demanda no status `aberta`.

### 5.2. Aba: Pedidos
Reutiliza o componente base como `<DemandasTab isPedido={true} />`. 
Isso filtra o backend pelas demandas cujo flag `is_pedido` seja verde, identificando intenções que já passaram pelo crivo do serviço de fornecimento e que, no back, dispararam os eventos na malha Kafka para aprovação das demais equipes. Aqui, as ações mudam: você não pode mais formalizar um pedido, apenas acompanhar os status: `em_negociacao` e `atendida`.
- **Criar Pedido Direto:** É possível criar um pedido diretamente clicando em "Novo pedido" a partir desta aba. O frontend reutiliza o componente `NovaDemandaDialog` informando a prop `isPedido=true`. O hook `useCreateDemanda` realiza uma **operação em duas etapas**: ele cria a demanda normal e **imediatamente** aciona a rota de formalização (`promover`). Caso a promoção falhe (ex: falta de estoque de fornecedor), a UI captura o erro `422`, aborta o status de pedido e avisa o comprador.

### 5.3. Aba: Wishlist
Intenções "soltas". Itens desejados onde a quantidade desejada, preço ou prioridade são, num primeiro momento, **opcionais**. Não existe vínculo imediato de endereço.
- **Conversão (`useConvertWishlist`):** A qualquer momento o comprador pode clicar em "Converter", momento onde o frontend forçará o input do localizador ("Endereço de entrega"). Quando bem sucedido, a chamada limpa (invalida) não só o cache do Wishlist mas também do `useDemandas` para que a demanda criada brote instantaneamente na primeira aba.

### 5.4. Aba: Endereços
Listagem tradicional em tabela. Um único modal `EnderecoDialog.tsx` atende a criação e a edição. Se nenhuma prop contendo os dados base do endereço é fornecida ao `<EnderecoDialog />`, ele funciona em modo Inserção; caso contrário, é preenchido como Update.
A deleção de endereços envia um verbo `DELETE` e aguarda retorno `204`, que no backend reflete num _soft delete_.

---

## 6. Projeção de Produtos (Integração Indireta)

Como a Equipe 4 (Demandas) depende do cadastro oficial gerido pela Equipe 2 (Catálogo) que comunica pelo Kafka, o frontend **não fará chamadas síncronas HTTP caindo se o serviço da Equipe 2 estiver fora.**
Em vez disso:
- O frontend consome `/api/demandas/produtos/projecao` na nossa própria base (que é mantida populada por *background jobs* no backend ouvindo o Kafka).
- A UI utiliza o componente tolerante a falhas `<ProdutoCell />`.
  - Se a resposta assíncrona estiver carregando, projeta um `Skeleton`.
  - Se o `id_produto` não retornar nada na busca (produto ainda não chegou no cache ou foi excluído), o frontend degrada graciosamente exibindo texto monoespaçado "Produto não identificado" ou "N/D", permitindo uso ininterrupto da plataforma.

---

## 7. Refetch e Revalidação 

O cache da API no TanStack Query é balanceado pela propriedade `staleTime`. Atualmente, não ocorre *polling infinito constante*, poupando performance na máquina e nos servidores, seguindo a diretriz:
- `useDemandas`: Mantém os dados frescos e imutáveis por **4 segundos**.
- `useWishlist`: Mantém os dados por **5 segundos**.
- `useEnderecos`: Mantém os dados por **30 segundos** (endereços raramente mudam em tempo real).

Para revalidações em tela, as listagens fornecem o botão **"Refresh"** (`<RefreshCw />`) que aciona nativamente a reobtenção (`refetch()`). Eventuais implementações de WebSocket poderão facilmente espetar as suas `subscriptions` chamando os métodos `queryClient.setQueryData` ou `queryClient.invalidateQueries` para plugar o tempo real exato sem necessitar refatorar o React.