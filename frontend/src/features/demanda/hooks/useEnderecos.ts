import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { mockApi } from "../mocks/store";

const KEY = ["enderecos"] as const;

export function useEnderecos() {
  return useQuery({ queryKey: KEY, queryFn: () => mockApi.listEnderecos(), staleTime: 30_000 });
}

export function useCreateEndereco() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (p: Parameters<typeof mockApi.createEndereco>[0]) => mockApi.createEndereco(p),
    onSuccess: () => {
      toast.success("Endereço cadastrado");
      qc.invalidateQueries({ queryKey: KEY });
    },
  });
}
