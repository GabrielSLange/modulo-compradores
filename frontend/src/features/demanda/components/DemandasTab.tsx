import { useMemo, useState } from "react";
import { format } from "date-fns";
import { Eye, Search, RefreshCw, Repeat, X } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";

import { useDemandas, useUpdateStatus } from "../hooks/useDemandas";
import { ProdutoCell } from "./ProdutoCell";
import { StatusBadge } from "./StatusBadge";
import { NovaDemandaDialog } from "./NovaDemandaDialog";
import { VisualizarDemandaDialog } from "./VisualizarDemandaDialog";
import type { DemandaStatus } from "../types";

export function DemandasTab() {
  const { data: demandas, isLoading, refetch, isFetching } = useDemandas();
  const updateStatus = useUpdateStatus();
  const [busca, setBusca] = useState("");
  const [statusFilter, setStatusFilter] = useState<"todas" | DemandaStatus>("todas");

  const lista = useMemo(() => {
    return (demandas ?? []).filter((d) => {
      if (statusFilter !== "todas" && d.status !== statusFilter) return false;
      if (busca && !d.id.toLowerCase().includes(busca.toLowerCase())) return false;
      return true;
    });
  }, [demandas, busca, statusFilter]);

  return (
    <section className="space-y-4">
      <header className="flex flex-col gap-3 rounded-lg border border-border bg-card p-5 shadow-[var(--shadow-card)]">
        <div className="flex items-start justify-between gap-3">
          <div>
            <h2 className="text-lg font-semibold text-primary">Demandas</h2>
            <p className="text-sm text-muted-foreground">
              Intenções de compra. Status atualiza automaticamente conforme eventos do <em>Matching Engine</em>.
            </p>
          </div>
          <NovaDemandaDialog />
        </div>
        <div className="flex flex-col gap-2 sm:flex-row">
          <div className="relative flex-1">
            <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              value={busca}
              onChange={(e) => setBusca(e.target.value)}
              placeholder="Buscar por ID..."
              className="pl-9 bg-background"
            />
          </div>
          <Select value={statusFilter} onValueChange={(v) => setStatusFilter(v as typeof statusFilter)}>
            <SelectTrigger className="w-full sm:w-44 bg-background"><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="todas">Todos status</SelectItem>
              <SelectItem value="aberta">Aberta</SelectItem>
              <SelectItem value="em_negociacao">Em negociação</SelectItem>
              <SelectItem value="atendida">Atendida</SelectItem>
              <SelectItem value="cancelada">Cancelada</SelectItem>
            </SelectContent>
          </Select>
          <Button variant="outline" size="icon" onClick={() => refetch()} aria-label="Atualizar">
            <RefreshCw className={isFetching ? "animate-spin" : ""} />
          </Button>
        </div>
      </header>

      <div className="overflow-hidden rounded-lg border border-border bg-card shadow-[var(--shadow-card)]">
        <Table>
          <TableHeader>
            <TableRow className="bg-muted/40 hover:bg-muted/40">
              <TableHead className="text-xs uppercase tracking-wide text-muted-foreground">ID</TableHead>
              <TableHead className="text-xs uppercase tracking-wide text-muted-foreground">Produto</TableHead>
              <TableHead className="text-xs uppercase tracking-wide text-muted-foreground">Qtd.</TableHead>
              <TableHead className="text-xs uppercase tracking-wide text-muted-foreground">Tipo</TableHead>
              <TableHead className="text-xs uppercase tracking-wide text-muted-foreground">Status</TableHead>
              <TableHead className="text-xs uppercase tracking-wide text-muted-foreground">Criado</TableHead>
              <TableHead className="text-right text-xs uppercase tracking-wide text-muted-foreground">Ações</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading
              ? Array.from({ length: 4 }).map((_, i) => (
                  <TableRow key={i}>
                    <TableCell colSpan={7}><Skeleton className="h-10 w-full" /></TableCell>
                  </TableRow>
                ))
              : lista.length === 0
              ? (
                <TableRow>
                  <TableCell colSpan={7} className="py-10 text-center text-sm text-muted-foreground">
                    Nenhuma demanda encontrada.
                  </TableCell>
                </TableRow>
              )
              : lista.map((d) => (
                <TableRow key={d.id} className="hover:bg-accent/40">
                  <TableCell className="font-mono text-xs">{d.id}</TableCell>
                  <TableCell><ProdutoCell id={d.id_produto} /></TableCell>
                  <TableCell className="font-medium">{d.quantidade_desejada}</TableCell>
                  <TableCell>
                    {d.is_recorrente ? (
                      <span className="inline-flex items-center gap-1 rounded-full bg-secondary/15 px-2 py-0.5 text-xs font-medium text-secondary border border-secondary/30">
                        <Repeat className="size-3" /> {d.recorrencia?.frequencia}
                      </span>
                    ) : (
                      <span className="text-xs text-muted-foreground">Única</span>
                    )}
                  </TableCell>
                  <TableCell><StatusBadge status={d.status} /></TableCell>
                  <TableCell className="text-sm text-muted-foreground">
                    {format(new Date(d.criado_em), "dd/MM/yyyy HH:mm")}
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex justify-end gap-1">
                      <VisualizarDemandaDialog demanda={d} />
                      {d.status !== "cancelada" && d.status !== "atendida" && (
                        <Button
                          size="icon"
                          variant="ghost"
                          title="Cancelar"
                          onClick={() => updateStatus.mutate({ id: d.id, status: "cancelada" })}
                          className="text-destructive hover:text-destructive hover:bg-destructive/10"
                        >
                          <X className="size-4" />
                        </Button>
                      )}
                    </div>
                  </TableCell>
                </TableRow>
              ))}
          </TableBody>
        </Table>
      </div>

      <p className="px-1 text-xs text-muted-foreground">
        Exibindo {lista.length} registro(s) · sincronizado a cada 8s (polling de eventos Kafka).
      </p>
    </section>
  );
}
