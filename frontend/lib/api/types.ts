/**
 * Formas de datos de NovoClip.
 *
 * ── PARTE 1: YA EXISTE EN EL BACKEND (app.py / pipeline.py) ─────────────────────────────
 * Estas formas son copia exacta de lo que devuelve FastAPI. No inventar campos aquí.
 *   POST /api/jobs      -> { id }
 *   GET  /api/jobs/{id} -> Job
 *   GET  /api/config    -> Config
 *   GET  /files/{job_id}/{name}[?download=1] -> archivo del clip
 *
 * ── PARTE 2: REQUIERE BACKEND NUEVO ─────────────────────────────────────────────────────
 * Proyectos (listado), kit de marca, calendario y cuentas de redes no existen en el backend.
 * Se simulan en el navegador (localStorage) y cada tipo lleva la marca [REQUIERE BACKEND NUEVO].
 */

// ───────────────────────── PARTE 1: backend existente ─────────────────────────

/** GET /api/config  (app.py: config()) */
export interface Config {
  ai: string | boolean | null; // qué IA se usa ("gemini", "proxy", "api"...) o null si no hay
  ai_mode?: "incluida" | "propia";
  ai_source?: AiSource; // la IA elegida en Ajustes
  ai_sources?: Record<AiSource, { ok: boolean; text: string }>; // disponibilidad de cada opción
  ai_name?: string; // texto listo para mostrar: "Gemini · gemini-flash-latest"
  included?: { ok: boolean; source: string | null; text: string };
  license?: boolean;
  anthropic?: boolean;
  gemini?: boolean;
  gemini_model?: string;
  dev?: boolean;
  profile?: HardwareProfile;
  styles: string[]; // list(pipeline.STYLES) + ["none"]
  aspects: string[]; // list(pipeline.ASPECTS)  -> "9:16" | "1:1" | "4:5" | "16:9"
}

/** Lo que la app lee del equipo (system_profile() en pipeline.py). */
export interface HardwareProfile {
  cpu: string;
  threads: number;
  ram_gb: number | null;
  gpu: string | null;
  vram_gb: number | null;
  transcribe_on: string;
  render_on: string;
  tier: "potente" | "medio" | "básico" | string;
  recommended: { whisper_model: string; speed: string; device: string };
  summary: string;
}

/** Estados que escribe app.py: queued -> running -> done | error */
export type JobStatus = "queued" | "running" | "live" | "done" | "error" | "cancelled";

export interface Problem {
  tipo: string; // encuadre | subtitulos | gancho | inicio | final | contenido | tecnico
  gravedad: "alta" | "media" | "baja" | string;
  detalle: string;
  segundo: number | null;
}

/** pipeline.review_clip().model_dump() */
export interface ClipReview {
  aprobado: boolean;
  nota: number; // 0-100
  resumen: string;
  problemas: Problem[];
  sugerencias: string[];
}

/** Clip.review puede venir vacío ({}) si no hubo revisión, o { error } si la IA falló. */
export type ReviewField = ClipReview | { error: string } | Record<string, never>;

/** pipeline.Clip + duration (pipeline.process()) */
export interface ClipResult {
  index: number;
  start: number;
  end: number;
  title: string;
  hook: string;
  score: number; // 0-100 (virality_score)
  reason: string;
  caption: string;
  hashtags: string[];
  file: string;
  thumb: string;
  review: ReviewField;
  duration: number;
  keywords?: string[];
  layout?: string;
  edited?: boolean;
  meta_edited?: boolean; // título/hashtags cambiados a mano
  optimized?: boolean; // la IA optimizó este clip
  opt_note?: string[]; // qué cambió la IA
  opt_prev?: Record<string, unknown> | null; // lo de antes (para deshacer)
  rev?: number; // versión del archivo: cambia cada vez que se vuelve a generar el clip
}

/** pipeline.probe() */
export interface SourceMeta {
  width: number;
  height: number;
  fps: number;
  duration: number;
  has_audio: boolean;
}

/** pipeline.process() -> result */
export interface JobResult {
  title: string;
  language: string | null;
  source: SourceMeta;
  clips: ClipResult[];
  live?: boolean; // directo: los clips van apareciendo
  selection?: { mode: "ia" | "basico" | "manual"; reason: string }; // cómo se eligieron los clips
  partial?: boolean; // todavía hay clips por generar
  total?: number;
}

/** app.py: JOBS[job_id] */
export interface Job {
  id: string;
  status: JobStatus;
  progress: number; // 0-100, lo escribe pipeline con progress(p, msg)
  message: string; // último mensaje; en status "error" trae el texto del error
  log: string[]; // mensajes únicos, máx. 200
  source: string; // url o nombre del archivo
  created: number; // time.time() (segundos)
  result: JobResult | null;
  live?: boolean;
  cancel_requested?: boolean;
}

