import { useQuery } from "@tanstack/react-query";
import { getProdutoProjecao } from "@/services/demandaService";

// Projeção local: lê o cache do serviço de Demanda. Se ainda não foi
// sincronizada via Kafka, retorna null (UI mostra fallback "produto não identificado").
export function useProduto(id: string) {
  return useQuery({
    queryKey: ["produto-projecao", id],
    queryFn: () => getProdutoProjecao(id),
    staleTime: 60_000,
  });
}
