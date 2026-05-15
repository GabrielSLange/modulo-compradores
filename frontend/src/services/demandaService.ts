import { api } from "./api";
import type { Demanda, DemandaStatus } from "@/features/types";

export async function listarDemandas(): Promise<Demanda[]> {
  return await api.get<Demanda[]>("/api/demandas/");
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
    id_endereco_destino: id_endereco_entrega || (payload as any).id_endereco_destino,
  };
  return await api.post<Demanda>("/api/demandas/", data);
}

export async function cancelarDemanda(id: string): Promise<Demanda> {
  return await api.patch<Demanda>(`/api/demandas/${id}/cancelar`);
}

export async function atualizarStatus(id: string, status: DemandaStatus): Promise<Demanda> {
  if (status === "cancelada") return cancelarDemanda(id);
  return await api.patch<Demanda>(`/api/demandas/${id}/status`, { status });
}
