/**
 * Datos SIMULADOS. Las formas son las del backend (types.ts, parte 1). Los textos imitan lo que
 * escribiría Claude en select_ai() y review_clip() (pipeline.py).
 */
import type { ClipResult, Job, JobResult, ReviewField } from "./types";

type ClipSeed = Omit<ClipResult, "index" | "start" | "end" | "duration" | "file" | "thumb">;

const ok = (nota: number, resumen: string, sugerencias: string[] = []): ReviewField => ({ aprobado: true, nota, resumen, problemas: [], sugerencias });

export const CLIP_POOL: ClipSeed[] = [
  {
    title: "El error que me costó RD$200,000 en mi primer negocio",
    hook: "Perdí 200 mil en un mes",
    score: 94,
    reason: "Abre con una cifra concreta y una confesión; el remate cierra la idea completa.",
    caption: "Así perdí RD$200,000 por no hacer esto antes de abrir mi negocio. Guárdalo antes de que te pase igual. 👇",
    hashtags: ["#emprender", "#republicadominicana", "#negocios", "#finanzas", "#dominicanos"],
    review: ok(91, "Listo para publicar: gancho fuerte y encuadre estable.", ["Sube un poco el tamaño de los subtítulos en el segundo 12."]),
  },
  {
    title: "Por qué nadie te dice esto sobre emprender en RD",
    hook: "Nadie te lo dice",
    score: 88,
    reason: "Afirmación polémica en los primeros 2 segundos y ejemplo local fácil de reconocer.",
    caption: "Lo que no te cuentan de emprender en República Dominicana (y que yo aprendí a golpes).",
    hashtags: ["#emprendedores", "#rd", "#consejos", "#negocio"],
    review: {
      aprobado: true,
      nota: 78,
      resumen: "Publicable, pero los subtítulos tapan parte de la cara en un momento.",
      problemas: [{ tipo: "subtitulos", gravedad: "media", detalle: "Los subtítulos cubren la barbilla entre los segundos 18 y 24.", segundo: 18 }],
      sugerencias: ["Sube la posición de los subtítulos o usa el estilo «minimal».", "Corta 0.4 s al inicio: hay una pausa antes de la primera palabra."],
    },
  },
  {
    title: "El truco de los 3 segundos para que no te salten el video",
    hook: "Tienes 3 segundos",
    score: 85,
    reason: "Dato accionable, ritmo rápido y ejemplo en pantalla.",
    caption: "Si no enganchas en 3 segundos, te saltan. Mira cómo lo hago yo.",
    hashtags: ["#tiktokrd", "#creadores", "#reels", "#viral"],
    review: {
      aprobado: false,
      nota: 64,
      resumen: "Revisar antes de publicar: empieza a mitad de una frase.",
      problemas: [
        { tipo: "inicio", gravedad: "alta", detalle: "El clip arranca con «…y por eso», sin contexto previo.", segundo: 0 },
        { tipo: "encuadre", gravedad: "media", detalle: "La persona sale cortada por la derecha entre los segundos 31 y 36.", segundo: 31 },
      ],
      sugerencias: ["Mueve el inicio 2.5 s hacia adelante para empezar en «Mira, esto es lo que hago».", "Prueba el encuadre «Completo + fondo» en ese tramo."],
    },
  },
  {
    title: "Mi rutina de grabación con un celular de RD$15,000",
    hook: "Con un celular normal",
    score: 79,
    reason: "Demuestra el proceso paso a paso; cierra con un resultado visible.",
    caption: "No necesitas cámara cara. Esta es mi rutina completa con un celular de RD$15,000.",
    hashtags: ["#contenido", "#creadordecontenido", "#tips", "#celular"],
    review: ok(100, "Impecable: encuadre, subtítulos y gancho sin problemas."),
  },
  {
    title: "Lo que el algoritmo realmente premia",
    hook: "No es lo que piensas",
    score: 72,
    reason: "Contradice una creencia común, aunque el final queda algo abierto.",
    caption: "Spoiler: no son los hashtags. Te explico qué premia el algoritmo hoy.",
    hashtags: ["#algoritmo", "#tiktok", "#crecer"],
    review: {
      aprobado: false,
      nota: 0,
      resumen: "No publicar: el sujeto principal casi no aparece en cuadro.",
      problemas: [
        { tipo: "encuadre", gravedad: "alta", detalle: "La persona queda fuera de cuadro durante casi todo el clip.", segundo: 4 },
        { tipo: "tecnico", gravedad: "alta", detalle: "Hay fotogramas vacíos entre los segundos 20 y 27.", segundo: 20 },
      ],
      sugerencias: ["Vuelve a generar este clip con el encuadre «Seguir la cara».", "Si el video original es de pantalla compartida, usa «Completo + fondo»."],
    },
  },
  {
    title: "Cuánto cobrar por tu primer clip",
    hook: "No cobres menos de esto",
    score: 68,
    reason: "Responde una duda frecuente con números claros.",
    caption: "¿Cuánto cobrar cuando recién empiezas a editar clips? Aquí van mis números reales.",
    hashtags: ["#freelance", "#editor", "#dinero"],
    review: { error: "No se pudo contactar con la IA (tiempo de espera agotado)." },
  },
  {
    title: "La pregunta que cambió mi canal",
    hook: "Una sola pregunta",
    score: 61,
    reason: "Historia personal corta con giro final.",
    caption: "Una sola pregunta cambió cómo hago contenido. ¿La adivinas?",
    hashtags: ["#storytime", "#aprendizaje"],
    review: {},
  },
  {
    title: "Cuando el sponsor no paga: qué hacer",
    hook: "Me dejaron sin pagar",
    score: 55,
    reason: "Tema útil pero el ritmo baja a mitad del clip.",
    caption: "Un sponsor no me pagó. Esto fue lo que hice (y lo que haría distinto).",
    hashtags: ["#marcas", "#colaboraciones", "#influencers"],
    review: {
      aprobado: false,
      nota: 47,
      resumen: "Ritmo lento y final poco claro.",
      problemas: [{ tipo: "final", gravedad: "media", detalle: "Termina a mitad de la idea; falta el remate.", segundo: 48 }],
      sugerencias: ["Alarga el final 4 s para incluir la conclusión.", "Quita la pausa larga del segundo 22."],
    },
  },
];

