import { useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { Boxes, Heart, MapPin, Moon, Sun } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";

import { DemandasTab } from "@/features/demandas/components/DemandasTab";
import { WishlistTab } from "@/features/wishlist/components/WishlistTab";
import { EnderecosTab } from "@/features/enderecos/components/EnderecosTab";

export const Route = createFileRoute("/")({
  component: DemandaPage,
});

function DemandaPage() {
  const [dark, setDark] = useState(false);

  const toggleDark = () => {
    const next = !dark;
    setDark(next);
    document.documentElement.classList.toggle("dark", next);
  };

  return (
    <main className="min-h-screen bg-background p-4 sm:p-8">
      <div className="mx-auto max-w-7xl rounded-2xl border border-border bg-card shadow-[var(--shadow-elevated)]">
        <header className="flex items-start justify-between gap-4 border-b border-border px-6 py-5">
          <div>
            <h1 className="text-2xl font-bold text-primary">Catálogo de Demandas</h1>
            <p className="mt-1 text-sm text-muted-foreground">
              Gestão de demandas únicas e recorrentes, wishlist e endereços de entrega
              do microserviço <span className="font-medium text-foreground">SDI.Micro.Demanda</span>.
            </p>
          </div>
          <Button variant="outline" size="icon" onClick={toggleDark} aria-label="Alternar tema">
            {dark ? <Sun className="size-4" /> : <Moon className="size-4" />}
          </Button>
        </header>

        <Tabs defaultValue="demandas" className="px-6 pb-6 pt-4">
          <TabsList className="h-auto justify-start gap-1 rounded-md bg-transparent p-0 border-b border-border w-full">
            <TabTrigger value="demandas" icon={<Boxes className="size-4" />} label="Demandas" />
            <TabTrigger value="wishlist" icon={<Heart className="size-4" />} label="Wishlist" />
            <TabTrigger value="enderecos" icon={<MapPin className="size-4" />} label="Endereços" />
          </TabsList>

          <TabsContent value="demandas" className="mt-5"><DemandasTab /></TabsContent>
          <TabsContent value="wishlist" className="mt-5"><WishlistTab /></TabsContent>
          <TabsContent value="enderecos" className="mt-5"><EnderecosTab /></TabsContent>
        </Tabs>
      </div>
    </main>
  );
}

function TabTrigger({ value, icon, label }: { value: string; icon: React.ReactNode; label: string }) {
  return (
    <TabsTrigger
      value={value}
      className="gap-2 rounded-none border-b-2 border-transparent bg-transparent px-4 py-2.5 text-sm font-medium text-muted-foreground shadow-none data-[state=active]:border-primary data-[state=active]:bg-transparent data-[state=active]:text-primary data-[state=active]:shadow-none"
    >
      {icon}{label}
    </TabsTrigger>
  );
}
