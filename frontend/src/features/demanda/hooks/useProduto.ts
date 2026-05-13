import { useQuery } from "@tanstack/react-query";
import { getProdutos } from "@/services/demandaService";
import type { Produto } from "@/services/demandaService";

/**
 * Hook para buscar a LISTA COMPLETA de produtos.
 * Ideal para popular selects e comboboxes.
 */
export function useProdutos() {
  return useQuery<Produto[]>({
    // A chave "produtos" é usada para cachear a lista completa.
    queryKey: ["produtos"],
    // Chama a nova função getProdutos SEM passar um ID.
    queryFn: getProdutos,
    // Opcional: produtos não mudam com frequência, então podemos
    // manter os dados em cache por mais tempo (ex: 5 minutos).
    staleTime: 1000 * 60 * 5,
  });
}

/**
 * Hook para buscar UM ÚNICO produto pelo seu ID.
 * @param id O ID do produto a ser buscado.
 */
export function useProduto(id: string | undefined) {
  return useQuery<Produto>({
    queryKey: ["produtos", id],
    queryFn: () => getProdutos(id!),
    enabled: !!id,
  });
}
