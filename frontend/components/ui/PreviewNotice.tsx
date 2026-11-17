import { Info } from "lucide-react";
import type { ReactNode } from "react";

/** Aviso de pantallas que todavía no están conectadas al backend (se guardan solo en este navegador). */
export function PreviewNotice({ children }: { children: ReactNode }) {
  return (
    <p role="note" className="mb-6 flex items-start gap-2.5 rounded-2xl border border-warn/30 bg-warn-soft px-4 py-3 text-sm text-warn">
      <Info className="mt-0.5 size-4 shrink-0" aria-hidden />
      <span className="[overflow-wrap:anywhere]">{children}</span>
    </p>
  );
}
