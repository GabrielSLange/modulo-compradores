import { useQuery } from "@tanstack/react-query";
import { mockApi } from "../mocks/store";

// Projeção local: lê o cache do serviço de Demanda. Se ainda não foi
// sincronizada via Kafka, retorna null (UI mostra fallback).
export function useProduto(id: string) {
  return useQuery({
    queryKey: ["produto-projecao", id],
    queryFn: () => mockApi.getProduto(id),
    staleTime: 60_000,
  });
}
