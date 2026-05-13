import { api } from "./api";
import type { WishlistItem, Demanda } from "@/features/types";

const MOCK_USUARIO_ID = "usuario-001";
const MOCK_EMPRESA_ID = "empresa-001";

export type AdicionarWishlistPayload = Omit<WishlistItem, "id" | "id_usuario" | "id_empresa" | "convertida_em_demanda" | "data_criacao">;

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
