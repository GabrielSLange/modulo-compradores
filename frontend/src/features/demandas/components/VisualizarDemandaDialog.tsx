import { format } from "date-fns";
import { Eye, MapPin, Repeat, Loader2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger,
} from "@/components/ui/dialog";

import type { Demanda } from "@/features/types";
import { ProdutoCell } from "@/features/produtos/components/ProdutoCell";
import { StatusBadge } from "./StatusBadge";
import { useEnderecos } from "@/features/enderecos/hooks/useEnderecos";
import { useCotacoes, useContratarFrete } from "../hooks/useDemandas";

function ListarESelecionarFrete({ idDemanda }: { idDemanda: string }) {
  const { data: cotacoes, isLoading, isError } = useCotacoes(idDemanda, true);
  const contratar = useContratarFrete();

  if (isLoading) return <div className="text-sm text-muted-foreground flex items-center gap-2"><Loader2 className="animate-spin size-4" /> Buscando cotações de frete...</div>;
  if (isError) return <div className="text-sm text-destructive">Erro ao buscar cotações.</div>;
  if (!cotacoes || cotacoes.length === 0) return <div className="text-sm text-muted-foreground">Nenhuma cotação disponível no momento.</div>;

  return (
    <div className="space-y-2 mt-2">
      {cotacoes.map((c: any) => (
        <div key={c.id} className="p-3 border rounded-lg flex justify-between items-center bg-background">
          <div>
            <span className="block font-medium text-sm">{c.transportadora_nome || c.id_transportadora || "Transportadora " + c.id}</span>
            <span className="text-xs text-muted-foreground">Prazo: {c.prazo_dias || c.prazo} dias</span>
          </div>
          <div className="flex items-center gap-3">
            <span className="font-semibold text-primary">R$ {c.valor?.toFixed(2)}</span>
            <Button 
              size="sm" 
              onClick={() => contratar.mutate({ id_demanda: idDemanda, cotacao_id: c.id })}
              disabled={contratar.isPending}
            >
              {contratar.isPending ? "Contratando..." : "Contratar"}
            </Button>
          </div>
        </div>
      ))}
    </div>
  );
}

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

          {demanda.is_pedido && (
            <div className="col-span-2 border-t pt-4 mt-2 space-y-4">
              <h3 className="font-semibold text-sm uppercase tracking-wider text-primary">
                Detalhes do Pedido & Logística
              </h3>
              
              <div className="grid grid-cols-2 gap-4 bg-muted/20 p-3 rounded-lg border">
                <div>
                  <span className="text-xs text-muted-foreground block">Fornecedor Vencedor</span>
                  <span className="font-medium">{demanda.id_fornecedor || "N/A"}</span>
                </div>
                <div>
                  <span className="text-xs text-muted-foreground block">Modal de Transporte</span>
                  <span className="font-medium capitalize">{demanda.tipo_transporte?.toLowerCase() || "N/A"}</span>
                </div>
                <div>
                  <span className="text-xs text-muted-foreground block">Preço Final Unitário</span>
                  <span className="font-medium text-green-600">R$ {demanda.preco_final?.toFixed(2) || "0.00"}</span>
                </div>
                <div>
                  <span className="text-xs text-muted-foreground block">Total dos Produtos</span>
                  <span className="font-medium text-green-600">R$ {demanda.valor_total?.toFixed(2) || "0.00"}</span>
                </div>
                <div>
                  <span className="text-xs text-muted-foreground block">Peso da Carga</span>
                  <span className="font-medium">{demanda.peso_carga || 0} kg</span>
                </div>
                <div className="col-span-2 border-t pt-2 mt-1">
                  <span className="text-xs text-muted-foreground block">Rota de Envio</span>
                  <span className="text-sm font-medium">
                    CEP {demanda.cep_origem || "N/A"} (Fornecedor) &rarr; CEP {demanda.cep_destino || "N/A"} (Você)
                  </span>
                </div>
              </div>

              {/* Seção de Contratação / Exibição de Cotações */}
              <div className="space-y-2">
                <span className="text-xs font-semibold uppercase text-muted-foreground block">
                  Status do Frete: <span className="text-primary font-bold">{demanda.status_frete || "PENDENTE"}</span>
                </span>

                {/* Caso o frete já tenha sido contratado */}
                {demanda.id_frete_selecionado ? (
                  <div className="p-3 bg-blue-50/50 text-blue-900 border border-blue-200/50 rounded-lg text-sm flex justify-between items-center">
                    <div>
                      <span className="block text-xs text-blue-700">Frete Contratado</span>
                      <span className="font-semibold">Valor: R$ {demanda.valor_frete?.toFixed(2) || "0.00"}</span>
                    </div>
                    <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded font-semibold text-xs uppercase tracking-wider">
                      {demanda.status_frete || "SELECIONADO"}
                    </span>
                  </div>
                ) : (
                  /* Caso precise contratar */
                  <ListarESelecionarFrete idDemanda={demanda.id} />
                )}
              </div>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
