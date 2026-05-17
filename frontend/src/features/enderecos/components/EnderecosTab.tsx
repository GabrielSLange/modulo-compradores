import { useMemo, useState } from "react";
import { format } from "date-fns";
import { MapPin, Pencil, X, ChevronLeft, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

import { useEnderecos, useDeleteEndereco } from "../hooks/useEnderecos";
import { EnderecoDialog } from "./EnderecoDialog";

export function EnderecosTab() {
  const { data: enderecos, isLoading } = useEnderecos();
  const deleteEndereco = useDeleteEndereco();

  const [pagina, setPagina] = useState(1);
  const itensPorPagina = 10;
  const totalPaginas = Math.max(1, Math.ceil((enderecos ?? []).length / itensPorPagina));
  const lista = useMemo(() => {
    return (enderecos ?? []).slice((pagina - 1) * itensPorPagina, pagina * itensPorPagina);
  }, [enderecos, pagina]);

  return (
    <section className="space-y-4">
      <header className="flex flex-col gap-3 rounded-lg border border-border bg-card p-5 shadow-[var(--shadow-card)] sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h2 className="text-lg font-semibold text-primary">Endereços de entrega</h2>
        </div>
        <EnderecoDialog />
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
              <TableHead className="text-right text-xs uppercase text-muted-foreground">Ações</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              Array.from({ length: 5 }).map((_, i) => (
                <TableRow key={i}>
                  <TableCell colSpan={6}><Skeleton className="h-10 w-full" /></TableCell>
                </TableRow>
              ))
            ) : (enderecos ?? []).length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} className="py-10 text-center text-sm text-muted-foreground">
                  Nenhum endereço encontrado.
                </TableCell>
              </TableRow>
            ) : lista.map((e) => (
              <TableRow key={e.id} className="hover:bg-accent/40">
                <TableCell className="font-semibold">
                  <span className="inline-flex items-center gap-2"><MapPin className="size-4 text-primary" />{e.apelido}</span>
                </TableCell>
                <TableCell className="text-sm">{e.logradouro}, {e.numero}{e.complemento ? ` — ${e.complemento}` : ""} · {e.bairro}</TableCell>
                <TableCell>{e.cidade}/{e.uf}</TableCell>
                <TableCell className="font-mono text-sm">{e.cep}</TableCell>
                <TableCell className="text-sm text-muted-foreground">{format(new Date(e.data_criacao), "dd/MM/yyyy")}</TableCell>
                <TableCell className="text-right">
                  <div className="flex justify-end gap-1">
                    <EnderecoDialog
                      endereco={e}
                      trigger={
                        <Button size="icon" variant="ghost" title="Editar">
                          <Pencil className="size-4" />
                        </Button>
                      }
                    />
                    <Button
                      size="icon"
                      variant="ghost"
                      title="Excluir"
                      onClick={() => deleteEndereco.mutate(e.id)}
                      className="text-destructive hover:text-destructive hover:bg-destructive/10"
                    >
                      <X className="size-4" />
                    </Button>
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      <div className="flex items-center justify-between px-1">
        <p className="text-xs text-muted-foreground">
          Exibindo página {pagina} de {totalPaginas} · {(enderecos ?? []).length} registro(s)
        </p>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setPagina((p) => Math.max(1, p - 1))}
            disabled={pagina === 1}
            className="h-8 text-xs bg-transparent"
          >
            <ChevronLeft className="mr-1 size-3" /> Anterior
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setPagina((p) => Math.min(totalPaginas, p + 1))}
            disabled={pagina === totalPaginas}
            className="h-8 text-xs bg-transparent"
          >
            Próxima <ChevronRight className="ml-1 size-3" />
          </Button>
        </div>
      </div>
    </section>
  );
}
