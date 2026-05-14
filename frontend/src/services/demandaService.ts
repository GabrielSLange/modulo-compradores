import { api } from "./api";
import type { Demanda, DemandaStatus } from "@/features/types";

// IDs fixos idênticos ao seed.py do backend
const MOCK_USUARIO_ID = "550e8400-e29b-41d4-a716-446655440000";
const MOCK_EMPRESA_ID = "f47ac10b-58cc-4372-a567-0e02b2c3d479";

export async function listarDemandas(): Promise<Demanda[]> {
  return await api.get<Demanda[]>("/api/demandas");
}

export type CriarDemandaPayload = Omit<
  Demanda,
  "id" | "id_usuario_criador" | "id_empresa_comprador" | "status" | "data_criacao" | "atualizado_em"
>;

export async function criarDemanda(payload: CriarDemandaPayload): Promise<Demanda> {
  // Mapeia o id_endereco_entrega do front para id_endereco_destino que a base/DTO deve esperar
  const { id_endereco_entrega, ...rest } = payload as any;
  const data = {
    ...rest,
    id_endereco_destino: id_endereco_entrega || payload.id_endereco_entrega,
    id_usuario_criador: MOCK_USUARIO_ID,
    id_empresa_comprador: MOCK_EMPRESA_ID,
  };
  return await api.post<Demanda>("/api/demandas", data);
}

export async function cancelarDemanda(id: string): Promise<Demanda> {
  return await api.patch<Demanda>(`/api/demandas/${id}/cancelar`);
}

export async function atualizarStatus(id: string, status: DemandaStatus): Promise<Demanda> {
  if (status === "cancelada") return cancelarDemanda(id);
  return await api.patch<Demanda>(`/api/demandas/${id}/status`, { status });
}