/** POST /api/jobs (Form). Solo los campos que app.py acepta. */
export interface CreateJobInput {
  url?: string;
  file?: File | null;
  num_clips: number; // 1-30 (el backend lo limita)
  min_len: number;
  max_len: number;
  aspect: string; // 9:16 | 4:5 | 1:1 | 16:9
  caption_style: string; // viral | caja | karaoke | neon | minimal | none
  review: boolean; // "Revisar clips con IA"
  // El resto de campos del backend, con su valor por defecto (layout, words_per_line, font, etc.)
  layout?: string;
  words_per_line?: number;
  font?: string;
  show_hook?: boolean;
  language?: string;
  whisper_model?: string;
  use_ai?: boolean;
  crf?: number;
  // Opciones nuevas del backend
  jumpcuts?: boolean; // quitar silencios
  zoom?: boolean; // zoom dinámico
  progress_bar?: boolean;
  color_pop?: boolean;
  music?: boolean;
  highlight_keywords?: boolean; // resaltar palabras clave en los subtítulos
  logo?: File | null; // Kit de marca: logo que se pone como marca de agua
  logo_pos?: WatermarkPosition;
  logo_size?: number; // % del ancho
  logo_opacity?: number; // %
  manual_ranges?: string; // JSON [[inicio, fin], ...] en segundos: el usuario elige los cortes
  loudnorm?: boolean; // igualar el volumen
  refine?: boolean; // afinar inicio y final con IA
  complete_ideas?: boolean; // que cada clip termine cuando la idea queda cerrada
  video_ai?: boolean; // la IA ve el video del clip (imagen + audio) al revisarlo (solo Gemini)
  snap_silence?: boolean; // cortar en silencios naturales
  live?: boolean; // el enlace es un directo: clips en tiempo real
  live_window?: number;
  smart_download?: boolean; // descarga rápida (solo audio y trozos)
  use_captions?: boolean; // modo instantáneo con subtítulos de YouTube
  source_quality?: "max" | "1080";
  device?: "auto" | "gpu" | "cpu";
  speed?: string;
  ai_provider?: string;
}

/** GET /api/jobs/{id}/clips/{n}: lo que necesita el editor de cortes. */
export interface EditWord {
  w: string;
  s: number;
  e: number;
}
export interface ClipEditData {
  clip: ClipResult;
  words: EditWord[];
  editable: boolean;
  layout: string;
  caption_style: string;
  styles: string[];
  toggles?: ClipToggles;
  show_hook?: boolean;
  has_logo?: boolean; // el trabajo tiene un logo (Kit de marca)
}
/** Interruptores de edición de cada clip. */
export interface ClipToggles {
  zoom: boolean;
  jumpcuts: boolean;
  progress_bar: boolean;
  color_pop: boolean;
  music: boolean;
  highlight_keywords: boolean;
  loudnorm: boolean;
  logo_on: boolean;
}
/** Cambios que se envían al volver a generar un clip. */
export interface ClipEdits {
  start: number;
  end: number;
  title: string;
  hook: string;
  show_hook: boolean;
  caption: string;
  hashtags: string[];
  keywords: string[];
  words: EditWord[];
  layout: string;
  caption_style: string;
  zoom?: boolean;
  jumpcuts?: boolean;
  progress_bar?: boolean;
  color_pop?: boolean;
  music?: boolean;
  highlight_keywords?: boolean;
  loudnorm?: boolean;
  logo_on?: boolean;
}
/** Una comprobación del diagnóstico del equipo. */
export interface DiagItem {
  id: string;
  name: string;
  status: "ok" | "warn" | "bad";
  detail: string;
  fix: string;
}
/** Muestra rápida del encuadre. */
export interface PreviewInput {
  url?: string;
  file?: File | null;
  layout: string;
  aspect: string;
  zoom: boolean;
  jumpcuts: boolean;
  color_pop: boolean;
  progress_bar: boolean;
  source_quality: "max" | "1080";
  at: number; // posición del video (0-1)
}
export type AiSource = "auto" | "cli" | "claude_api" | "gemini" | "incluida";
export interface SettingsInput {
  ai_source?: AiSource;
  ai_mode?: "incluida" | "propia";
  gemini_key?: string;
  gemini_model?: string;
  anthropic_key?: string;
  license_key?: string;
}

/** Error con el formato de FastAPI HTTPException: { detail } */
export class ApiError extends Error {
  status: number;
  constructor(message: string, status = 400) {
    super(message);
    this.status = status;
  }
}

// ───────────────────── PARTE 2: [REQUIERE BACKEND NUEVO] ─────────────────────

/** [REQUIERE BACKEND NUEVO] Estado de un proyecto para filtrar. "empty" = terminó con 0 clips. */
export type ProjectState = "queued" | "running" | "done" | "empty" | "error";

