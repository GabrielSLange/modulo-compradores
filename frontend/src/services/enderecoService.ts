import { api } from "./api";
import type { EnderecoEntrega } from "@/features/types";

// Mock para id da empresa — no futuro virá do contexto/auth
const MOCK_EMPRESA_ID = "empresa-001";

export type CriarEnderecoPayload = Omit<EnderecoEntrega, "id" | "id_empresa" | "data_criacao" | "ativo" | "numero"> & {
  numero?: string;
};

export async function listarEnderecos(): Promise<EnderecoEntrega[]> {
  return await api.get<EnderecoEntrega[]>("/api/demandas/enderecos");
}

export async function criarEndereco(payload: CriarEnderecoPayload): Promise<EnderecoEntrega> {
  const data = { ...payload, id_empresa: MOCK_EMPRESA_ID };
  return await api.post<EnderecoEntrega>("/api/demandas/enderecos", data);
}

export async function atualizarEndereco(id: string, payload: CriarEnderecoPayload): Promise<EnderecoEntrega> {
  const data = { ...payload, id_empresa: MOCK_EMPRESA_ID };
  return await api.put<EnderecoEntrega>(`/api/demandas/enderecos/${id}`, data);
}

export async function excluirEndereco(id: string): Promise<void> {
  return await api.delete(`/api/demandas/enderecos/${id}?id_empresa=${MOCK_EMPRESA_ID}`);
}
