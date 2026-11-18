import { api } from "./index";

/** Espera a que termine un trabajo en segundo plano (rehacer, optimizar...). Lanza si falla. */
export async function waitJob(id: string, onTick?: (pct: number, msg: string) => void, alive: () => boolean = () => true): Promise<void> {
  for (;;) {
    await new Promise((r) => setTimeout(r, 1000));
    if (!alive()) return;
    const j = await api.getJob(id);
    onTick?.(j.progress, j.message);
    if (j.status === "error") throw new Error(j.message || "No se pudo completar.");
    if (j.status === "done") return;
  }
}
