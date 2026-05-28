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

### Fluxo Completo: Da UI até a API
1. **Ação do Usuário:** O usuário clica em um botão (ex: "Converter Wishlist" ou "Criar Demanda").
2. **Validação UI:** O `React Hook Form` + `Zod` validam as entradas localmente. Se inválidas, a execução para e exibe os erros no formulário.
3. **Hook (React Query):** A UI despacha a intenção chamando o `mutate` do hook correspondente.
4. **Otimismo (`onMutate`):** O hook aplica uma _Optimistic Update_, atualizando a tela imediatamente antes de consultar o servidor. O estado de carregamento (`isPending`) é ativado.
5. **Service Layer:** O hook delega o envio de dados aos **Services** (ex: `demandaService.ts`). O Service converte chaves se necessário (ex: `id_endereco_entrega` -> `id_endereco_destino`).
6. **Client HTTP (`api.ts`):** Prepara a requisição anexando o JWT no `Authorization`, o `Content-Type: application/json` e dispara contra a API.
7. **Resposta do Backend:**
   - **Sucesso (20x):** O backend (ou Kafka) consolida os dados. O frontend comemora o sucesso (`onSuccess`), dispara o `invalidateQueries` para atualizar os caches no background (Eventual Consistency) e emite um Toast de sucesso.
   - **Falha (4xx/5xx):** A execução cai no `onError`. O erro é formatado, a interface sofre **Rollback** (revertendo o optimistic update para o estado seguro `ctx.prev`) e um Toast de erro é disparado.

### Tratamento de Falhas (Error Handling) e Fallbacks
- Requisições não-sucesso sempre são encapsuladas num `ApiError` formatado. Telas de listas que falham no carregamento primário contam com `ErrorBoundaries` ou _Fallbacks_ graciosos que oferecem a opção "Tentar Novamente".
- Quando há falhas de rede globais ou o token não pode ser validado, o sistema alerta e recua as ações.

---

## 5. Fluxos Visuais: As Quatro Abas (Tabs)

A Home principal (`index.tsx`) divide a aplicação em quatro abas fundamentais. A tabela de listagens compartilha lógicas de paginação e pagina no front-end, fatiando de `10` a `15` itens por vez.

### 5.1. Aba: Demandas
Exibe as **intenções de compra** não finalizadas. Utiliza o componente interno `<DemandasTab />` (passando o prop padrão `isPedido={false}`).
- **Nova Demanda (Dialogs):** Aciona um dialog altamente controlado (aberto/fechado via React State `useState`). Através do `Zod`, o formulário valida as datas de periodicidade apenas se a checkbox "Demanda Recorrente" for marcada (`superRefine`).
- **Filtros e Busca Conjunta:** 
  - *Filtros Locais vs Servidor:* A busca por texto funciona no client-side vasculhando o ID da demanda e buscando no nome do produto vindo do _cache_ na memória.
  - *Filtros de Status:* Componentes UI permitem isolar as exibições (ex: apenas `aberta`, `cancelada`). Esses filtros afetam o array já cacheados localmente, resultando em atualizações visuais em tempo real, sem bater na API.
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
Listagem tradicional em tabela. Um único modal `EnderecoDialog.tsx` atende a criação e a edição, controlado via propriedades React (se prop de `endereco_base` estiver presente, assume edição, preenchendo o React Hook Form; senão, entra vazio como criação).
A deleção logicamente deleta na API (HTTP `204`) e expurga o item dos caches locais via `optimistic update`.

---

## 6. Projeção de Produtos (Integração Indireta)

Como a Equipe 4 (Demandas) depende do cadastro oficial gerido pela Equipe 2 (Catálogo) que comunica pelo Kafka, o frontend **não fará chamadas síncronas HTTP caindo se o serviço da Equipe 2 estiver fora.**
Em vez disso:
- O frontend consome `/api/demandas/produtos/projecao` na nossa própria base (que é mantida populada por *background jobs* no backend ouvindo o Kafka).
- A UI utiliza o componente tolerante a falhas `<ProdutoCell />`.
  - Se a resposta assíncrona estiver carregando, projeta um `Skeleton`.
  - Se o `id_produto` não retornar nada na busca (produto ainda não chegou no cache ou foi excluído), o frontend degrada graciosamente exibindo texto monoespaçado "Produto não identificado" ou "N/D", permitindo uso ininterrupto da plataforma.

---

## 7. Estados de Loading, Refetch e Revalidação

O front-end adota práticas para não deixar a interface travada durante operações e sincronias.

### Experiência de Carregamento (Loading States)
- **Buscas Iniciais:** Sempre que a Query não tem cache (primeira visita), componentes `<Skeleton />` são renderizados para delinear os grids e tabelas, mantendo o layout contínuo.
- **Botões e Ações:** Operações assíncronas (como _submit_ no formulário ou remoção de um item) injetam prop de estado de _loading_ (`isPending` ou `isFetching`) nos botões, muitas vezes desabilitando-os e exibindo ícones de _spinner_.

### Refetch Estratégico (React Query)
O cache (`gcTime` - Garbage Collection) segura os dados na memória caso a aba fique inativa, mas o momento da **revalidação silenciosa** é definido pelo `staleTime`. Evitamos o *polling infinito agressivo* poupando recursos:
- `useDemandas`: Mantém os dados frescos por **4 segundos**.
- `useWishlist`: Mantém os dados frescos por **5 segundos**.
- `useEnderecos`: Mantém os dados frescos por **30 segundos**.

Além do limite de tempo, o hook está configurado para **`refetchOnWindowFocus`**: assim que o comprador muda de aba no navegador e volta ao portal B2B, as requisições que estão *stale* (vencidas) regerem-se automaticamente por baixo dos panos, piscando eventuais atualizações feitas pelo Kafka no banco de dados.

Para revalidação manual sob-demanda, as tabelas também dispõem do botão **"Refresh"** explícito (`<RefreshCw />`) chamando `refetch()`.