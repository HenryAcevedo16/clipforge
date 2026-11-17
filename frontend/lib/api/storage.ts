/** localStorage seguro: puede lanzar o venir vacío (ventana privada, datos bloqueados). Siempre con try/catch. */
export function readJSON<T>(key: string, fallback: T): T {
  try {
    if (typeof window === "undefined") return fallback;
    const raw = window.localStorage.getItem(key);
    return raw ? (JSON.parse(raw) as T) : fallback;
  } catch {
    return fallback;
  }
}

export function writeJSON(key: string, value: unknown): void {
  try {
    if (typeof window === "undefined") return;
    window.localStorage.setItem(key, JSON.stringify(value));
  } catch {
    /* sin espacio o bloqueado: el prototipo sigue funcionando en memoria de la pestaña */
  }
}

export function readString(key: string, fallback = "", store: "local" | "session" = "local"): string {
  try {
    if (typeof window === "undefined") return fallback;
    return (store === "session" ? window.sessionStorage : window.localStorage).getItem(key) ?? fallback;
  } catch {
    return fallback;
  }
}

export function writeString(key: string, value: string, store: "local" | "session" = "local"): void {
  try {
    if (typeof window !== "undefined") (store === "session" ? window.sessionStorage : window.localStorage).setItem(key, value);
  } catch {
    /* ignorar */
  }
}

export const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));
export const uid = (n = 10) => Math.random().toString(36).slice(2, 2 + n).padEnd(n, "0");
