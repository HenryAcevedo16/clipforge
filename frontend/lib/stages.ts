import type { Job } from "./api/types";

/**
 * Etapas REALES del pipeline (pipeline.process()). Los rangos de progreso salen de las llamadas
 * progress(p, msg) en pipeline.py:
 *   download()        progress 1–10   "Descargando video..."
 *   process()         progress 11     "Video: 1920x1080 @ 30fps, 1843s"
 *   transcribe()      progress 12–40  "Cargando modelo Whisper..." / "Transcribiendo... 120s / 1800s"
 *   select_clips()    progress 42–43  "La IA está eligiendo..." / "Analizando energía, ganchos y ritmo..."
 *   render_clip()     progress 45–99  "Clip N: cortando / analizando el encuadre / renderizando k/total"
 *                                      + "Clip N: la IA está revisando el resultado..." (si hay revisión)
 *   process()         progress 100    "¡Listo! N clips generados."
 */
export interface Stage {
  id: "descarga" | "lectura" | "transcripcion" | "momentos" | "clips" | "listo";
  label: string;
  hint: string;
}

export const STAGES: Stage[] = [
  { id: "descarga", label: "Descargar", hint: "Bajamos el video de YouTube" },
  { id: "lectura", label: "Leer el video", hint: "Revisamos tamaño y duración" },
  { id: "transcripcion", label: "Transcribir", hint: "Pasamos lo que se dice a texto" },
  { id: "momentos", label: "Elegir momentos", hint: "Buscamos los mejores fragmentos" },
  { id: "clips", label: "Crear clips", hint: "Encuadre, subtítulos y revisión con IA" },
  { id: "listo", label: "Listo", hint: "Tus clips están preparados" },
];

export type StageState = "done" | "active" | "pending" | "skipped" | "failed";

/** Índice de la etapa en curso (-1 = en cola). */
export function currentStage(job: Pick<Job, "status" | "progress">): number {
  if (job.status === "queued") return -1;
  if (job.status === "done") return STAGES.length - 1;
  const p = job.progress;
  if (p < 11) return 0;
  if (p < 12) return 1;
  if (p < 41) return 2;
  if (p < 45) return 3;
  return 4;
}

export function stageStates(job: Pick<Job, "status" | "progress" | "source">): StageState[] {
  const isUpload = !/^https?:\/\//.test(job.source);
  const cur = currentStage(job);
  return STAGES.map((_, i) => {
    if (i === 0 && isUpload && job.status !== "queued") return "skipped";
    if (job.status === "done") return i === STAGES.length - 1 ? "done" : "done";
    if (job.status === "error") return i < cur ? "done" : i === cur ? "failed" : "pending";
    if (cur === -1) return "pending";
    return i < cur ? "done" : i === cur ? "active" : "pending";
  });
}

/**
 * Traduce los mensajes técnicos que escribe pipeline.py (progress(p, msg)) a español claro, sin jerga.
 * Si no reconoce el mensaje, lo deja tal cual.
 */
export function friendlyMessage(msg: string): string {
  let m: RegExpMatchArray | null;
  if (/^En cola/.test(msg)) return "Esperando tu turno…";
  if (/^Descargando video/.test(msg)) return "Descargando el video…";
  if (/^Leyendo los componentes/.test(msg)) return "Leyendo los componentes de tu equipo…";
  if (/^Tu equipo:/.test(msg)) return "Equipo listo: elegimos la mejor configuración para él.";
  if (/^Leyendo los subtítulos/.test(msg)) return "Leyendo los subtítulos de YouTube (sin descargar el video)…";
  if (/^Listo en segundos/.test(msg)) return "Subtítulos leídos. Ya podemos elegir los momentos.";
  if (/^Descarga rápida|^Descargando el audio/.test(msg)) return "Bajando solo el audio, no el video entero…";
  if ((m = msg.match(/^Clip (\d+): descargando solo ese trozo/))) return `Bajando solo el trozo del clip ${m[1]}…`;
  if ((m = msg.match(/^Clip (\d+): afinando los tiempos/))) return `Afinando los subtítulos del clip ${m[1]}…`;
  if (/^La IA \(.*\) está eligiendo/.test(msg)) return "La IA está eligiendo los mejores momentos…";
  if (/^La IA está afinando/.test(msg)) return "La IA está afinando dónde empieza y termina cada clip…";
  if (/^La IA está identificando/.test(msg)) return "La IA está viendo qué tipo de video es…";
  if (/^Conectando con el directo/.test(msg)) return "Conectando con el directo…";
  if (msg.startsWith("🔴")) return msg.replace(/^🔴\s*/, "En directo: ");
  if ((m = msg.match(/^Video: (\d+)x(\d+) @ [\d.]+fps, (\d+)s/))) {
    const min = Math.round(Number(m[3]) / 60);
    return `Video recibido: dura ${min < 1 ? "menos de 1 minuto" : min === 1 ? "1 minuto" : `${min} minutos`}.`;
  }
  if (/^Cargando modelo Whisper/.test(msg)) return "Preparando la transcripción…";
  if ((m = msg.match(/^Transcribiendo\.\.\. (\d+)s \/ (\d+)s/))) return `Pasando el audio a texto: minuto ${Math.floor(Number(m[1]) / 60)} de ${Math.max(1, Math.ceil(Number(m[2]) / 60))}`;
  if (/^La IA está eligiendo/.test(msg)) return "La IA está eligiendo los mejores momentos…";
  if (/^IA no disponible/.test(msg)) return "La IA no respondió; elegimos los momentos con otro método…";
  if (/^Analizando energía/.test(msg)) return "Buscando los momentos con más fuerza…";
  if ((m = msg.match(/^Clip (\d+): cortando/))) return `Cortando el clip ${m[1]}…`;
  if ((m = msg.match(/^Clip (\d+): analizando el encuadre/))) return `Buscando el mejor encuadre del clip ${m[1]}…`;
  if ((m = msg.match(/^Clip (\d+): webcam detectada/))) return `Clip ${m[1]}: acomodando la cámara y el juego…`;
  if ((m = msg.match(/^Clip (\d+): renderizando/))) return `Dando formato y subtítulos al clip ${m[1]}…`;
  if ((m = msg.match(/^Clip (\d+): la IA está revisando/))) return `La IA está revisando el clip ${m[1]}…`;
  if ((m = msg.match(/^¡Listo! (\d+)/))) return `¡Listo! ${m[1]} ${m[1] === "1" ? "clip generado" : "clips generados"}.`;
  return msg;
}
