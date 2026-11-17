/**
 * Implementación SIMULADA (NEXT_PUBLIC_USE_MOCK=true).
 *
 * Lógica clave (para aprender):
 *  - Un trabajo creado guarda sus opciones y la hora de creación. `getJob()` NO usa timers: calcula
 *    "qué mensaje tocaría ahora" según el tiempo transcurrido, con la misma secuencia de mensajes y
 *    rangos de progreso que escribe pipeline.py. Así el progreso sobrevive a recargar la página.
 *  - Las respuestas tienen exactamente la forma del backend real (types.ts, parte 1).
 */
import { ApiError, type Api, type Config, type CreateJobInput, type Job, type Project, type ProjectState } from "./types";
import { createExtras, type MockMode } from "./extras";
import { assetFor, extremeJobs, makeClips, makeResult, seedJobs, type SeedJob } from "./mock-data";
import { readJSON, readString, sleep, uid, writeJSON } from "./storage";

const K = { mode: "novoclip:mock:mode", jobs: "novoclip:v1:jobs", projects: "novoclip:v1:projects" };

export function getMockMode(): MockMode {
  const m = readString(K.mode, "normal");
  return (["normal", "empty", "error", "slow", "extreme"].includes(m) ? m : "normal") as MockMode;
}

const latency = () => (getMockMode() === "slow" ? 3500 : 280 + Math.random() * 320);
const wait = async (): Promise<void> => { await sleep(latency()); };

interface StoredJob {
  job: Job; // snapshot inicial (queued)
  meta?: { numClips: number; review: boolean; ai: boolean; fail: boolean; title: string; lengthS: number };
  frozen?: boolean;
  addedAt?: number;
}

const config: Config = { ai: true, styles: ["viral", "caja", "karaoke", "neon", "minimal", "none"], aspects: ["9:16", "1:1", "4:5", "16:9"] };

// ───────── Secuencia de eventos del pipeline para un trabajo creado ─────────

interface Ev {
  t: number; // segundos desde la creación
  p: number;
  msg: string;
  fail?: string;
}

const QUEUE_S = 1.5;
const DOWNLOAD_S = 6;
const TRANSCRIBE_S = 10;
const PER_CLIP_S = 4;

function buildEvents(source: string, m: NonNullable<StoredJob["meta"]>): Ev[] {
  const ev: Ev[] = [];
  let t = QUEUE_S;
  const isUrl = /^https?:\/\//.test(source);
  if (isUrl) {
    ev.push({ t, p: 1, msg: "Descargando video de YouTube..." });
    for (let k = 1; k <= 4; k++) ev.push({ t: t + (DOWNLOAD_S * k) / 5, p: 2 + 8 * (k / 5), msg: "Descargando video..." });
    t += DOWNLOAD_S;
  }
  ev.push({ t, p: 11, msg: `Video: 1920x1080 @ 30fps, ${m.lengthS}s` });
  t += 0.5;
  ev.push({ t, p: 12, msg: "Cargando modelo Whisper 'small'..." });
  if (m.fail) {
    ev.push({ t: t + 3, p: 12 + 28 * 0.3, msg: "Falló", fail: "No se encontraron segmentos con voz para recortar." });
    return ev;
  }
  t += 1.2;
  for (let k = 1; k <= 6; k++) {
    const frac = k / 6;
    ev.push({ t: t + TRANSCRIBE_S * frac, p: 12 + 28 * frac, msg: `Transcribiendo... ${Math.round(m.lengthS * frac)}s / ${m.lengthS}s` });
  }
  t += TRANSCRIBE_S + 0.4;
  ev.push(m.ai ? { t, p: 42, msg: "La IA está eligiendo los mejores momentos..." } : { t, p: 43, msg: "Analizando energía, ganchos y ritmo..." });
  t += 1.6;
  const span = 55 / m.numClips;
  for (let n = 0; n < m.numClips; n++) {
    const p0 = 45 + n * span;
    const pEnd = p0 + span * (m.review ? 0.85 : 1);
    const c = n + 1;
    const t0 = t + n * PER_CLIP_S;
    ev.push({ t: t0, p: p0, msg: `Clip ${c}: cortando...` });
    ev.push({ t: t0 + 0.5, p: p0 + (pEnd - p0) * 0.15, msg: `Clip ${c}: analizando el encuadre...` });
    const total = 300;
    for (let k = 1; k <= 3; k++) ev.push({ t: t0 + 0.5 + (PER_CLIP_S - 1.2) * (k / 3), p: p0 + (pEnd - p0) * (0.3 + 0.68 * (k / 3)), msg: `Clip ${c}: renderizando ${Math.round(total * (k / 3))}/${total} frames` });
    if (m.review) ev.push({ t: t0 + PER_CLIP_S - 0.5, p: pEnd, msg: `Clip ${c}: la IA está revisando el resultado...` });
  }
  ev.push({ t: t + m.numClips * PER_CLIP_S, p: 100, msg: `¡Listo! ${m.numClips} clips generados.` });
  return ev;
}

function resolveJob(s: StoredJob): Job {
  if (s.frozen || !s.meta) return s.job;
  const base = s.job;
  const elapsed = Date.now() / 1000 - base.created;
  const events = buildEvents(base.source, s.meta);
  const seen = events.filter((e) => e.t <= elapsed);
  const log: string[] = [];
  for (const e of seen) if (!e.fail && log[log.length - 1] !== e.msg) log.push(e.msg);
  const last = seen[seen.length - 1];
  if (!last) return { ...base, status: "queued", progress: 0, message: "En cola...", log: [] };
  if (last.fail) return { ...base, status: "error", progress: Math.round(last.p * 10) / 10, message: last.fail, log };
  if (last.p >= 100) {
    const clips = makeClips(s.meta.numClips, { review: s.meta.review });
    return { ...base, status: "done", progress: 100, message: last.msg, log, result: makeResult(s.meta.title, clips, "es", s.meta.lengthS) };
  }
  return { ...base, status: "running", progress: Math.round(last.p * 10) / 10, message: last.msg, log };
}

