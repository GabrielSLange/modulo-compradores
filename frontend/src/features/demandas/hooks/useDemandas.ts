import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  listarDemandas,
  criarDemanda,
  cancelarDemanda,
  atualizarStatus,
  type CriarDemandaPayload,
} from "@/services/demandaService";
import type { Demanda, DemandaStatus } from "@/features/types";

const KEY = ["demandas"] as const;

// refetchInterval simula a reatividade dos eventos Kafka enquanto o WS não existe.
export function useDemandas() {
  return useQuery({
    queryKey: KEY,
    queryFn: () => listarDemandas(),
    refetchInterval: 8000,
    staleTime: 4000,
  });
}

export function useCreateDemanda() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: CriarDemandaPayload) => criarDemanda(payload),
    // Optimistic UI: insere a demanda imediatamente; rollback se a API falhar.
    onMutate: async (payload) => {
      await qc.cancelQueries({ queryKey: KEY });
      const prev = qc.getQueryData<Demanda[]>(KEY) ?? [];
      const optimistic: Demanda = {
        ...payload,
        id_usuario_criador: "u-1",
        id_empresa_comprador: "emp-1",
        id: "tmp-" + Math.random().toString(36).slice(2, 8),
        status: "aberta",
        data_criacao: new Date().toISOString(),
        atualizado_em: new Date().toISOString(),
      };
      qc.setQueryData<Demanda[]>(KEY, [optimistic, ...prev]);
      return { prev };
    },
    onError: (err, _vars, ctx) => {
      if (ctx?.prev) qc.setQueryData(KEY, ctx.prev);
      toast.error("Não foi possível criar a demanda", { description: (err as Error).message });
    },
    onSuccess: () => toast.success("Demanda criada", { description: "Evento demanda_criada publicado." }),
    onSettled: () => qc.invalidateQueries({ queryKey: KEY }),
  });
}

export function useUpdateStatus() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, status }: { id: string; status: DemandaStatus }) =>
      status === "cancelada" ? cancelarDemanda(id) : atualizarStatus(id, status),
    onMutate: async ({ id, status }) => {
      await qc.cancelQueries({ queryKey: KEY });
      const prev = qc.getQueryData<Demanda[]>(KEY) ?? [];
      qc.setQueryData<Demanda[]>(
        KEY,
        prev.map((d) => (d.id === id ? { ...d, status } : d)),
      );
      return { prev };
    },
    onError: (err, _v, ctx) => {
      if (ctx?.prev) qc.setQueryData(KEY, ctx.prev);
      toast.error("Falha ao atualizar status", { description: (err as Error).message });
    },
    onSuccess: (_d, v) => {
      if (v.status === "cancelada") toast.success("Demanda cancelada", { description: "Evento demanda_cancelada publicado." });
    },
    onSettled: () => qc.invalidateQueries({ queryKey: KEY }),
  });
}
