import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  listarDemandas,
  criarDemanda,
  cancelarDemanda,
  atualizarStatus,

  listarCotacoes,
  contratarFrete,
  type CriarDemandaPayload,
} from "@/services/demandaService";
import type { Demanda, DemandaStatus } from "@/features/types";
import { ApiError } from "@/services/api";

const KEY = ["demandas"] as const;

export function useDemandas() {
  return useQuery({
    queryKey: KEY,
    queryFn: () => listarDemandas(),
    staleTime: 4000,
    // Polling inteligente: faz refetch a cada 5 segundos apenas se houver
    // algum pedido ativo que possui frete e ainda não foi entregue ou cancelado.
    refetchInterval: (query) => {
      const demandas = query.state.data;
      const temFreteAtivo = demandas?.some(
        (d) =>
          d.is_pedido &&
          d.status_frete &&
          !["ENTREGUE", "CANCELADA", "PENDENTE"].includes(d.status_frete.toUpperCase())
      );
      return temFreteAtivo ? 5000 : false;
    },
  });
}

export function useCreateDemanda() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: CriarDemandaPayload) => {
      return await criarDemanda(payload);
    },
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
        is_pedido: false,
        data_criacao: new Date().toISOString(),
        atualizado_em: new Date().toISOString(),
      };
      qc.setQueryData<Demanda[]>(KEY, [optimistic, ...prev]);
      return { prev };
    },
    onError: (err, _vars, ctx) => {
      if (ctx?.prev) qc.setQueryData(KEY, ctx.prev);
      if (err instanceof ApiError && err.status === 422) {
        toast.error("Estoque insuficiente", {
          description: "Não foi possível converter esta demanda em pedido pois nenhum fornecedor possui estoque suficiente no momento. A demanda permanece aberta.",
        });
      } else {
        toast.error("Não foi possível criar a demanda", { description: (err as Error).message });
      }
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

export function useCotacoes(id_demanda: string, enabled = true) {
  return useQuery({
    queryKey: ["cotacoes", id_demanda],
    queryFn: () => listarCotacoes(id_demanda),
    enabled: !!id_demanda && enabled,
    staleTime: 1000 * 60 * 5, // 5 minutos
  });
}

export function useContratarFrete() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id_demanda, cotacao_id }: { id_demanda: string; cotacao_id: string }) =>
      contratarFrete(id_demanda, cotacao_id),
    onSuccess: (data, variables) => {
      toast.success("Frete contratado com sucesso!");
      qc.setQueryData<Demanda[]>(KEY, (old) => {
        if (!old) return old;
        return old.map((d) => (d.id === variables.id_demanda ? data : d));
      });
      qc.invalidateQueries({ queryKey: KEY });
    },
    onError: (err) => {
      toast.error("Erro ao contratar frete", { description: (err as Error).message });
    },
  });
}