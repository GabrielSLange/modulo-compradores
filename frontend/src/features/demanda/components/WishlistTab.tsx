import { useState } from "react";
import { format } from "date-fns";
import { ArrowRightCircle, Plus } from "lucide-react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Textarea } from "@/components/ui/textarea";
import {
  Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle, DialogTrigger,
} from "@/components/ui/dialog";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";

import { useAddWishlist, useConvertWishlist, useWishlist } from "../hooks/useWishlist";
import { useEnderecos } from "../hooks/useEnderecos";
import { ProdutoCell } from "./ProdutoCell";
import { mockProdutosCatalog } from "../mocks/store";

const schema = z.object({
  id_produto: z.string().min(1),
  quantidade_desejada: z.coerce.number().int().positive(),
  observacao: z.string().optional(),
});
type Form = z.infer<typeof schema>;

export function WishlistTab() {
  const { data: items, isLoading } = useWishlist();
  const { data: enderecos = [] } = useEnderecos();
  const add = useAddWishlist();
  const convert = useConvertWishlist();
  const [open, setOpen] = useState(false);
  const [convertId, setConvertId] = useState<string | null>(null);
  const [endereco, setEndereco] = useState<string>("");

  const form = useForm<Form>({ resolver: zodResolver(schema), defaultValues: { quantidade_desejada: 1 } });

  return (
    <section className="space-y-4">
      <header className="flex flex-col gap-3 rounded-lg border border-border bg-card p-5 shadow-[var(--shadow-card)] sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h2 className="text-lg font-semibold text-primary">Wishlist</h2>
          <p className="text-sm text-muted-foreground">
            Intenções informais de compra. Podem ser convertidas em demanda quando confirmadas.
          </p>
        </div>
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild>
            <Button className="bg-primary text-primary-foreground hover:bg-primary/90">
              <Plus className="size-4" /> Adicionar à wishlist
            </Button>
          </DialogTrigger>
          <DialogContent aria-describedby={undefined}>
            <DialogHeader><DialogTitle>Novo item</DialogTitle></DialogHeader>
            <form
              onSubmit={form.handleSubmit(async (v) => {
                await add.mutateAsync({
                  id_usuario: "u-1",
                  id_empresa: "emp-1",
                  id_produto: v.id_produto,
                  quantidade_desejada: v.quantidade_desejada,
                  observacao: v.observacao,
                });
                form.reset({ quantidade_desejada: 1 });
                setOpen(false);
              })}
              className="space-y-3"
            >
              <div className="space-y-1.5">
                <Label>Produto</Label>
                <Select onValueChange={(v) => form.setValue("id_produto", v, { shouldValidate: true })}>
                  <SelectTrigger><SelectValue placeholder="Selecione" /></SelectTrigger>
                  <SelectContent>
                    {mockProdutosCatalog.map((p) => (
                      <SelectItem key={p.id} value={p.id}>{p.codigo} — {p.nome}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-1.5">
                <Label>Quantidade desejada</Label>
                <Input type="number" min={1} {...form.register("quantidade_desejada")} />
              </div>
              <div className="space-y-1.5">
                <Label>Observação</Label>
                <Textarea rows={2} {...form.register("observacao")} />
              </div>
              <DialogFooter>
                <Button type="submit" className="bg-secondary text-secondary-foreground hover:bg-secondary/90">
                  Adicionar
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </header>

      <div className="overflow-hidden rounded-lg border border-border bg-card shadow-[var(--shadow-card)]">
        <Table>
          <TableHeader>
            <TableRow className="bg-muted/40 hover:bg-muted/40">
              <TableHead className="text-xs uppercase text-muted-foreground">Produto</TableHead>
              <TableHead className="text-xs uppercase text-muted-foreground">Qtd. desejada</TableHead>
              <TableHead className="text-xs uppercase text-muted-foreground">Status</TableHead>
              <TableHead className="text-xs uppercase text-muted-foreground">Criado</TableHead>
              <TableHead className="text-right text-xs uppercase text-muted-foreground">Ações</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              <TableRow><TableCell colSpan={5}><Skeleton className="h-10 w-full" /></TableCell></TableRow>
            ) : (items ?? []).length === 0 ? (
              <TableRow>
                <TableCell colSpan={5} className="py-10 text-center text-sm text-muted-foreground">
                  Nenhum item na wishlist.
                </TableCell>
              </TableRow>
            ) : items!.map((w) => (
              <TableRow key={w.id} className="hover:bg-accent/40">
                <TableCell><ProdutoCell id={w.id_produto} /></TableCell>
                <TableCell className="font-medium">{w.quantidade_desejada}</TableCell>
                <TableCell>
                  {w.convertida_em_demanda ? (
                    <span className="rounded-full bg-success/15 text-success border border-success/30 px-2 py-0.5 text-xs font-medium">
                      Convertida
                    </span>
                  ) : (
                    <span className="rounded-full bg-accent text-accent-foreground border border-primary/20 px-2 py-0.5 text-xs font-medium">
                      Pendente
                    </span>
                  )}
                </TableCell>
                <TableCell className="text-sm text-muted-foreground">
                  {format(new Date(w.criado_em), "dd/MM/yyyy")}
                </TableCell>
                <TableCell className="text-right">
                  {!w.convertida_em_demanda && (
                    <Button
                      size="sm"
                      variant="ghost"
                      className="text-secondary hover:bg-secondary/10 hover:text-secondary"
                      onClick={() => { setConvertId(w.id); setEndereco(""); }}
                    >
                      <ArrowRightCircle className="size-4" /> Converter
                    </Button>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      <Dialog open={!!convertId} onOpenChange={(o) => !o && setConvertId(null)}>
        <DialogContent aria-describedby={undefined}>
          <DialogHeader><DialogTitle>Converter em demanda</DialogTitle></DialogHeader>
          <div className="space-y-3">
            <div className="space-y-1.5">
              <Label>Endereço de entrega</Label>
              <Select value={endereco} onValueChange={setEndereco}>
                <SelectTrigger><SelectValue placeholder="Selecione" /></SelectTrigger>
                <SelectContent>
                  {enderecos.map((e) => (
                    <SelectItem key={e.id} value={e.id}>{e.apelido} — {e.cidade}/{e.uf}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setConvertId(null)}>Cancelar</Button>
            <Button
              disabled={!endereco || convert.isPending}
              className="bg-secondary text-secondary-foreground hover:bg-secondary/90"
              onClick={async () => {
                if (!convertId || !endereco) return;
                await convert.mutateAsync({ id: convertId, id_endereco_entrega: endereco });
                setConvertId(null);
              }}
            >
              {convert.isPending ? "Convertendo..." : "Confirmar"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </section>
  );
}
