import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { Plus } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import {
  Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger,
} from "@/components/ui/dialog";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";

import { useCreateDemanda } from "../hooks/useDemandas";
import { useEnderecos } from "../hooks/useEnderecos";
import { useProdutos } from "../hooks/useProduto"; // Importa o hook correto para listar produtos
import type { RecorrenciaFrequencia } from "../types";

// Validação dinâmica: quando is_recorrente=true, recorrencia.* vira obrigatório.
const schema = z
  .object({
    id_produto: z.string().min(1, "Selecione um produto"),
    id_endereco_destino: z.string().min(1, "Selecione um endereço"),
    quantidade_desejada: z.coerce.number().int().positive("Mín. 1"),
    prioridade: z.enum(["baixa", "media", "alta"]),
    preco_maximo: z.coerce.number().optional(),
    observacao: z.string().optional(),
    is_recorrente: z.boolean(),
    frequencia: z.enum(["diaria", "semanal", "mensal"]).optional(),
    data_inicio: z.string().optional(),
    data_fim: z.string().optional(),
    dia_preferencial: z.coerce.number().int().min(1).max(31).optional(),
  })
  .superRefine((v, ctx) => {
    if (!v.is_recorrente) return;
    if (!v.frequencia) ctx.addIssue({ code: "custom", path: ["frequencia"], message: "Obrigatório" });
    if (!v.data_inicio) ctx.addIssue({ code: "custom", path: ["data_inicio"], message: "Obrigatório" });
    if (!v.dia_preferencial) ctx.addIssue({ code: "custom", path: ["dia_preferencial"], message: "Obrigatório" });
  });

type FormValues = z.infer<typeof schema>;

