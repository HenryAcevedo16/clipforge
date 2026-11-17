/**
 * Zona horaria de programación: America/Santo_Domingo.
 * República Dominicana no usa horario de verano: el desfase es siempre UTC-4. Por eso se puede pasar
 * entre "hora de RD" y UTC con una suma fija, sin librería de fechas.
 */
export const TZ = "America/Santo_Domingo";
const OFFSET_H = 4; // UTC-4

export interface SDParts {
  y: number;
  m: number; // 0-11
  d: number;
  h: number;
  min: number;
  dow: number; // 0 = domingo
}

/** Descompone un instante en fecha/hora de Santo Domingo. */
export function toSD(date: Date | string | number): SDParts {
  const t = new Date(date).getTime() - OFFSET_H * 3600_000;
  const x = new Date(t);
  return { y: x.getUTCFullYear(), m: x.getUTCMonth(), d: x.getUTCDate(), h: x.getUTCHours(), min: x.getUTCMinutes(), dow: x.getUTCDay() };
}

/** Crea un instante UTC a partir de fecha/hora de Santo Domingo. */
export function fromSD(y: number, m: number, d: number, h = 0, min = 0): Date {
  return new Date(Date.UTC(y, m, d, h + OFFSET_H, min));
}

export const pad = (n: number) => String(n).padStart(2, "0");
export const ymd = (p: Pick<SDParts, "y" | "m" | "d">) => `${p.y}-${pad(p.m + 1)}-${pad(p.d)}`;
export const hm = (p: Pick<SDParts, "h" | "min">) => `${pad(p.h)}:${pad(p.min)}`;

export function nowSD(): SDParts {
  return toSD(new Date());
}

export const MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"];
export const DIAS_CORTOS = ["dom", "lun", "mar", "mié", "jue", "vie", "sáb"];
export const DIAS_LARGOS = ["domingo", "lunes", "martes", "miércoles", "jueves", "viernes", "sábado"];

/** "lun 17 nov · 3:30 p. m." */
export function formatSD(date: Date | string | number): string {
  return new Intl.DateTimeFormat("es-DO", { timeZone: TZ, weekday: "short", day: "numeric", month: "short", hour: "numeric", minute: "2-digit" }).format(new Date(date));
}

export function formatTimeSD(date: Date | string | number): string {
  return new Intl.DateTimeFormat("es-DO", { timeZone: TZ, hour: "numeric", minute: "2-digit" }).format(new Date(date));
}

export function formatDuration(s: number): string {
  const t = Math.max(0, Math.floor(s));
  const h = Math.floor(t / 3600);
  const m = Math.floor((t % 3600) / 60);
  const sec = t % 60;
  return h ? `${h}:${pad(m)}:${pad(sec)}` : `${m}:${pad(sec)}`;
}

/** "hace 5 min", "ayer", "hace 3 d" */
export function timeAgo(ms: number): string {
  const diff = Date.now() - ms;
  const min = Math.round(diff / 60000);
  if (min < 1) return "ahora mismo";
  if (min < 60) return `hace ${min} min`;
  const h = Math.round(min / 60);
  if (h < 24) return `hace ${h} h`;
  const d = Math.round(h / 24);
  if (d === 1) return "ayer";
  return `hace ${d} días`;
}
