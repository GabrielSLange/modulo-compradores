import { api } from "./api";
import type { WishlistItem, Demanda } from "@/features/types";

const MOCK_USUARIO_ID = "u-1";
const MOCK_EMPRESA_ID = "emp-1";

export type AdicionarWishlistPayload = Omit<WishlistItem, "id" | "id_usuario" | "id_empresa" | "convertida_em_demanda" | "criado_em">;

export async function listarWishlist(): Promise<WishlistItem[]> {
  return await api.get<WishlistItem[]>("/api/demandas/wishlist");
}

export async function adicionarWishlist(payload: AdicionarWishlistPayload): Promise<WishlistItem> {
  const data = { ...payload, id_usuario: MOCK_USUARIO_ID, id_empresa: MOCK_EMPRESA_ID };
  return await api.post<WishlistItem>("/api/demandas/wishlist", data);
}

export async function converterWishlist(id: string, id_endereco_destino: string): Promise<Demanda> {
  return await api.post<Demanda>(`/api/demandas/wishlist/${id}/converter`, {
    id_endereco_destino,
  });
}