export function NovaDemandaDialog() {
  const [open, setOpen] = useState(false);
  const { data: enderecos, isLoading: isLoadingEnderecos, isError: isErrorEnderecos } = useEnderecos();
  const { data: produtos, isLoading: isLoadingProdutos, isError: isErrorProdutos } = useProdutos(); // Usa useProdutos
  const create = useCreateDemanda();

  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { is_recorrente: false, quantidade_desejada: 1, prioridade: "media" },
  });

  const isRec = form.watch("is_recorrente");

  const onSubmit = form.handleSubmit((v) => {
    create.mutate({
      id_usuario_criador: "u-1",          // mock JWT
      id_empresa_comprador: "emp-1",      // mock JWT
      id_produto: v.id_produto,
      id_endereco_destino: v.id_endereco_destino,
      quantidade_desejada: v.quantidade_desejada,
      prioridade: v.prioridade,
      preco_maximo: v.preco_maximo,
      observacao: v.observacao,
      is_recorrente: v.is_recorrente,
      recorrencia: v.is_recorrente
        ? {
            frequencia: v.frequencia as RecorrenciaFrequencia,
            data_inicio: v.data_inicio!,
            data_fim: v.data_fim || undefined,
            dia_preferencial: v.dia_preferencial!,
          }
        : undefined,
    }, {
      onSuccess: () => {
        form.reset({ is_recorrente: false, quantidade_desejada: 1, prioridade: "media" });
        setOpen(false);
      }
    });
  });

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button className="bg-primary text-primary-foreground hover:bg-primary/90">
          <Plus className="size-4" /> Nova demanda
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Nova demanda</DialogTitle>
          <DialogDescription>
            Cadastre uma intenção de compra. Marque "recorrente" para automatizar a geração periódica.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={onSubmit} className="grid grid-cols-2 gap-4">
          <div className="col-span-2 sm:col-span-1 space-y-1.5">
            <Label>Produto *</Label>
            <Select
              onValueChange={(v) => form.setValue("id_produto", v, { shouldValidate: true })}
              disabled={isLoadingProdutos || isErrorProdutos}
            >
              <SelectTrigger>
                <SelectValue placeholder={
                  isLoadingProdutos ? "Carregando produtos..."
                  : isErrorProdutos ? "Erro ao carregar produtos"
                  : !produtos || produtos.length === 0 ? "Nenhum produto cadastrado"
                  : "Selecione"
                } />
              </SelectTrigger>
              <SelectContent>
                {isErrorProdutos && <SelectItem value="error" disabled>Erro ao carregar produtos</SelectItem>}
                {!isLoadingProdutos && !isErrorProdutos && (!produtos || produtos.length === 0) && (
                  <SelectItem value="empty" disabled>Nenhum produto encontrado</SelectItem>
                )}
                {produtos?.map((p) => (
                  <SelectItem key={p.id} value={p.id}>
                    {p.codigo} — {p.nome}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {form.formState.errors.id_produto && (
              <p className="text-xs text-destructive">{form.formState.errors.id_produto.message}</p>
            )}
          </div>

          <div className="col-span-2 sm:col-span-1 space-y-1.5">
            <Label>Endereço de entrega *</Label>
            <Select
              onValueChange={(v) => form.setValue("id_endereco_destino", v, { shouldValidate: true })}
              disabled={isLoadingEnderecos || isErrorEnderecos}
            >
              <SelectTrigger>
                <SelectValue placeholder={
                  isLoadingEnderecos ? "Carregando endereços..."
                  : isErrorEnderecos ? "Erro ao carregar endereços"
                  : !enderecos || enderecos.length === 0 ? "Nenhum endereço encontrado"
                  : "Selecione"
                } />
              </SelectTrigger>
              <SelectContent>
                {isErrorEnderecos && <SelectItem value="error" disabled>Erro ao carregar endereços</SelectItem>}
                {!isLoadingEnderecos && !isErrorEnderecos && (!enderecos || enderecos.length === 0) && (
                  <SelectItem value="empty" disabled>Nenhum endereço encontrado</SelectItem>
                )}
                {enderecos?.map((e) => (
                  <SelectItem key={e.id} value={e.id}>
                    {e.apelido} — {e.cidade}/{e.uf}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {form.formState.errors.id_endereco_destino && (
              <p className="text-xs text-destructive">{form.formState.errors.id_endereco_destino.message}</p>
            )}
          </div>

          <div className="col-span-2 sm:col-span-1 space-y-1.5">
            <Label>Quantidade *</Label>
            <Input type="number" min={1} {...form.register("quantidade_desejada")} />
          </div>

          <div className="col-span-2 sm:col-span-1 space-y-1.5">
            <Label>Prioridade *</Label>
            <Select onValueChange={(v) => form.setValue("prioridade", v as "baixa"|"media"|"alta", { shouldValidate: true })} defaultValue="media">
              <SelectTrigger><SelectValue placeholder="Selecione" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="baixa">Baixa</SelectItem>
                <SelectItem value="media">Média</SelectItem>
                <SelectItem value="alta">Alta</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="col-span-2 sm:col-span-1 flex items-center justify-between rounded-md border border-input bg-muted/40 px-3 py-2">
            <div>
              <Label className="cursor-pointer">Demanda recorrente</Label>
              <p className="text-xs text-muted-foreground">Gera demandas automaticamente.</p>
            </div>
            <Switch
              checked={isRec}
              onCheckedChange={(c) => form.setValue("is_recorrente", c, { shouldValidate: true })}
            />
          </div>

          <div className="col-span-2 space-y-1.5">
            <Label>Observação</Label>
            <Textarea rows={2} {...form.register("observacao")} />
          </div>

          {isRec && (
            <div className="col-span-2 grid grid-cols-2 gap-4 rounded-md border border-primary/20 bg-accent/40 p-4">
              <div className="col-span-2 sm:col-span-1 space-y-1.5">
                <Label>Frequência *</Label>
                <Select onValueChange={(v) => form.setValue("frequencia", v as RecorrenciaFrequencia, { shouldValidate: true })}>
                  <SelectTrigger><SelectValue placeholder="Selecione" /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="diaria">Diária</SelectItem>
                    <SelectItem value="semanal">Semanal</SelectItem>
                    <SelectItem value="mensal">Mensal</SelectItem>
                  </SelectContent>
                </Select>
                {form.formState.errors.frequencia && (
                  <p className="text-xs text-destructive">{form.formState.errors.frequencia.message}</p>
                )}
              </div>
              <div className="col-span-2 sm:col-span-1 space-y-1.5">
                <Label>Dia preferencial *</Label>
                <Input type="number" min={1} max={31} {...form.register("dia_preferencial")} />
                {form.formState.errors.dia_preferencial && (
                  <p className="text-xs text-destructive">{form.formState.errors.dia_preferencial.message}</p>
                )}
              </div>
              <div className="col-span-2 sm:col-span-1 space-y-1.5">
                <Label>Data de início *</Label>
                <Input type="date" {...form.register("data_inicio")} />
                {form.formState.errors.data_inicio && (
                  <p className="text-xs text-destructive">{form.formState.errors.data_inicio.message}</p>
                )}
              </div>
              <div className="col-span-2 sm:col-span-1 space-y-1.5">
                <Label>Data de fim</Label>
                <Input type="date" {...form.register("data_fim")} />
              </div>
            </div>
          )}

          <DialogFooter className="col-span-2">
            <Button type="button" variant="outline" onClick={() => setOpen(false)}>Cancelar</Button>
            <Button type="submit" disabled={create.isPending} className="bg-secondary text-secondary-foreground hover:bg-secondary/90">
              {create.isPending ? "Publicando..." : "Criar demanda"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
