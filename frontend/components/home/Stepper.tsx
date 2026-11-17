import { Check } from "lucide-react";
import { cn } from "../ui/cn";

export const HOME_STEPS = ["Tu video", "Personalizar", "Procesar", "Resultado"];

/** Tira de 4 pasos con píldoras. El paso actual lleva aria-current="step"; los pasos hechos (1–2) se pueden volver a abrir. */
export function Stepper({ step, onGo }: { step: number; onGo: (n: number) => void }) {
  return (
    <ol className="mb-8 grid grid-cols-4 gap-2 sm:gap-3" aria-label="Pasos para crear tus clips">
      {HOME_STEPS.map((label, i) => {
        const n = i + 1;
        const done = n < step;
        const on = n === step;
        const canGo = done && step < 3;
        const inner = (
          <>
            <span className={cn("grid size-8 shrink-0 place-items-center rounded-full text-sm font-extrabold transition-[background-color,color,box-shadow] duration-200 ease-[var(--ease-out)]", done || on ? "brand-bg text-white" : "bg-raised-2 text-ink-3", on && "shadow-[0_0_0_4px_oklch(0.6_0.22_290/0.25)]")}>
              {done ? <Check className="size-4" strokeWidth={3} aria-hidden /> : n}
            </span>
            <span className={cn("text-[13px] font-bold leading-tight sm:text-sm", on ? "text-ink" : done ? "text-ink-2" : "text-ink-3")}>{label}</span>
          </>
        );
        return (
          <li key={label} aria-current={on ? "step" : undefined} className="min-w-0">
            {canGo ? (
              <button type="button" onClick={() => onGo(n)} className="flex w-full flex-col items-start gap-2 rounded-2xl border border-line bg-raised p-3 text-left transition-colors hover:border-line-2 sm:flex-row sm:items-center sm:gap-2.5">
                {inner}
                <span className="sr-only">(volver a este paso)</span>
              </button>
            ) : (
              <div className={cn("flex flex-col items-start gap-2 rounded-2xl border p-3 sm:flex-row sm:items-center sm:gap-2.5", on ? "border-transparent bg-surface-secondary shadow-[inset_0_0_0_1px_var(--color-line-2)]" : "border-line bg-raised/60")}>{inner}</div>
            )}
          </li>
        );
      })}
    </ol>
  );
}
