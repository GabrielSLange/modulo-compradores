import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  listarEnderecos,
  criarEndereco,
  atualizarEndereco,
  excluirEndereco,
  type CriarEnderecoPayload,
} from "@/services/enderecoService";
import type { EnderecoEntrega } from "@/features/types";

const KEY = ["enderecos"] as const;

export function useEnderecos() {
  return useQuery({ queryKey: KEY, queryFn: () => listarEnderecos(), staleTime: 30_000 });
}

export function useCreateEndereco() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (p: CriarEnderecoPayload) => criarEndereco(p),
    onSuccess: () => {
      toast.success("Endereço cadastrado");
      qc.invalidateQueries({ queryKey: KEY });
    },
  });
}

export function useUpdateEndereco() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: CriarEnderecoPayload }) =>
      atualizarEndereco(id, payload),
    onSuccess: () => {
      toast.success("Endereço atualizado");
      qc.invalidateQueries({ queryKey: KEY });
    },
    onError: (err) => {
      toast.error("Falha ao atualizar endereço", { description: (err as Error).message });
    },
  });
}

export function useDeleteEndereco() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => excluirEndereco(id),
    onSuccess: () => {
      toast.success("Endereço excluído");
      qc.invalidateQueries({ queryKey: KEY });
    },
    onError: (err) => {
      toast.error("Falha ao excluir endereço", { description: (err as Error).message });
    },
  });
}
