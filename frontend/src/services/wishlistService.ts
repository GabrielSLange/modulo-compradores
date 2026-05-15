import { api } from "./api";
import type { WishlistItem, Demanda } from "@/features/types";

export type AdicionarWishlistPayload = Omit<
  WishlistItem,
  "id" | "id_usuario" | "id_empresa" | "convertido_em_demanda" | "convertida_em_demanda" | "id_demanda_gerada" | "data_criacao" | "atualizado_em"
>;

export async function listarWishlist(): Promise<WishlistItem[]> {
  const items = await api.get<(WishlistItem & { convertido_em_demanda?: boolean })[]>("/api/demandas/wishlist");
  return items.map(normalizeWishlistItem);
}

export async function adicionarWishlist(payload: AdicionarWishlistPayload): Promise<WishlistItem> {
  const item = await api.post<WishlistItem & { convertido_em_demanda?: boolean }>("/api/demandas/wishlist", payload);
  return normalizeWishlistItem(item);
}

export type ConverterWishlistPayload = {
  id_endereco_destino: string;
  quantidade_desejada: number;
  prioridade: "baixa" | "media" | "alta";
};

export async function converterWishlist(id: string, payload: ConverterWishlistPayload): Promise<Demanda> {
  return await api.post<Demanda>(`/api/demandas/wishlist/${id}/converter`, payload);
}

function normalizeWishlistItem(item: WishlistItem & { convertido_em_demanda?: boolean }): WishlistItem {
  return {
    ...item,
    convertida_em_demanda: item.convertida_em_demanda ?? item.convertido_em_demanda ?? false,
  };
}
