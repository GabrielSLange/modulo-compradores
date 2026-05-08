import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { DemandaStatus } from "../types";

const map: Record<DemandaStatus, { label: string; cls: string }> = {
  aberta:        { label: "Aberta",         cls: "bg-accent text-accent-foreground border border-primary/20" },
  em_negociacao: { label: "Em negociação",  cls: "bg-warning/15 text-warning border border-warning/30" },
  atendida:      { label: "Atendida",       cls: "bg-success/15 text-success border border-success/30" },
  cancelada:     { label: "Cancelada",      cls: "bg-destructive/15 text-destructive border border-destructive/30" },
};

export function StatusBadge({ status }: { status: DemandaStatus }) {
  const { label, cls } = map[status];
  return <Badge variant="outline" className={cn("rounded-full px-2.5 py-0.5 text-xs font-medium", cls)}>{label}</Badge>;
}
