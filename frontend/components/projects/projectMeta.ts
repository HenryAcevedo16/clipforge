import type { Project, ProjectState } from "@/lib/api";
import { jobTitle } from "@/lib/format";
import type { Tone } from "../ui/Badge";

export const STATE_META: Record<ProjectState, { label: string; tone: Tone }> = {
  queued: { label: "En cola", tone: "neutral" },
  running: { label: "Procesando", tone: "accent" },
  done: { label: "Terminado", tone: "ok" },
  empty: { label: "Sin clips", tone: "warn" },
  error: { label: "Falló", tone: "bad" },
};

export function projectTitle(p: Project): string {
  return jobTitle(p.job);
}

export const FILTERS: { v: "all" | "active" | ProjectState; label: string }[] = [
  { v: "all", label: "Todos" },
  { v: "active", label: "En proceso" },
  { v: "done", label: "Terminados" },
  { v: "empty", label: "Sin clips" },
  { v: "error", label: "Fallidos" },
];
