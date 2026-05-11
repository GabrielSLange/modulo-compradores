// Serviço do domínio Demanda — chama a API real via Gateway (/api/demanda).
// Cada função tem fallback para o mock em memória, garantindo que a UI
// continue funcional mesmo enquanto o backend não estiver disponível.

import { api, ApiError } from "./api";
import { mockApi } from "@/features/demanda/mocks/store";
import type {
  Demanda,
  DemandaStatus,
  EnderecoEntrega,
  ProdutoProjecao,
  WishlistItem,
} from "@/features/demanda/types";

/** Loga o motivo do fallback sem poluir a UI. */
function warnFallback(scope: string, err: unknown) {
  const msg = err instanceof ApiError ? `${err.status} ${err.message}` : (err as Error)?.message;
  // eslint-disable-next-line no-console
  console.warn(`[demandaService] ${scope}: usando mock (motivo: ${msg})`);
}

// ------------------------------------------------------------------ Demandas

export async function listarDemandas(): Promise<Demanda[]> {
  try {
    return await api.get<Demanda[]>("/api/demanda");
  } catch (err) {
    warnFallback("listarDemandas", err);
    return mockApi.listDemandas();
  }
}

export type CriarDemandaPayload = Omit<
  Demanda,
  "id" | "status" | "criado_em" | "atualizado_em"
>;

export async function criarDemanda(payload: CriarDemandaPayload): Promise<Demanda> {
  try {
    return await api.post<Demanda>("/api/demanda", payload);
  } catch (err) {
    warnFallback("criarDemanda", err);
    return mockApi.createDemanda(payload);
  }
}

export async function cancelarDemanda(id: string): Promise<Demanda> {
  try {
    return await api.patch<Demanda>(`/api/demanda/${id}/cancelar`);
  } catch (err) {
    warnFallback("cancelarDemanda", err);
    return mockApi.updateStatus(id, "cancelada");
  }
}

export async function atualizarStatus(id: string, status: DemandaStatus): Promise<Demanda> {
  if (status === "cancelada") return cancelarDemanda(id);
  try {
    return await api.patch<Demanda>(`/api/demanda/${id}/status`, { status });
  } catch (err) {
    warnFallback("atualizarStatus", err);
    return mockApi.updateStatus(id, status);
  }
}

// ----------------------------------------------------------------- Endereços

export async function listarEnderecos(): Promise<EnderecoEntrega[]> {
  try {
    return await api.get<EnderecoEntrega[]>("/api/demanda/enderecos");
  } catch (err) {
    warnFallback("listarEnderecos", err);
    return mockApi.listEnderecos();
  }
}

export async function criarEndereco(
  payload: Omit<EnderecoEntrega, "id" | "criado_em" | "ativo">,
): Promise<EnderecoEntrega> {
  try {
    return await api.post<EnderecoEntrega>("/api/demanda/enderecos", payload);
  } catch (err) {
    warnFallback("criarEndereco", err);
    return mockApi.createEndereco(payload);
  }
}

// ------------------------------------------------------------------ Wishlist

export async function listarWishlist(): Promise<WishlistItem[]> {
  try {
    return await api.get<WishlistItem[]>("/api/demanda/wishlist");
  } catch (err) {
    warnFallback("listarWishlist", err);
    return mockApi.listWishlist();
  }
}

export async function adicionarWishlist(
  payload: Omit<WishlistItem, "id" | "convertida_em_demanda" | "criado_em">,
): Promise<WishlistItem> {
  try {
    return await api.post<WishlistItem>("/api/demanda/wishlist", payload);
  } catch (err) {
    warnFallback("adicionarWishlist", err);
    return mockApi.addWishlist(payload);
  }
}

export async function converterWishlist(
  id: string,
  id_endereco_entrega: string,
): Promise<Demanda> {
  try {
    return await api.post<Demanda>(`/api/demanda/wishlist/${id}/converter`, {
      id_endereco_entrega,
    });
  } catch (err) {
    warnFallback("converterWishlist", err);
    return mockApi.convertWishlist(id, id_endereco_entrega);
  }
}

// ----------------------------------------- Produtos (projeção via Kafka)

export async function getProdutoProjecao(id: string): Promise<ProdutoProjecao | null> {
  try {
    return await api.get<ProdutoProjecao>(`/api/produtos/projecao/${id}`);
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) return null;
    warnFallback("getProdutoProjecao", err);
    return mockApi.getProduto(id);
  }
}
