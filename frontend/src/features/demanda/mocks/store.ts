// Store em memória que simula a API + projeções Kafka enquanto o back não existe.
// Mantém latência artificial para exercitar Skeleton/Optimistic UI.

import type {
  Demanda,
  DemandaStatus,
  EnderecoEntrega,
  ProdutoProjecao,
  WishlistItem,
} from "../types";

const delay = (ms = 450) => new Promise((r) => setTimeout(r, ms));
const uid = () => Math.random().toString(36).slice(2, 10).toUpperCase();
const now = () => new Date().toISOString();

const produtos: ProdutoProjecao[] = [
  { id: "p-1", codigo: "PROD-001", nome: "Notebook Dell Inspiron 15", categoria: "Eletrônicos", unidade: "UN", sincronizado_em: now() },
  { id: "p-2", codigo: "PROD-002", nome: "Notebook Dell g15",         categoria: "Eletrônicos", unidade: "UN", sincronizado_em: now() },
  { id: "p-3", codigo: "PROD-003", nome: "Monitor LG 27\"",           categoria: "Eletrônicos", unidade: "UN", sincronizado_em: now() },
  // p-99 propositalmente NÃO existe — usado para mostrar fallback "produto não sincronizado".
];

const enderecos: EnderecoEntrega[] = [
  {
    id: "e-1", id_empresa: "emp-1", apelido: "Matriz",
    logradouro: "Av. Paulista", numero: "1000", bairro: "Bela Vista",
    cidade: "São Paulo", uf: "SP", cep: "01310-100",
    ativo: true, criado_em: now(),
  },
  {
    id: "e-2", id_empresa: "emp-1", apelido: "CD Campinas",
    logradouro: "Rod. Anhanguera", numero: "Km 95", bairro: "Distrito Industrial",
    cidade: "Campinas", uf: "SP", cep: "13050-000",
    ativo: true, criado_em: now(),
  },
];

const demandas: Demanda[] = [
  {
    id: uid(), id_usuario_criador: "u-1", id_empresa_comprador: "emp-1",
    id_produto: "p-1", id_endereco_entrega: "e-1",
    quantidade: 10, observacao: "Entrega em horário comercial.",
    status: "aberta", is_recorrente: false,
    criado_em: now(), atualizado_em: now(),
  },
  {
    id: uid(), id_usuario_criador: "u-1", id_empresa_comprador: "emp-1",
    id_produto: "p-2", id_endereco_entrega: "e-2",
    quantidade: 4, status: "em_negociacao", is_recorrente: false,
    criado_em: now(), atualizado_em: now(),
  },
  {
    id: uid(), id_usuario_criador: "u-1", id_empresa_comprador: "emp-1",
    id_produto: "p-99", // produto NÃO sincronizado — fallback
    id_endereco_entrega: "e-1",
    quantidade: 25, status: "aberta", is_recorrente: true,
    recorrencia: { frequencia: "mensal", data_inicio: now(), dia_preferencial: 5 },
    criado_em: now(), atualizado_em: now(),
  },
];

const wishlist: WishlistItem[] = [
  {
    id: uid(), id_usuario: "u-1", id_empresa: "emp-1",
    id_produto: "p-3", quantidade_desejada: 2,
    observacao: "Avaliar para o Q2.",
    convertida_em_demanda: false, criado_em: now(),
  },
];

// Simula evolução assíncrona (Matching Engine — Equipe 5).
// A cada chamada de listDemandas, com pequena chance promovemos uma demanda aberta.
function tickStatus() {
  const candidatas = demandas.filter((d) => d.status === "aberta");
  if (candidatas.length && Math.random() < 0.15) {
    const alvo = candidatas[Math.floor(Math.random() * candidatas.length)];
    alvo.status = "em_negociacao";
    alvo.atualizado_em = now();
  }
}

export const mockApi = {
  // ---------- Produtos (projeção) ----------
  async getProduto(id: string): Promise<ProdutoProjecao | null> {
    await delay(120);
    return produtos.find((p) => p.id === id) ?? null;
  },

  // ---------- Endereços ----------
  async listEnderecos(): Promise<EnderecoEntrega[]> {
    await delay();
    return [...enderecos];
  },
  async createEndereco(payload: Omit<EnderecoEntrega, "id" | "criado_em" | "ativo">) {
    await delay();
    const novo: EnderecoEntrega = { ...payload, id: "e-" + uid(), ativo: true, criado_em: now() };
    enderecos.unshift(novo);
    return novo;
  },

  // ---------- Demandas ----------
  async listDemandas(): Promise<Demanda[]> {
    await delay();
    tickStatus();
    return [...demandas].sort((a, b) => b.criado_em.localeCompare(a.criado_em));
  },
  async createDemanda(payload: Omit<Demanda, "id" | "status" | "criado_em" | "atualizado_em">) {
    await delay(700);
    if (Math.random() < 0.05) throw new Error("Falha ao publicar evento demanda_criada.");
    const novo: Demanda = {
      ...payload, id: uid(), status: "aberta",
      criado_em: now(), atualizado_em: now(),
    };
    demandas.unshift(novo);
    return novo;
  },
  async updateStatus(id: string, status: DemandaStatus) {
    await delay(400);
    const d = demandas.find((x) => x.id === id);
    if (!d) throw new Error("Demanda não encontrada.");
    d.status = status; d.atualizado_em = now();
    return d;
  },

  // ---------- Wishlist ----------
  async listWishlist(): Promise<WishlistItem[]> {
    await delay();
    return [...wishlist].sort((a, b) => b.criado_em.localeCompare(a.criado_em));
  },
  async addWishlist(payload: Omit<WishlistItem, "id" | "convertida_em_demanda" | "criado_em">) {
    await delay();
    const novo: WishlistItem = {
      ...payload, id: uid(), convertida_em_demanda: false, criado_em: now(),
    };
    wishlist.unshift(novo);
    return novo;
  },
  async convertWishlist(id: string, id_endereco_entrega: string): Promise<Demanda> {
    await delay(600);
    const w = wishlist.find((x) => x.id === id);
    if (!w) throw new Error("Item de wishlist não encontrado.");
    const d = await this.createDemanda({
      id_usuario_criador: w.id_usuario,
      id_empresa_comprador: w.id_empresa,
      id_produto: w.id_produto,
      id_endereco_entrega,
      quantidade: w.quantidade_desejada,
      observacao: w.observacao,
      is_recorrente: false,
    });
    w.convertida_em_demanda = true;
    w.id_demanda_gerada = d.id;
    return d;
  },
};

export const mockProdutosCatalog = produtos;
