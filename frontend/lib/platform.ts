/** Reconoce de qué plataforma es un enlace y si es un directo. Espejo de platform_of / is_live_url del backend. */
export type PlatformId = "youtube" | "twitch" | "kick" | "tiktok";
export type LinkKind = "live" | "video";

export interface PlatformInfo {
  id: PlatformId;
  label: string;
  kind: LinkKind;
  /** Color de marca (para el borde/ícono del pill). */
  color: string;
}

export const PLATFORM_META: Record<PlatformId, { label: string; color: string }> = {
  youtube: { label: "YouTube", color: "#FF3B3B" },
  twitch: { label: "Twitch", color: "#A970FF" },
  kick: { label: "Kick", color: "#53FC18" },
  tiktok: { label: "TikTok", color: "#25F4EE" },
};

export function detectPlatform(raw: string): PlatformInfo | null {
  const v = raw.trim().toLowerCase();
  if (!v) return null;
  const u = v.split("?")[0].replace(/\/+$/, "");
  const host = (u.replace(/^https?:\/\//, "").split("/")[0] || "").replace(/^www\./, "");
  const path = u.replace(/^(https?:\/\/)?[^/]+/, "");
  const has = (d: string) => host === d || host.endsWith("." + d);
  let id: PlatformId | null = null;
  if (has("youtube.com") || host === "youtu.be") id = "youtube";
  else if (has("twitch.tv")) id = "twitch";
  else if (has("kick.com")) id = "kick";
  else if (has("tiktok.com")) id = "tiktok";
  if (!id) return null;
  let live = false;
  if (id === "twitch") live = /^\/[a-z0-9_]+$/.test(path) && !["/directory", "/downloads", "/jobs"].includes(path);
  else if (id === "kick") live = /^\/[a-z0-9_-]+$/.test(path) && !["/categories", "/browse"].includes(path);
  else live = /^\/@[^/]+\/live$/.test(path);
  return { id, ...PLATFORM_META[id], kind: live ? "live" : "video" };
}

export const SUPPORTED_TEXT = "YouTube, Twitch, Kick o TikTok";
