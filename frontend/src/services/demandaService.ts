// Serviço do domínio Demanda — chama a API real via Gateway (/api/demanda).
// Cada função tem fallback para o mock em memória, garantindo que a UI
// continue funcional mesmo enquanto o backend não estiver disponível.

import { api, ApiError } from "./api";
import type {
  Demanda,
  DemandaStatus,
  EnderecoEntrega,
  ProdutoProjecao,
  WishlistItem,
} from "@/features/demanda/types";

// ------------------------------------------------------------------ Demandas

export async function listarDemandas(): Promise<Demanda[]> {
  return await api.get<Demanda[]>("/api/demandas");
}

export type CriarDemandaPayload = Omit<
  Demanda,
  "id" | "status" | "criado_em" | "atualizado_em"
>;

export async function criarDemanda(payload: CriarDemandaPayload): Promise<Demanda> {
  return await api.post<Demanda>("/api/demandas", payload);
}

export async function cancelarDemanda(id: string): Promise<Demanda> {
  return await api.patch<Demanda>(`/api/demandas/${id}/cancelar`);
}

export async function atualizarStatus(id: string, status: DemandaStatus): Promise<Demanda> {
  if (status === "cancelada") return cancelarDemanda(id);
  return await api.patch<Demanda>(`/api/demandas/${id}/status`, { status });
}

// ----------------------------------------------------------------- Endereços

export async function listarEnderecos(): Promise<EnderecoEntrega[]> {
  return await api.get<EnderecoEntrega[]>("/api/demandas/enderecos");
}

export type CriarEnderecoPayload = Omit<EnderecoEntrega, "id" | "criado_em" | "ativo" | "numero"> & {
  numero?: string;
};

export async function criarEndereco(payload: CriarEnderecoPayload): Promise<EnderecoEntrega> {
  return await api.post<EnderecoEntrega>("/api/demandas/enderecos", payload);
}

export async function atualizarEndereco(id: string, payload: CriarEnderecoPayload): Promise<EnderecoEntrega> {
  return await api.put<EnderecoEntrega>(`/api/demandas/enderecos/${id}`, payload);
}

export async function excluirEndereco(id: string, id_empresa: string): Promise<void> {
  return await api.delete(`/api/demandas/enderecos/${id}?id_empresa=${id_empresa}`);
}

// ------------------------------------------------------------------ Wishlist

export async function listarWishlist(): Promise<WishlistItem[]> {
  return await api.get<WishlistItem[]>("/api/demandas/wishlist");
}

export async function adicionarWishlist(
  payload: Omit<WishlistItem, "id" | "convertida_em_demanda" | "criado_em">,
): Promise<WishlistItem> {
  return await api.post<WishlistItem>("/api/demandas/wishlist", payload);
}

export async function converterWishlist(
  id: string,
  id_endereco_destino: string,
): Promise<Demanda> {
  return await api.post<Demanda>(`/api/demandas/wishlist/${id}/converter`, {
    id_endereco_destino,
  });
}

// ----------------------------------------- Produtos (projeção via Kafka)

export type Produto = {
  id: string;
  nome: string;
  codigo?: string;
  categoria?: string;
  unidade?: string;
};

export async function getProdutos(): Promise<Produto[]>;
export async function getProdutos(id: string): Promise<Produto>;
export async function getProdutos(id?: string): Promise<Produto | Produto[]> {
  if (id) {
    // Busca um produto específico
    try {
      return await api.get<Produto>(`/api/demandas/produtos/projecao/${id}`);
    } catch (error) {
      console.error(`[Produtos] Falha ao buscar produto com id ${id}`, error);
      // Re-lança o erro para que o chamador (ex: TanStack Query) possa tratá-lo
      throw error;
    }
  } else {
    // Lista todos os produtos
    try {
      return await api.get<Produto[]>("/api/demandas/produtos/projecao");
    } catch (error) {
      console.warn("[Produtos] Falha ao buscar produtos", error);
      return []; // IMPORTANTE: não quebra UI em listagens
    }
  }
}

export async function getProdutoProjecao(id: string): Promise<ProdutoProjecao | string> {
  try {
    return await api.get<ProdutoProjecao>(`/api/demandas/produtos/projecao/${id}`);
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) {
      return "Produto não identificado";
    }
    throw err;
  }
}
