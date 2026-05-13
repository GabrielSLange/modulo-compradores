import { format } from "date-fns";
import { Eye, MapPin, Repeat } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger,
} from "@/components/ui/dialog";

import type { Demanda } from "@/features/types";
import { ProdutoCell } from "@/features/produtos/components/ProdutoCell";
import { StatusBadge } from "./StatusBadge";
import { useEnderecos } from "@/features/enderecos/hooks/useEnderecos";

interface Props {
  demanda: Demanda;
}

export function VisualizarDemandaDialog({ demanda }: Props) {
  const { data: enderecos } = useEnderecos();
  const endereco = enderecos?.find((e) => e.id === demanda.id_endereco_entrega);

  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button size="icon" variant="ghost" title="Detalhes"><Eye className="size-4" /></Button>
      </DialogTrigger>
      <DialogContent className="max-w-xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            Demanda <span className="font-mono text-sm text-muted-foreground">{demanda.id}</span>
            <StatusBadge status={demanda.status} />
          </DialogTitle>
          <DialogDescription>
            Criada em {format(new Date(demanda.data_criacao), "dd/MM/yyyy 'às' HH:mm")}
          </DialogDescription>
        </DialogHeader>

        <div className="grid grid-cols-2 gap-4 mt-2">
          <div className="col-span-2 space-y-1">
            <span className="text-xs font-semibold uppercase text-muted-foreground">Produto</span>
            <div className="rounded-md border bg-muted/40 p-3">
              <ProdutoCell id={demanda.id_produto} />
            </div>
          </div>

          <div className="space-y-1">
            <span className="text-xs font-semibold uppercase text-muted-foreground">Quantidade Desejada</span>
            <div className="font-medium text-lg">{demanda.quantidade_desejada}</div>
          </div>

          <div className="space-y-1">
            <span className="text-xs font-semibold uppercase text-muted-foreground">Preço Máximo</span>
            <div className="font-medium">
              {demanda.preco_maximo ? `R$ ${demanda.preco_maximo.toFixed(2)}` : "Não definido"}
            </div>
          </div>

          <div className="space-y-1">
            <span className="text-xs font-semibold uppercase text-muted-foreground">Prioridade</span>
            <div className="capitalize font-medium">{demanda.prioridade}</div>
          </div>

          <div className="space-y-1">
            <span className="text-xs font-semibold uppercase text-muted-foreground">Recorrência</span>
            <div>
              {demanda.is_recorrente ? (
                <span className="inline-flex items-center gap-1 rounded-full bg-secondary/15 px-2 py-0.5 text-xs font-medium text-secondary border border-secondary/30">
                  <Repeat className="size-3" /> {demanda.recorrencia?.frequencia}
                </span>
              ) : (
                <span className="text-sm text-muted-foreground">Única</span>
              )}
            </div>
          </div>

          <div className="col-span-2 space-y-1">
            <span className="text-xs font-semibold uppercase text-muted-foreground">Endereço de Destino</span>
            <div className="rounded-md border bg-muted/40 p-3 flex flex-col gap-1">
              {endereco ? (
                <>
                  <span className="font-medium inline-flex items-center gap-1">
                    <MapPin className="size-3" /> {endereco.apelido}
                  </span>
                  <span className="text-sm text-muted-foreground">
                    {endereco.logradouro}, {endereco.numero} {endereco.complemento ? `— ${endereco.complemento}` : ""}
                  </span>
                  <span className="text-sm text-muted-foreground">
                    {endereco.cidade}/{endereco.uf} — CEP {endereco.cep}
                  </span>
                </>
              ) : (
                <span className="text-sm text-muted-foreground">ID: {demanda.id_endereco_entrega} (Não encontrado)</span>
              )}
            </div>
          </div>

          {demanda.observacao && (
            <div className="col-span-2 space-y-1">
              <span className="text-xs font-semibold uppercase text-muted-foreground">Observações</span>
              <div className="rounded-md border bg-muted/40 p-3 text-sm">
                {demanda.observacao}
              </div>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
