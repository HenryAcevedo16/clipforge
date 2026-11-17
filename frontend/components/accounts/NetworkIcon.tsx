import { Clapperboard, Music2, Smartphone } from "lucide-react";
import type { Network } from "@/lib/api";
import { NETWORK_META } from "@/lib/brand";

/** Símbolos neutros (no usamos logos de las redes). El color de cada red se usa solo como punto de referencia. */
export function NetworkIcon({ network, className = "size-5" }: { network: Network; className?: string }) {
  const I = network === "tiktok" ? Music2 : network === "youtube" ? Clapperboard : Smartphone;
  return <I className={className} aria-hidden />;
}

export function NetworkChip({ network, label }: { network: Network; label?: string }) {
  const m = NETWORK_META[network];
  return (
    <span className="inline-flex items-center gap-1.5 text-sm font-medium">
      <span aria-hidden className="size-2.5 rounded-full" style={{ background: m.color }} />
      {label ?? m.short}
    </span>
  );
}