// ───────── Almacén de trabajos ─────────

function allJobs(): StoredJob[] {
  const mode = getMockMode();
  const created = readJSON<StoredJob[]>(K.jobs, []);
  if (mode === "empty") return created;
  const seeds: SeedJob[] = [...seedJobs(), ...(mode === "extreme" ? extremeJobs() : [])];
  return [...created, ...seeds.map((s) => ({ job: s.job, frozen: true, addedAt: s.addedAt }))];
}

function titleFromSource(url: string, file?: File | null): string {
  if (file) return file.name.replace(/\.[^.]+$/, "");
  const m = url.match(/[?&]v=([\w-]{6,})/) ?? url.match(/youtu\.be\/([\w-]{6,})/);
  return m ? `Video de YouTube (${m[1]})` : "Video de YouTube";
}

function stateOf(job: Job): ProjectState {
  if (job.status === "done") return job.result && job.result.clips.length === 0 ? "empty" : "done";
  return job.status === "queued" ? "queued" : job.status === "running" || job.status === "live" ? "running" : "error";
}

function addedIds(): { jobId: string; addedAt: number }[] {
  return readJSON(K.projects, []);
}

const extras = createExtras({ seeded: true, mode: getMockMode, wait });

function failIfModeError() {
  if (getMockMode() === "error") throw new ApiError("No pudimos conectar con el servidor. Revisa tu conexión e inténtalo de nuevo.", 503);
}

export const mockApi: Api = {
  kind: "mock",

  async getConfig() {
    await wait();
    failIfModeError();
    return config;
  },

  /** Valida igual que app.py: create_job(). */
  async createJob(input: CreateJobInput) {
    await wait();
    failIfModeError();
    const url = (input.url ?? "").trim();
    if (!url && !input.file) throw new ApiError("Pega una URL de YouTube o sube un video.", 400);
    if (input.min_len >= input.max_len) throw new ApiError("La duración mínima debe ser menor que la máxima.", 400);
    const id = uid(10);
    const numClips = Math.max(1, Math.min(input.num_clips, 30));
    const source = input.file?.name ? input.file.name : url;
    const job: Job = { id, status: "queued", progress: 0, message: "En cola...", log: [], source: url || input.file?.name || "", created: Date.now() / 1000, result: null };
    const stored: StoredJob = {
      job,
      meta: { numClips, review: input.review, ai: true, fail: /falla|error/i.test(source), title: titleFromSource(url, input.file), lengthS: 1843 },
    };
    writeJSON(K.jobs, [stored, ...readJSON<StoredJob[]>(K.jobs, [])]);
    return { id };
  },

  async getJob(id: string) {
    await sleep(120);
    failIfModeError();
    const s = allJobs().find((j) => j.job.id === id);
    if (!s) throw new ApiError("Trabajo no encontrado", 404);
    return resolveJob(s);
  },

  /** Los archivos de ejemplo salen de /public/mock/clips (a–d). En real: /files/{job_id}/{name}. */
  async cancelJob() {
    /* en el modo simulado no hay nada que cancelar */
  },
  async saveSettings() {
    return config;
  },
  async getClipEdit(jobId, index) {
    const job = await this.getJob(jobId);
    const clip = job.result?.clips.find((c) => c.index === index);
    if (!clip) throw new ApiError("Clip no encontrado", 404);
    const words = (clip.title + " " + clip.caption).split(/\s+/).filter(Boolean).map((w, i) => ({ w, s: clip.start + i * 0.5, e: clip.start + i * 0.5 + 0.4 }));
    return { clip, words, editable: true, layout: "auto", caption_style: "viral", styles: config.styles };
  },
  async renderClip() {
    return { id: "mock-render" };
  },
  async deleteClip() {
    /* simulado */
  },
  fileUrl(_jobId, name, opts) {
    const key = assetFor(name);
    return `/mock/clips/${key}.${name.endsWith(".jpg") ? "jpg" : "mp4"}${opts?.download ? "?download=1" : ""}`;
  },

  // ── [REQUIERE BACKEND NUEVO] Proyectos ──
  async listProjects() {
    await wait();
    failIfModeError();
    const added = new Map(addedIds().map((a) => [a.jobId, a.addedAt]));
    const projects: Project[] = allJobs()
      .filter((s) => s.frozen || added.has(s.job.id))
      .map((s) => {
        const job = resolveJob(s);
        return { jobId: job.id, addedAt: s.addedAt ?? added.get(job.id) ?? job.created * 1000, job, state: stateOf(job) };
      })
      .sort((a, b) => b.addedAt - a.addedAt);
    return projects;
  },
  async addProject(jobId) {
    await sleep(150);
    const list = addedIds();
    if (!list.some((a) => a.jobId === jobId)) writeJSON(K.projects, [{ jobId, addedAt: Date.now() }, ...list]);
  },
  async removeProject(jobId) {
    await wait();
    writeJSON(K.projects, addedIds().filter((a) => a.jobId !== jobId));
    writeJSON(K.jobs, readJSON<StoredJob[]>(K.jobs, []).filter((j) => j.job.id !== jobId));
  },

  ...extras,
};
