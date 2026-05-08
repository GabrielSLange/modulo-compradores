import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { mockApi } from "../mocks/store";

const KEY = ["wishlist"] as const;

export function useWishlist() {
  return useQuery({ queryKey: KEY, queryFn: () => mockApi.listWishlist(), staleTime: 5000 });
}

export function useAddWishlist() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (p: Parameters<typeof mockApi.addWishlist>[0]) => mockApi.addWishlist(p),
    onSuccess: () => {
      toast.success("Item adicionado à wishlist", { description: "Evento wishlist_item_adicionado publicado." });
      qc.invalidateQueries({ queryKey: KEY });
    },
  });
}

export function useConvertWishlist() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, id_endereco_entrega }: { id: string; id_endereco_entrega: string }) =>
      mockApi.convertWishlist(id, id_endereco_entrega),
    onSuccess: () => {
      toast.success("Wishlist convertida em demanda", { description: "Evento wishlist_convertida_em_demanda publicado." });
      qc.invalidateQueries({ queryKey: KEY });
      qc.invalidateQueries({ queryKey: ["demandas"] });
    },
  });
}
