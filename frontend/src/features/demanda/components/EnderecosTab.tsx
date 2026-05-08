import { useState } from "react";
import { format } from "date-fns";
import { Plus, MapPin } from "lucide-react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import {
  Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle, DialogTrigger,
} from "@/components/ui/dialog";

import { useCreateEndereco, useEnderecos } from "../hooks/useEnderecos";

const schema = z.object({
  apelido: z.string().min(1),
  logradouro: z.string().min(1),
  numero: z.string().min(1),
  complemento: z.string().optional(),
  bairro: z.string().min(1),
  cidade: z.string().min(1),
  uf: z.string().length(2),
  cep: z.string().min(8),
});
type Form = z.infer<typeof schema>;

export function EnderecosTab() {
  const { data: enderecos, isLoading } = useEnderecos();
  const create = useCreateEndereco();
  const [open, setOpen] = useState(false);
  const form = useForm<Form>({ resolver: zodResolver(schema) });

  return (
    <section className="space-y-4">
      <header className="flex flex-col gap-3 rounded-lg border border-border bg-card p-5 shadow-[var(--shadow-card)] sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h2 className="text-lg font-semibold text-primary">Endereços de entrega</h2>
          <p className="text-sm text-muted-foreground">
            Cadastro próprio do módulo Demanda — independente dos endereços globais (Equipe 1).
          </p>
        </div>
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild>
            <Button className="bg-primary text-primary-foreground hover:bg-primary/90">
              <Plus className="size-4" /> Novo endereço
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-xl">
            <DialogHeader><DialogTitle>Novo endereço</DialogTitle></DialogHeader>
            <form
              onSubmit={form.handleSubmit(async (v) => {
                await create.mutateAsync({ ...v, id_empresa: "emp-1" });
                form.reset();
                setOpen(false);
              })}
              className="grid grid-cols-2 gap-3"
            >
              <div className="col-span-2 space-y-1.5"><Label>Apelido</Label><Input {...form.register("apelido")} /></div>
              <div className="col-span-2 space-y-1.5"><Label>Logradouro</Label><Input {...form.register("logradouro")} /></div>
              <div className="space-y-1.5"><Label>Número</Label><Input {...form.register("numero")} /></div>
              <div className="space-y-1.5"><Label>Complemento</Label><Input {...form.register("complemento")} /></div>
              <div className="col-span-2 space-y-1.5"><Label>Bairro</Label><Input {...form.register("bairro")} /></div>
              <div className="space-y-1.5"><Label>Cidade</Label><Input {...form.register("cidade")} /></div>
              <div className="space-y-1.5"><Label>UF</Label><Input maxLength={2} {...form.register("uf")} /></div>
              <div className="col-span-2 space-y-1.5"><Label>CEP</Label><Input {...form.register("cep")} /></div>
              <DialogFooter className="col-span-2">
                <Button type="submit" className="bg-secondary text-secondary-foreground hover:bg-secondary/90">
                  Salvar
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
              <TableHead className="text-xs uppercase text-muted-foreground">Apelido</TableHead>
              <TableHead className="text-xs uppercase text-muted-foreground">Endereço</TableHead>
              <TableHead className="text-xs uppercase text-muted-foreground">Cidade/UF</TableHead>
              <TableHead className="text-xs uppercase text-muted-foreground">CEP</TableHead>
              <TableHead className="text-xs uppercase text-muted-foreground">Cadastro</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              <TableRow><TableCell colSpan={5}><Skeleton className="h-10 w-full" /></TableCell></TableRow>
            ) : enderecos!.map((e) => (
              <TableRow key={e.id} className="hover:bg-accent/40">
                <TableCell className="font-semibold">
                  <span className="inline-flex items-center gap-2"><MapPin className="size-4 text-primary" />{e.apelido}</span>
                </TableCell>
                <TableCell className="text-sm">{e.logradouro}, {e.numero}{e.complemento ? ` — ${e.complemento}` : ""} · {e.bairro}</TableCell>
                <TableCell>{e.cidade}/{e.uf}</TableCell>
                <TableCell className="font-mono text-sm">{e.cep}</TableCell>
                <TableCell className="text-sm text-muted-foreground">{format(new Date(e.criado_em), "dd/MM/yyyy")}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </section>
  );
}
