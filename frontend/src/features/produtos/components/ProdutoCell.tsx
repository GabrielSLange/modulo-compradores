import { useProduto } from "../hooks/useProduto";
import { Skeleton } from "@/components/ui/skeleton";
import { AlertCircle } from "lucide-react";

// Estratégia de Projeção: 3 estados.
// 1) loading       → Skeleton (cache local sendo lido)
// 2) sincronizado  → mostra nome + categoria
// 3) inexistente   → fallback "Produto não identificado" (evento Kafka ainda não chegou)
export function ProdutoCell({ id }: { id: string }) {
  const { data, isLoading } = useProduto(id);

  if (isLoading) {
    return (
      <div className="space-y-1.5">
        <Skeleton className="h-4 w-40" />
        <Skeleton className="h-3 w-24" />
      </div>
    );
  }

  if (!data || typeof data === "string") {
    return (
      <div className="flex items-start gap-2 text-muted-foreground">
        <AlertCircle className="mt-0.5 size-4 text-warning" />
        <div className="leading-tight">
          <div className="text-sm font-medium text-foreground">
            {typeof data === "string" ? data : "Produto não identificado"}
          </div>
          <div className="text-xs">
            <span className="font-mono">{id}</span> — aguardando sincronização
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="leading-tight">
      <div className="text-sm font-semibold text-foreground">{data.nome}</div>
      <div className="text-xs text-muted-foreground">
        <span className="font-mono">{data.codigo}</span> · {data.categoria} · {data.unidade}
      </div>
    </div>
  );
}
