import { api } from "./api";
import type { Demanda, DemandaStatus } from "@/features/types";

const MOCK_USUARIO_ID = "usuario-001";
const MOCK_EMPRESA_ID = "empresa-001";

export async function listarDemandas(): Promise<Demanda[]> {
  return await api.get<Demanda[]>("/api/demandas");
}

export type CriarDemandaPayload = Omit<
  Demanda,
  "id" | "id_usuario_criador" | "id_empresa_comprador" | "status" | "criado_em" | "atualizado_em"
>;

export async function criarDemanda(payload: CriarDemandaPayload): Promise<Demanda> {
  const { id_endereco_entrega, ...rest } = payload;
  const data = {
    ...rest,
    id_endereco_destino: id_endereco_entrega, // backend usa id_endereco_destino
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
