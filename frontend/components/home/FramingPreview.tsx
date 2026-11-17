"use client";
import { Loader2, RefreshCw } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { api, ApiError, type PreviewInput } from "@/lib/api";
import { Button } from "../ui/Button";
import { Dialog } from "../ui/Dialog";

/** Muestra de ~10 s con el encuadre y los efectos elegidos, para ver cómo quedará antes de generar todo. */
export function FramingPreview({ input, onClose }: { input: Omit<PreviewInput, "at">; onClose: () => void }) {
  const [state, setState] = useState<{ phase: "work" | "done" | "error"; pct: number; msg: string; src?: string; info?: string }>({ phase: "work", pct: 0, msg: "Enviando…" });
  const alive = useRef(true);
  const inputRef = useRef(input);
  inputRef.current = input;

  const run = useCallback(async (at: number) => {
    setState({ phase: "work", pct: 0, msg: "Enviando…" });
    try {
      const { id } = await api.previewFraming({ ...inputRef.current, at });
      for (;;) {
        await new Promise((r) => setTimeout(r, 1000));
        if (!alive.current) return;
        const j = await api.getJob(id);
        setState((s) => ({ ...s, pct: j.progress, msg: j.message }));
        if (j.status === "error") throw new ApiError(j.message || "No pude crear la muestra.");
        if (j.status === "done") {
          const c = j.result?.clips?.[0];
          if (!c) throw new ApiError("No salió la muestra.");
          const mins = (c as { moment?: number }).moment ?? 0;
          setState({ phase: "done", pct: 100, msg: "", src: `${api.fileUrl(id, c.file)}?v=${c.rev ?? Date.now()}`, info: `Muestra del minuto ${(mins / 60).toFixed(1)} · encuadre usado: ${c.layout || "automático"}` });
          return;
        }
      }
    } catch (e) {
      if (alive.current) setState({ phase: "error", pct: 0, msg: e instanceof Error ? e.message : "No pude crear la muestra." });
    }
  }, []);

  useEffect(() => {
    alive.current = true;
    run(0.35);
    return () => {
      alive.current = false;
    };
  }, [run]);

  return (
    <Dialog
      open
      onClose={onClose}
      title="Vista previa del encuadre"
      footer={
        <>
          <Button onClick={() => run(0.1 + Math.random() * 0.8)} disabled={state.phase === "work"} icon={<RefreshCw className="size-4" aria-hidden />}>
            Probar otro momento
          </Button>
          <Button variant="primary" onClick={onClose}>
            Listo
          </Button>
        </>
      }
    >
      {state.phase === "work" && (
        <div role="status" className="flex flex-col gap-3 py-4">
          <div className="flex items-center gap-2 font-semibold">
            <Loader2 className="size-4 animate-spin motion-reduce:animate-none" aria-hidden />
            <span className="min-w-0 truncate">{state.msg || "Trabajando…"}</span>
            <span className="tnum ml-auto text-ink-3">{Math.round(state.pct)}%</span>
          </div>
          <div className="h-1.5 overflow-hidden rounded-full bg-raised-2">
            <div className="brand-bg h-full rounded-full transition-[width] duration-500" style={{ width: `${state.pct}%` }} />
          </div>
          <p className="text-sm text-ink-3">Saco 10 segundos del video y les aplico el encuadre y los efectos que elegiste.</p>
        </div>
      )}
      {state.phase === "error" && (
        <p role="alert" className="rounded-2xl border border-bad/40 bg-bad-soft/60 p-4 text-ink-2">
          {state.msg}
        </p>
      )}
      {state.phase === "done" && state.src && (
        <div className="flex flex-col items-center gap-3">
          <video key={state.src} src={state.src} controls autoPlay loop muted playsInline className="aspect-[9/16] max-h-[26rem] w-auto rounded-2xl bg-black object-contain" aria-label="Muestra del encuadre" />
          <p className="text-center text-sm text-ink-3">{state.info}. Si no te gusta, cambia el encuadre y vuelve a probar.</p>
        </div>
      )}
    </Dialog>
  );
}
