import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  listarWishlist,
  adicionarWishlist,
  converterWishlist,
  type AdicionarWishlistPayload,
} from "@/services/wishlistService";
import type { WishlistItem } from "@/features/types";

const KEY = ["wishlist"] as const;

export function useWishlist() {
  return useQuery({ queryKey: KEY, queryFn: () => listarWishlist(), staleTime: 5000 });
}

export function useAddWishlist() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (p: AdicionarWishlistPayload) =>
      adicionarWishlist(p),
    onSuccess: () => {
      toast.success("Item adicionado à wishlist", { description: "Evento wishlist_item_adicionado publicado." });
      qc.invalidateQueries({ queryKey: KEY });
    },
  });
}

export function useConvertWishlist() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, id_endereco_destino }: { id: string; id_endereco_destino: string }) =>
      converterWishlist(id, id_endereco_destino),
    onSuccess: () => {
      toast.success("Wishlist convertida em demanda", { description: "Evento wishlist_convertida_em_demanda publicado." });
      qc.invalidateQueries({ queryKey: KEY });
      qc.invalidateQueries({ queryKey: ["demandas"] });
    },
  });
}
