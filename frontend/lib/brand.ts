import type { FontId, SubtitleStyleId, WatermarkPosition } from "./api/types";

/**
 * ✅ SOPORTADO POR EL BACKEND: los 5 estilos de subtítulos (pipeline.STYLES) + "none".
 * Los colores de abajo son los que usa pipeline.py (STYLES) para cada estilo.
 * ❌ REQUIERE BACKEND NUEVO: fuentes propias, colores propios, logo, marca de agua, guardar plantillas.
 */
export const STYLE_META: Record<SubtitleStyleId, { label: string; hint: string; highlight: string }> = {
  viral: { label: "Viral", hint: "Amarillo con salto en cada palabra", highlight: "#FFE600" },
  caja: { label: "Caja", hint: "Letras sobre una caja negra", highlight: "#00E676" },
  karaoke: { label: "Karaoke", hint: "La palabra activa se ilumina en rosa", highlight: "#FF3DD8" },
  neon: { label: "Neón", hint: "Brillo cian sobre fondo oscuro", highlight: "#00F0FF" },
  minimal: { label: "Minimal", hint: "Texto blanco, sobrio", highlight: "#FFFFFF" },
  none: { label: "Sin subtítulos", hint: "El clip sale sin texto", highlight: "#FFFFFF" },
};

export const STYLE_ORDER: SubtitleStyleId[] = ["viral", "caja", "karaoke", "neon", "minimal", "none"];

/** [BACKEND NUEVO] Tipografías predefinidas. Hoy el backend solo recibe el nombre en `font` (por defecto "Arial Black"). */
export const FONT_META: Record<FontId, { label: string; css: string; weight: number; upper?: boolean }> = {
  "arial-black": { label: "Arial Black (la de siempre)", css: `"Arial Black", var(--font-sans)`, weight: 900 },
  bricolage: { label: "Bricolage · con carácter", css: "var(--font-display)", weight: 800 },
  figtree: { label: "Figtree · limpia y amable", css: "var(--font-sans)", weight: 800 },
  "big-shoulders": { label: "Big Shoulders · alta y fuerte", css: "var(--font-num)", weight: 800, upper: true },
  serif: { label: "Serif · editorial", css: `Georgia, "Times New Roman", serif`, weight: 700 },
};

export const FONT_ORDER: FontId[] = ["arial-black", "bricolage", "figtree", "big-shoulders", "serif"];

export const POSITIONS: { v: WatermarkPosition; label: string }[] = [
  { v: "tl", label: "Arriba izquierda" },
  { v: "tr", label: "Arriba derecha" },
  { v: "center", label: "Centro" },
  { v: "bl", label: "Abajo izquierda" },
  { v: "br", label: "Abajo derecha" },
];

export const ASPECT_META: Record<string, { label: string; sub: string; ratio: string }> = {
  "9:16": { label: "9:16", sub: "TikTok · Reels · Shorts", ratio: "9 / 16" },
  "4:5": { label: "4:5", sub: "Feed de Instagram", ratio: "4 / 5" },
  "1:1": { label: "1:1", sub: "Cuadrado", ratio: "1 / 1" },
  "16:9": { label: "16:9", sub: "Horizontal", ratio: "16 / 9" },
};

export const NETWORK_META = {
  tiktok: { label: "TikTok", short: "TikTok", color: "#25F4EE", will: "Video vertical de hasta 3 minutos, con tu descripción y hashtags." },
  youtube: { label: "YouTube Shorts", short: "Shorts", color: "#FF4E45", will: "Video vertical de menos de 60 segundos; título y descripción del clip." },
  instagram: { label: "Instagram Reels", short: "Reels", color: "#E1306C", will: "Video vertical de hasta 90 segundos, con tu descripción y hashtags." },
} as const;
