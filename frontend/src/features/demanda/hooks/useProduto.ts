import { useQuery } from "@tanstack/react-query";
import { getProdutoProjecao, listarProdutos } from "@/services/demandaService";

/**
 * Hook para buscar a lista de projeções de produtos.
 * Ideal para popular selects e comboboxes.
 */
export function useProdutos() {
  return useQuery({
    queryKey: ["produtos"],
    queryFn: listarProdutos,
    staleTime: 1000 * 60 * 5,
  });
}

// Projeção local: lê o cache do serviço de Demanda. Se ainda não foi
// sincronizada via Kafka, retorna null (UI mostra fallback "produto não identificado").
export function useProduto(id: string) {
  return useQuery({
    queryKey: ["produto-projecao", id],
    queryFn: () => getProdutoProjecao(id),
    staleTime: 60_000,
  });
}