/** [REQUIERE BACKEND NUEVO] Un video procesado. En el backend real solo existe el Job en memoria. */
export interface Project {
  jobId: string;
  addedAt: number; // ms
  job: Job;
  state: ProjectState;
  expiresAt?: number | null; // ms: cuándo se borra solo
}

export type SubtitleStyleId = "viral" | "caja" | "karaoke" | "neon" | "minimal" | "none";

/** [REQUIERE BACKEND NUEVO] Tipografías predefinidas (el backend solo recibe el nombre en `font`). */
export type FontId = "arial-black" | "bricolage" | "figtree" | "big-shoulders" | "serif";

export type WatermarkPosition = "tl" | "tr" | "bl" | "br" | "center";

/**
 * [REQUIERE BACKEND NUEVO] Plantilla del kit de marca.
 * Ya soportado por el backend: SOLO `captionStyle` (los 5 estilos + ninguno -> campo caption_style).
 * NO soportado: logo/marca de agua, tipografía propia, colores propios, guardar plantillas.
 */
export interface BrandTemplate {
  id: string;
  name: string;
  isDefault: boolean;
  captionStyle: SubtitleStyleId; // ✅ existe en el backend
  fontId: FontId; // ❌ backend nuevo
  colors: { text: string; highlight: string }; // ❌ backend nuevo (hoy los colores van fijos por estilo)
  logo: { name: string; dataUrl: string } | null; // ❌ backend nuevo
  watermark: { enabled: boolean; position: WatermarkPosition; size: number; opacity: number }; // ❌
  createdAt: number;
}

export type Network = "tiktok" | "youtube" | "instagram";

/** [REQUIERE BACKEND NUEVO] Cuenta de red. En el prototipo todo es simulado: sin tokens reales. */
export interface SocialAccount {
  id: string;
  network: Network;
  handle: string;
  displayName: string;
  status: "connected" | "reconnect";
  connectedAt: number;
}

export type PostStatus = "scheduled" | "published" | "failed";

/** [REQUIERE BACKEND NUEVO] Publicación programada de un clip. `at` es ISO en UTC. */
export interface ScheduledPost {
  id: string;
  jobId: string;
  clipFile: string;
  clipTitle: string;
  caption: string;
  accountIds: string[];
  at: string;
  status: PostStatus;
  failReason?: string;
}

export interface SchedulePostInput {
  jobId: string;
  clipFile: string;
  clipTitle: string;
  caption: string;
  accountIds: string[];
  at: string;
}

/** Contrato único de la capa de datos: lo implementan lib/api/mock.ts y lib/api/real.ts. */
export interface Api {
  readonly kind: "mock" | "real";
  // ✅ existe en el backend
  getConfig(): Promise<Config>;
  createJob(input: CreateJobInput): Promise<{ id: string }>;
  getJob(id: string): Promise<Job>;
  cancelJob(id: string): Promise<void>;
  saveSettings(s: SettingsInput): Promise<Config>;
  getDiagnostics(): Promise<DiagItem[]>;
  getGeminiModels(): Promise<{ models: { name: string; label: string; description: string; limit: number | null }[]; current: string }>;
  previewFraming(input: PreviewInput): Promise<{ id: string }>;
  getClipEdit(jobId: string, index: number): Promise<ClipEditData>;
  renderClip(jobId: string, index: number, edits: Partial<ClipEdits>): Promise<{ id: string }>;
  deleteClip(jobId: string, index: number): Promise<void>;
  optimizeClip(jobId: string, index: number): Promise<{ id: string }>;
  revertClip(jobId: string, index: number): Promise<{ id: string }>;
  /** Guarda al instante título, descripción y hashtags (sin volver a generar el video). */
  updateClipMeta(jobId: string, index: number, meta: { title?: string; caption?: string; hashtags?: string[] }): Promise<void>;
  fileUrl(jobId: string, name: string, opts?: { download?: boolean }): string;
  // ❌ requiere backend nuevo
  listProjects(): Promise<Project[]>;
  addProject(jobId: string): Promise<void>;
  removeProject(jobId: string): Promise<void>;
  listTemplates(): Promise<BrandTemplate[]>;
  saveTemplate(t: BrandTemplate): Promise<BrandTemplate>;
  deleteTemplate(id: string): Promise<void>;
  setDefaultTemplate(id: string): Promise<void>;
  listAccounts(): Promise<SocialAccount[]>;
  connectAccount(network: Network): Promise<SocialAccount>;
  disconnectAccount(id: string): Promise<void>;
  reconnectAccount(id: string): Promise<SocialAccount>;
  listPosts(): Promise<ScheduledPost[]>;
  schedulePost(input: SchedulePostInput): Promise<ScheduledPost>;
  movePost(id: string, at: string): Promise<ScheduledPost>;
  cancelPost(id: string): Promise<void>;
}
