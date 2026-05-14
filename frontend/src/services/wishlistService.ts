import { api } from "./api";
import type { WishlistItem, Demanda } from "@/features/types";

// IDs fixos idênticos ao seed.py do backend
const MOCK_USUARIO_ID = "550e8400-e29b-41d4-a716-446655440000";
const MOCK_EMPRESA_ID = "f47ac10b-58cc-4372-a567-0e02b2c3d479";

export type AdicionarWishlistPayload = Omit<
  WishlistItem,
  "id" | "id_usuario" | "id_empresa" | "convertido_em_demanda" | "convertida_em_demanda" | "id_demanda_gerada" | "data_criacao" | "atualizado_em"
>;

export async function listarWishlist(): Promise<WishlistItem[]> {
  return await api.get<WishlistItem[]>("/api/demandas/wishlist");
}

export async function adicionarWishlist(payload: AdicionarWishlistPayload): Promise<WishlistItem> {
  const data = { ...payload, id_usuario: MOCK_USUARIO_ID, id_empresa: MOCK_EMPRESA_ID };
  return await api.post<WishlistItem>("/api/demandas/wishlist", data);
}

export type ConverterWishlistPayload = {
  id_endereco_destino: string;
  quantidade_desejada: number;
  prioridade: "baixa" | "media" | "alta";
};

export async function converterWishlist(id: string, payload: ConverterWishlistPayload): Promise<Demanda> {
  return await api.post<Demanda>(`/api/demandas/wishlist/${id}/converter?id_usuario=${MOCK_USUARIO_ID}`, payload);
}