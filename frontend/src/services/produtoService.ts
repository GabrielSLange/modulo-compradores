import { api } from "./api";
import type { ProdutoProjecao } from "@/features/types";

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
    try {
      return await api.get<Produto>(`/api/demandas/produtos/projecao/${id}`);
    } catch (error) {
      console.error(`[Produtos] Falha ao buscar produto com id ${id}`, error);
      throw error;
    }
  } else {
    try {
      return await api.get<Produto[]>("/api/demandas/produtos/projecao");
    } catch (error) {
      console.warn("[Produtos] Falha ao buscar produtos", error);
      return [];
    }
  }
}
