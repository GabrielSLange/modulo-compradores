import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { listarEnderecos, criarEndereco, type CriarEnderecoPayload } from "@/services/demandaService";
import type { EnderecoEntrega } from "../types";

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