const ASSET_KEYS = ["a", "b", "c", "d"] as const;

/** Nombre de archivo estilo backend: clip01_titulo.mp4  (ver render_clip). El asset de ejemplo se deduce del nombre. */
export function assetFor(name: string): (typeof ASSET_KEYS)[number] {
  let h = 0;
  for (const ch of name) h = (h * 31 + ch.charCodeAt(0)) >>> 0;
  return ASSET_KEYS[h % ASSET_KEYS.length];
}

function slug(t: string) {
  return t
    .normalize("NFKD")
    .replace(/[^\w\s-]/g, "")
    .trim()
    .toLowerCase()
    .replace(/[\s_-]+/g, "-")
    .slice(0, 40);
}

export function makeClips(n: number, opts: { review: boolean; poolStart?: number; startAt?: number }): ClipResult[] {
  const clips: ClipResult[] = [];
  let cursor = opts.startAt ?? 95;
  for (let i = 0; i < n; i++) {
    const seed = CLIP_POOL[((opts.poolStart ?? 0) + i) % CLIP_POOL.length];
    const cycle = Math.floor(i / CLIP_POOL.length);
    const dur = 24 + ((i * 7) % 33);
    const start = cursor;
    cursor += dur + 40 + ((i * 11) % 50);
    const index = i + 1;
    const title = cycle ? `${seed.title} (parte ${cycle + 1})` : seed.title;
    const base = `clip${String(index).padStart(2, "0")}_${slug(title)}`;
    clips.push({
      ...seed,
      title,
      score: Math.max(1, seed.score - cycle * 3),
      review: opts.review ? seed.review : {},
      index,
      start,
      end: start + dur,
      duration: dur,
      file: `${base}.mp4`,
      thumb: `${base}.jpg`,
    });
  }
  return clips;
}

export function makeResult(title: string, clips: ClipResult[], language: string | null = "es", lengthS = 1843): JobResult {
  return { title, language, source: { width: 1920, height: 1080, fps: 30, duration: lengthS, has_audio: true }, clips };
}

const NOW = () => Date.now() / 1000;

export interface SeedJob {
  job: Job;
  /** Si existe, el trabajo queda congelado en ese estado (no avanza solo). */
  frozen?: boolean;
  addedAt: number;
}

