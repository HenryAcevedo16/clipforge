import { TriangleAlert } from "lucide-react";
import Link from "next/link";

/** Aviso cuando los clips NO los eligió la IA (método básico): suelen ser más flojos y a veces no tienen sentido. */
export function SelectionNotice({ selection }: { selection?: { mode: string; reason: string } }) {
  if (selection?.mode !== "basico") return null;
  return (
    <div role="note" className="mb-5 flex items-start gap-3 rounded-2xl border border-warn/40 bg-warn-soft px-4 py-3.5 text-sm text-warn">
      <TriangleAlert className="mt-0.5 size-4 shrink-0" aria-hidden />
      <div className="min-w-0 [overflow-wrap:anywhere]">
        <p className="font-bold">Estos clips los eligió el método básico, sin IA</p>
        <p className="mt-0.5 text-ink-2">
          Por eso las notas son bajas y algunos clips pueden no tener sentido. {selection.reason ? `Motivo: ${selection.reason.replace(/[.\s]+$/, "")}. ` : ""}
          Activa una IA en <Link href="/ajustes" className="font-bold underline">Ajustes → Inteligencia artificial</Link> y vuelve a generar el video.
        </p>
      </div>
    </div>
  );
}
