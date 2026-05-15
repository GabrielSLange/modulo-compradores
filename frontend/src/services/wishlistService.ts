import { api } from "./api";
import type { WishlistItem, Demanda } from "@/features/types";

export type AdicionarWishlistPayload = Omit<
  WishlistItem,
  "id" | "id_usuario" | "id_empresa" | "convertido_em_demanda" | "convertida_em_demanda" | "id_demanda_gerada" | "data_criacao" | "atualizado_em"
>;

export async function listarWishlist(): Promise<WishlistItem[]> {
  return await api.get<WishlistItem[]>("/api/demandas/wishlist");
}

export async function adicionarWishlist(payload: AdicionarWishlistPayload): Promise<WishlistItem> {
  return await api.post<WishlistItem>("/api/demandas/wishlist", payload);
}

export type ConverterWishlistPayload = {
  id_endereco_destino: string;
  quantidade_desejada: number;
  prioridade: "baixa" | "media" | "alta";
};

export async function converterWishlist(id: string, payload: ConverterWishlistPayload): Promise<Demanda> {
  return await api.post<Demanda>(`/api/demandas/wishlist/${id}/converter`, payload);
}