export function seedJobs(): SeedJob[] {
  const now = NOW();
  const url = (id: string) => `https://www.youtube.com/watch?v=${id}`;
  const done = (id: string, src: string, title: string, clips: ClipResult[], ago: number, lengthS?: number): SeedJob => ({
    job: { id, status: "done", progress: 100, message: `¡Listo! ${clips.length} clips generados.`, log: [`¡Listo! ${clips.length} clips generados.`], source: src, created: now - ago, result: makeResult(title, clips, "es", lengthS) },
    frozen: true,
    addedAt: (now - ago + 300) * 1000,
  });
  return [
    done("k3m9xq1a7b", url("dQw4w9WgXcQ"), "Las Cosas Como Son #142 — Emprender en RD sin capital", makeClips(6, { review: true }), 3 * 3600, 5412),
    done("q8v2n5c4dz", url("9bZkp7q19f0"), "Cómo llegué a 100K en TikTok en 90 días (con celular)", makeClips(3, { review: true, poolStart: 4, startAt: 40 }), 26 * 3600, 1260),
    {
      job: { id: "t1w7h6p0ea", status: "running", progress: 58.4, message: "Clip 3: renderizando 140/312 frames", log: ["Descargando video de YouTube...", "Video: 1920x1080 @ 30fps, 2710s", "Cargando modelo Whisper 'small'...", "La IA está eligiendo los mejores momentos...", "Clip 1: la IA está revisando el resultado...", "Clip 2: la IA está revisando el resultado...", "Clip 3: renderizando 140/312 frames"], source: url("kJQP7kiw5Fk"), created: now - 4 * 60, result: null },
      frozen: true,
      addedAt: (now - 4 * 60) * 1000,
    },
    { job: { id: "m4r9d2y6fs", status: "queued", progress: 0, message: "En cola...", log: [], source: url("3JZ_D3ELwOQ"), created: now - 60, result: null }, frozen: true, addedAt: (now - 60) * 1000 },
    {
      job: { id: "z0b8k3j5gx", status: "error", progress: 41, message: "No se encontraron segmentos con voz para recortar.", log: ["Video: 1280x720 @ 30fps, 312s", "Cargando modelo Whisper 'small'...", "Transcribiendo... 312s / 312s"], source: "entrevista_sin_audio.mp4", created: now - 2 * 86400, result: null },
      frozen: true,
      addedAt: (now - 2 * 86400) * 1000,
    },
    done("c7u1l9e3ns", url("L_jWHffIx5E"), "Vlog sin voz — Malecón de noche", [], 5 * 86400, 214),
    done("h5a2f8v6qt", url("fJ9rUzIMcZQ"), "Reacción al partido: Licey vs Águilas", makeClips(1, { review: true, poolStart: 1, startAt: 612 }), 6 * 86400, 3320),
  ];
}

/** Caso extremo para break-ui: títulos larguísimos, 30 clips, notas 0 y 100. */
export function extremeJobs(): SeedJob[] {
  const now = NOW();
  const longTitle =
    "Entrevista completa de más de cuatro horas con el fundador de una cadena de colmados sobre cómo pasó de vender empanadas en la acera de Los Mina a abrir sesenta sucursales en todo el país y por qué nunca pidió un préstamo bancario (con subtítulos en español, inglés y creole)";
  const clips = makeClips(30, { review: true, startAt: 20 });
  clips[0].title = longTitle;
  clips[0].hook = "SUPERCALIFRAGILISTICOESPIALIDOSOEXTREMADAMENTELARGOSINESPACIOS";
  clips[0].hashtags = Array.from({ length: 24 }, (_, i) => `#etiquetamuylarga${i}paraprobarelajuste`);
  return [
    { job: { id: "x1extreme30", status: "done", progress: 100, message: "¡Listo! 30 clips generados.", log: [], source: "https://www.youtube.com/watch?v=extremeLONG", created: now - 3600, result: makeResult(longTitle, clips, "es", 15243) }, frozen: true, addedAt: (now - 3500) * 1000 },
    { job: { id: "x2extremeerr", status: "error", progress: 12, message: `Falló: ffmpeg -v error -ss 0.00 -i /jobs/x2/source.mp4 ...\n${"Error opening input file: moov atom not found. ".repeat(12)}`, log: [], source: "https://www.youtube.com/watch?v=" + "x".repeat(60), created: now - 7200, result: null }, frozen: true, addedAt: (now - 7000) * 1000 },
  ];
}
