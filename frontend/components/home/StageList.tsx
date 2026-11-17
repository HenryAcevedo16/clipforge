"use client";
import { Check, Minus, X } from "lucide-react";
import type { Job } from "@/lib/api";
import { friendlyMessage, STAGES, stageStates, type StageState } from "@/lib/stages";
import { cn } from "../ui/cn";

/** Círculo de una etapa: hecho = degradado con check; en curso = anillo que gira; pendiente = número apagado. */
export function Ring({ n, state }: { n: number; state: StageState }) {
  return (
    <span className="relative grid size-10 shrink-0 place-items-center">
      {state === "done" ? (
        <span className="brand-bg grid size-10 place-items-center rounded-full text-white">
          <Check className="size-5" strokeWidth={3} aria-hidden />
        </span>
      ) : state === "failed" ? (
        <span className="grid size-10 place-items-center rounded-full bg-bad-soft text-bad ring-1 ring-bad/50">
          <X className="size-5" strokeWidth={3} aria-hidden />
        </span>
      ) : (
        <>
          <svg viewBox="0 0 40 40" className={cn("absolute inset-0 size-full", state === "active" && "motion-safe:animate-[sweep_1.6s_linear_infinite]")} aria-hidden>
            <circle cx="20" cy="20" r="17.5" fill="none" strokeWidth="3" className="stroke-line" strokeDasharray={state === "skipped" ? "3 5" : undefined} />
            {state === "active" && <path d="M20 2.5a17.5 17.5 0 0 1 17.5 17.5" fill="none" strokeWidth="3" strokeLinecap="round" className="stroke-accent-hi" />}
          </svg>
          <span className={cn("relative text-sm font-extrabold", state === "active" ? "text-ink" : "text-ink-3")}>{state === "skipped" ? <Minus className="size-4" aria-hidden /> : n}</span>
        </>
      )}
    </span>
  );
}

const SR: Record<StageState, string> = { done: "completada", active: "en curso", pending: "pendiente", skipped: "no hace falta", failed: "con error" };

/** Etapas reales del pipeline (lib/stages.ts). El mensaje de la etapa en curso es el que escribe el backend, en español claro. */
export function StageList({ job }: { job: Job }) {
  const states = stageStates(job);
  return (
    <ol className="flex flex-col">
      {STAGES.map((s, i) => {
        const st = states[i];
        const last = i === STAGES.length - 1;
        return (
          <li key={s.id} className="relative flex gap-4 pb-5 last:pb-0" aria-current={st === "active" ? "step" : undefined}>
            {!last && <span aria-hidden className={cn("absolute left-[19px] top-10 h-[calc(100%-2.5rem)] w-0.5 rounded", st === "done" ? "bg-accent" : "bg-line")} />}
            <Ring n={i + 1} state={st} />
            <div className="min-w-0 flex-1 pt-1.5">
              <p className={cn("font-bold leading-tight", st === "pending" ? "text-ink-3" : "text-ink")}>
                {s.label} <span className="sr-only">— {SR[st]}</span>
              </p>
              <p className="mt-0.5 text-sm text-ink-2 [overflow-wrap:anywhere]">{st === "active" ? friendlyMessage(job.message) : st === "skipped" ? "No hace falta: subiste el video." : st === "failed" ? job.message : s.hint}</p>
            </div>
          </li>
        );
      })}
    </ol>
  );
}
