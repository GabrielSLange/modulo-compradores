import { useState, useEffect } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { Pencil, Plus } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle, DialogTrigger,
} from "@/components/ui/dialog";

import { useCreateEndereco, useUpdateEndereco } from "../hooks/useEnderecos";
import type { EnderecoEntrega } from "@/features/types";

const schema = z.object({
  apelido: z.string().min(1),
  logradouro: z.string().min(1),
  numero: z.string().optional(),
  complemento: z.string().optional(),
  bairro: z.string().min(1),
  cidade: z.string().min(1),
  uf: z.string().length(2),
  cep: z.string().min(8),
});
type Form = z.infer<typeof schema>;

interface Props {
  endereco?: EnderecoEntrega;
  trigger?: React.ReactNode;
}

export function EnderecoDialog({ endereco, trigger }: Props) {
  const [open, setOpen] = useState(false);
  const create = useCreateEndereco();
  const update = useUpdateEndereco();

  const form = useForm<Form>({
    resolver: zodResolver(schema),
    defaultValues: endereco || {},
  });

  // Reset form when opening to ensure clean state or fresh edit data
  useEffect(() => {
    if (open) {
      if (endereco) {
        form.reset({
          apelido: endereco.apelido || "",
          logradouro: endereco.logradouro,
          numero: endereco.numero || "",
          complemento: endereco.complemento || "",
          bairro: endereco.bairro || "",
          cidade: endereco.cidade,
          uf: endereco.uf,
          cep: endereco.cep,
        });
      } else {
        form.reset({
          apelido: "", logradouro: "", numero: "", complemento: "", bairro: "", cidade: "", uf: "", cep: ""
        });
      }
    }
  }, [open, endereco, form]);

  const onSubmit = form.handleSubmit((v) => {
    if (endereco) {
      update.mutate({ id: endereco.id, payload: v }, {
        onSuccess: () => setOpen(false)
      });
    } else {
      create.mutate(v, {
        onSuccess: () => setOpen(false)
      });
    }
  });

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        {trigger || (
          <Button className="bg-primary text-primary-foreground hover:bg-primary/90">
            <Plus className="size-4" /> Novo endereço
          </Button>
        )}
      </DialogTrigger>
      <DialogContent className="max-w-xl" aria-describedby={undefined}>
        <DialogHeader>
          <DialogTitle>{endereco ? "Editar endereço" : "Novo endereço"}</DialogTitle>
        </DialogHeader>
        <form onSubmit={onSubmit} className="grid grid-cols-2 gap-3">
          <div className="col-span-2 space-y-1.5"><Label>Apelido</Label><Input {...form.register("apelido")} /></div>
          <div className="col-span-2 space-y-1.5"><Label>Logradouro</Label><Input {...form.register("logradouro")} /></div>
          <div className="space-y-1.5"><Label>Número</Label><Input {...form.register("numero")} /></div>
          <div className="space-y-1.5"><Label>Complemento</Label><Input {...form.register("complemento")} /></div>
          <div className="col-span-2 space-y-1.5"><Label>Bairro</Label><Input {...form.register("bairro")} /></div>
          <div className="space-y-1.5"><Label>Cidade</Label><Input {...form.register("cidade")} /></div>
          <div className="space-y-1.5"><Label>UF</Label><Input maxLength={2} {...form.register("uf")} /></div>
          <div className="col-span-2 space-y-1.5"><Label>CEP</Label><Input {...form.register("cep")} /></div>
          <DialogFooter className="col-span-2">
            <Button type="button" variant="outline" onClick={() => setOpen(false)}>Cancelar</Button>
            <Button type="submit" disabled={create.isPending || update.isPending} className="bg-secondary text-secondary-foreground hover:bg-secondary/90">
              {create.isPending || update.isPending ? "Salvando..." : "Salvar"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
