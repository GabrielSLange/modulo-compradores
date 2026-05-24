import { useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { Boxes, Heart, MapPin, Moon, Sun, ShoppingCart } from "lucide-react";
import { useTheme } from "next-themes";

import { Dialog, DialogContent } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";

import { DemandasTab } from "@/features/demandas/components/DemandasTab";
import { WishlistTab } from "@/features/wishlist/components/WishlistTab";
import { EnderecosTab } from "@/features/enderecos/components/EnderecosTab";

const mainFrontUrl = import.meta.env.VITE_MAIN_FRONT_URL?.trim() || "/";

export const Route = createFileRoute("/")({
  component: DemandaPage,
});

function DemandaPage() {
  const { theme, setTheme } = useTheme();
  const [open, setOpen] = useState(true);

  function handleOpenChange(nextOpen: boolean) {
    if (nextOpen) {
      setOpen(true);
      return;
    }
    setOpen(false);
    window.location.assign(mainFrontUrl);
  }

  const toggleDark = () => setTheme(theme === "light" ? "dark" : "light");

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent
        className="max-w-[95vw] sm:max-w-7xl border-0 p-0 bg-transparent shadow-none"
        aria-describedby={undefined}
        onPointerDownOutside={(e) => e.preventDefault()}
        onEscapeKeyDown={(e) => e.preventDefault()}
      >
        <div className="mx-auto w-full rounded-2xl border border-border bg-card shadow-[var(--shadow-elevated)] overflow-hidden flex flex-col max-h-[90vh]">
          <header className="flex items-start justify-between gap-4 border-b border-border px-6 py-5 pr-14">
            <div>
              <h1 className="text-2xl font-bold text-primary">Catálogo de Demandas</h1>
              <p className="mt-1 text-sm text-muted-foreground">
                Gestão de demandas, pedidos, wishlist e endereços de entrega
                do microserviço SDI.Micro.Demanda
              </p>
            </div>
            <Button variant="outline" size="icon" onClick={toggleDark} aria-label="Alternar tema">
              {theme === "light" ? <Moon className="size-4" /> : <Sun className="size-4" />}
            </Button>
          </header>

          <div className="overflow-y-auto flex-1 p-0">

            <Tabs defaultValue="demandas" className="px-6 pb-6 pt-4">
              <TabsList className="h-auto justify-start gap-1 rounded-md bg-transparent p-0 border-b border-border w-full">
                <TabTrigger value="demandas" icon={<Boxes className="size-4" />} label="Demandas" />
                <TabTrigger value="pedidos" icon={<ShoppingCart className="size-4" />} label="Pedidos" />
                <TabTrigger value="wishlist" icon={<Heart className="size-4" />} label="Wishlist" />
                <TabTrigger value="enderecos" icon={<MapPin className="size-4" />} label="Endereços" />
              </TabsList>

              <TabsContent value="demandas" className="mt-5"><DemandasTab /></TabsContent>
              <TabsContent value="pedidos" className="mt-5"><DemandasTab isPedido /></TabsContent>
              <TabsContent value="wishlist" className="mt-5"><WishlistTab /></TabsContent>
              <TabsContent value="enderecos" className="mt-5"><EnderecosTab /></TabsContent>
            </Tabs>
          </div>
        </div>
      </DialogContent>
    </Dialog>
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
