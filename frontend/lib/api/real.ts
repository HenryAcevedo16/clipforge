/**
 * Implementación REAL (NEXT_PUBLIC_USE_MOCK=false): habla con el backend FastAPI.
 * El navegador llama a /api/* y /files/* en el mismo origen; next.config.ts los reenvía a BACKEND_URL
 * (así no hace falta CORS). Ver PENDIENTES-BACKEND.md.
 *
 * Solo la PARTE 1 de types.ts es real. Lo demás sigue en localStorage hasta que exista backend nuevo.
 */
import { ApiError, type Api, type ClipEditData, type Config, type CreateJobInput, type Job, type Project, type ProjectState } from "./types";
import { createExtras } from "./extras";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(path, init);
  } catch {
    throw new ApiError("No pudimos conectar con el servidor. Revisa que NovoClip esté encendido e inténtalo de nuevo.", 0);
  }
  if (!res.ok) {
    let detail = `Error ${res.status}`;
    try {
      const body = await res.json();
      // FastAPI: { detail: "texto" } para HTTPException, { detail: [...] } para validación (422)
      detail = typeof body.detail === "string" ? body.detail : "Alguno de los datos enviados no es válido.";
    } catch {
      /* respuesta sin JSON */
    }
    throw new ApiError(detail, res.status);
  }
  return res.json() as Promise<T>;
}

function normalize(job: Job): Job {
  // "live" (directo en marcha) se muestra como "running"; "cancelled" como error con su mensaje.
  if (job.status === "live") return { ...job, status: "running" };
  if (job.status === "cancelled") return { ...job, status: "error", message: job.message || "Se canceló la generación." };
  return job;
}
function stateOf(job: Job): ProjectState {
  if (job.status === "done") return job.result && job.result.clips.length === 0 ? "empty" : "done";
  return job.status === "running" || job.status === "queued" ? job.status : "error";
}

const extras = createExtras({ seeded: false, mode: () => "normal", wait: async () => {} });

export const realApi: Api = {
  kind: "real",

  getConfig: () => request<Config>("/api/config"),
  getDiagnostics: () => request("/api/diagnostics"),
  getGeminiModels: () => request("/api/gemini/models"),
  previewFraming(input) {
    const fd = new FormData();
    if (input.url) fd.set("url", input.url);
    if (input.file) fd.set("file", input.file);
    for (const k of ["layout", "aspect", "zoom", "jumpcuts", "color_pop", "progress_bar", "source_quality", "at"] as const) fd.set(k, String(input[k]));
    return request<{ id: string }>("/api/preview", { method: "POST", body: fd });
  },

  createJob(input: CreateJobInput) {
    const fd = new FormData();
    if (input.url) fd.set("url", input.url.trim());
    if (input.file) fd.set("file", input.file);
    // Los nombres y valores son los de app.py: create_job(...)
    fd.set("num_clips", String(input.num_clips));
    fd.set("min_len", String(input.min_len));
    fd.set("max_len", String(input.max_len));
    fd.set("aspect", input.aspect);
    fd.set("caption_style", input.caption_style);
    fd.set("review", String(input.review));
    for (const k of ["layout", "words_per_line", "font", "show_hook", "language", "whisper_model", "use_ai", "crf", "jumpcuts", "zoom", "progress_bar", "color_pop", "music", "highlight_keywords", "loudnorm", "logo_pos", "logo_size", "logo_opacity", "manual_ranges", "refine", "complete_ideas", "video_ai", "snap_silence", "live", "live_window", "smart_download", "use_captions", "source_quality", "device", "speed", "ai_provider"] as const) {
      const v = input[k];
      if (v !== undefined) fd.set(k, String(v));
    }
    if (input.logo) fd.set("logo", input.logo);
    return request<{ id: string }>("/api/jobs", { method: "POST", body: fd });
  },

  async getJob(id) {
    return normalize(await request<Job>(`/api/jobs/${encodeURIComponent(id)}`));
  },

  async cancelJob(id) {
    await request(`/api/jobs/${encodeURIComponent(id)}/cancel`, { method: "POST" });
  },

  saveSettings(s) {
    const fd = new FormData();
    for (const [k, v] of Object.entries(s)) if (v !== undefined) fd.set(k, String(v));
    return request<Config>("/api/settings", { method: "POST", body: fd });
  },

  getClipEdit: (jobId, index) => request<ClipEditData>(`/api/jobs/${encodeURIComponent(jobId)}/clips/${index}`),

  renderClip: (jobId, index, edits) =>
    request<{ id: string }>(`/api/jobs/${encodeURIComponent(jobId)}/clips/${index}/render`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(edits),
    }),

  optimizeClip: (jobId, index) => request(`/api/jobs/${encodeURIComponent(jobId)}/clips/${index}/optimize`, { method: "POST" }),
  revertClip: (jobId, index) => request(`/api/jobs/${encodeURIComponent(jobId)}/clips/${index}/revert`, { method: "POST" }),
  async updateClipMeta(jobId, index, meta) {
    await request(`/api/jobs/${encodeURIComponent(jobId)}/clips/${index}/meta`, { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify(meta) });
  },
  async deleteClip(jobId, index) {
    await request(`/api/jobs/${encodeURIComponent(jobId)}/clips/${index}`, { method: "DELETE" });
  },

  fileUrl: (jobId, name, opts) => `/files/${encodeURIComponent(jobId)}/${encodeURIComponent(name)}${opts?.download ? "?download=1" : ""}`,

  // Proyectos: el backend los guarda en disco y los lista.
  async listProjects() {
    const list = await request<Project[]>("/api/projects");
    return list.map((p) => {
      const job = normalize(p.job);
      return { ...p, job, state: stateOf(job) };
    });
  },
  async addProject() {
    /* ya se guardan solos */
  },
  async removeProject(jobId) {
    await request(`/api/jobs/${encodeURIComponent(jobId)}`, { method: "DELETE" });
  },

  ...extras,
};
