/**
 * [REQUIERE BACKEND NUEVO] Kit de marca, cuentas de redes y calendario.
 * El backend actual no tiene nada de esto. Se guarda en localStorage del navegador y se siembra con
 * datos de ejemplo solo en modo simulado. Las cuentas son 100 % ficticias: no hay tokens ni claves.
 */
import { ApiError, type BrandTemplate, type Network, type ScheduledPost, type SchedulePostInput, type SocialAccount } from "./types";
import { readJSON, uid, writeJSON } from "./storage";
import { makeClips } from "./mock-data";
import { fromSD, toSD } from "../time";

export type MockMode = "normal" | "empty" | "error" | "slow" | "extreme";

export interface ExtrasCtx {
  seeded: boolean;
  mode: () => MockMode;
  wait: () => Promise<void>;
}

const K = { templates: "novoclip:v1:templates", accounts: "novoclip:v1:accounts", posts: "novoclip:v1:posts" };

const NET_LABEL: Record<Network, string> = { tiktok: "TikTok", youtube: "YouTube Shorts", instagram: "Instagram Reels" };
export const networkLabel = (n: Network) => NET_LABEL[n];

/** Logo de ejemplo (SVG en data URL) para la plantilla sembrada. */
const SAMPLE_LOGO =
  "data:image/svg+xml;utf8," +
  encodeURIComponent(
    `<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 120 120'><rect width='120' height='120' rx='26' fill='#4466ee'/><path d='M34 84V36h12l28 34V36h12v48H74L46 50v34z' fill='#fff'/></svg>`,
  );

function seedTemplates(mode: MockMode): BrandTemplate[] {
  const now = Date.now();
  const list: BrandTemplate[] = [
    { id: "tpl_clasico", name: "NovoClip clásico", isDefault: true, captionStyle: "viral", fontId: "arial-black", colors: { text: "#FFFFFF", highlight: "#FFE600" }, logo: null, watermark: { enabled: false, position: "br", size: 16, opacity: 80 }, createdAt: now - 9 * 86400000 },
    { id: "tpl_podcast", name: "Podcast Las Cosas Como Son", isDefault: false, captionStyle: "caja", fontId: "bricolage", colors: { text: "#FFFFFF", highlight: "#00E676" }, logo: { name: "logo-lcs.svg", dataUrl: SAMPLE_LOGO }, watermark: { enabled: true, position: "tr", size: 18, opacity: 70 }, createdAt: now - 5 * 86400000 },
    { id: "tpl_neon", name: "Noches de neón", isDefault: false, captionStyle: "neon", fontId: "big-shoulders", colors: { text: "#FFFFFF", highlight: "#00F0FF" }, logo: null, watermark: { enabled: false, position: "bl", size: 14, opacity: 60 }, createdAt: now - 2 * 86400000 },
  ];
  if (mode === "extreme") {
    list.push({ id: "tpl_largo", name: "Plantilla oficial de la campaña de lanzamiento de verano para todos los canales de la marca en español", isDefault: false, captionStyle: "karaoke", fontId: "serif", colors: { text: "#FFFFFF", highlight: "#FF3DD8" }, logo: { name: "logo-con-un-nombre-de-archivo-realmente-largo-para-probar-el-ajuste-final.svg", dataUrl: SAMPLE_LOGO }, watermark: { enabled: true, position: "center", size: 40, opacity: 100 }, createdAt: now });
  }
  return list;
}

function seedAccounts(mode: MockMode): SocialAccount[] {
  const now = Date.now();
  const list: SocialAccount[] = [
    { id: "acc_tt1", network: "tiktok", handle: "@lacosa.rd", displayName: "La Cosa RD", status: "connected", connectedAt: now - 12 * 86400000 },
    { id: "acc_ig1", network: "instagram", handle: "@lacosa.rd", displayName: "La Cosa RD", status: "reconnect", connectedAt: now - 40 * 86400000 },
  ];
  if (mode === "extreme") {
    list.push(
      { id: "acc_tt2", network: "tiktok", handle: "@una_cuenta_con_un_nombre_de_usuario_extremadamente_largo_2026", displayName: "Nombre público larguísimo de una cuenta de prueba que no cabe", status: "connected", connectedAt: now - 86400000 },
      { id: "acc_yt1", network: "youtube", handle: "@LaCosaRD", displayName: "La Cosa RD — Clips", status: "connected", connectedAt: now - 3 * 86400000 },
    );
  }
  return list;
}

function seedPosts(mode: MockMode): ScheduledPost[] {
  const clips = makeClips(6, { review: true });
  const today = toSD(new Date());
  const at = (dayOffset: number, h: number, min = 0) => fromSD(today.y, today.m, today.d + dayOffset, h, min).toISOString();
  const mk = (i: number, id: string, dayOffset: number, h: number, accountIds: string[], status: ScheduledPost["status"], failReason?: string, min = 0): ScheduledPost => ({
    id,
    jobId: "k3m9xq1a7b",
    clipFile: clips[i].file,
    clipTitle: clips[i].title,
    caption: clips[i].caption,
    accountIds,
    at: at(dayOffset, h, min),
    status,
    failReason,
  });
  const list = [
    mk(0, "post_1", -2, 18, ["acc_tt1"], "published"),
    mk(1, "post_2", -1, 12, ["acc_tt1", "acc_ig1"], "failed", "Instagram: la cuenta necesita reconectarse.", 30),
    mk(2, "post_3", 0, 20, ["acc_tt1"], "scheduled"),
    mk(3, "post_4", 1, 9, ["acc_tt1"], "scheduled", undefined, 15),
    mk(4, "post_5", 3, 19, ["acc_tt1"], "scheduled"),
  ];
  if (mode === "extreme") {
    for (let i = 0; i < 12; i++) list.push(mk(i % 6, `post_x${i}`, 0, 6 + i, ["acc_tt1", "acc_yt1"], i % 4 === 0 ? "failed" : "scheduled", i % 4 === 0 ? "No se pudo subir el video." : undefined, (i * 7) % 60));
  }
  return list;
}

function guard(ctx: ExtrasCtx) {
  if (ctx.mode() === "error") throw new ApiError("No pudimos cargar esta sección. Revisa tu conexión e inténtalo de nuevo.", 503);
}

function load<T>(key: string, ctx: ExtrasCtx, seed: (m: MockMode) => T[]): T[] {
  const mode = ctx.mode();
  if (ctx.seeded && mode === "empty") return [];
  const stored = readJSON<T[] | null>(key, null);
  if (stored) {
    // En "extremo" se añaden los datos de prueba extremos sin guardarlos.
    if (ctx.seeded && mode === "extreme") {
      const ids = new Set((stored as unknown as { id: string }[]).map((x) => x.id));
      return [...stored, ...seed("extreme").filter((x) => !ids.has((x as unknown as { id: string }).id))];
    }
    return stored;
  }
  return ctx.seeded ? seed(mode) : [];
}

export function createExtras(ctx: ExtrasCtx) {
  const templates = () => load<BrandTemplate>(K.templates, ctx, seedTemplates);
  const accounts = () => load<SocialAccount>(K.accounts, ctx, seedAccounts);
  const posts = () => load<ScheduledPost>(K.posts, ctx, seedPosts);

  return {
    async listTemplates() {
      await ctx.wait();
      guard(ctx);
      return templates();
    },
    async saveTemplate(t: BrandTemplate) {
      await ctx.wait();
      guard(ctx);
      const list = templates();
      const i = list.findIndex((x) => x.id === t.id);
      let next = i >= 0 ? list.map((x) => (x.id === t.id ? t : x)) : [...list, t];
      // Solo una predeterminada; la primera plantilla creada lo es por defecto.
      if (next.length === 1) next = next.map((x) => ({ ...x, isDefault: true }));
      if (t.isDefault) next = next.map((x) => ({ ...x, isDefault: x.id === t.id }));
      writeJSON(K.templates, next);
      return t;
    },
    async deleteTemplate(id: string) {
      await ctx.wait();
      guard(ctx);
      let next = templates().filter((x) => x.id !== id);
      if (next.length && !next.some((x) => x.isDefault)) next = next.map((x, i) => ({ ...x, isDefault: i === 0 }));
      writeJSON(K.templates, next);
    },
    async setDefaultTemplate(id: string) {
      await ctx.wait();
      guard(ctx);
      writeJSON(K.templates, templates().map((x) => ({ ...x, isDefault: x.id === id })));
    },

    async listAccounts() {
      await ctx.wait();
      guard(ctx);
      return accounts();
    },
    async connectAccount(network: Network) {
      await ctx.wait();
      guard(ctx);
      const list = accounts();
      const n = list.filter((a) => a.network === network).length + 1;
      const acc: SocialAccount = { id: `acc_${uid(6)}`, network, handle: `@tu_cuenta_${network === "youtube" ? "yt" : network === "tiktok" ? "tt" : "ig"}${n > 1 ? n : ""}`, displayName: `Cuenta de ejemplo (${NET_LABEL[network]})`, status: "connected", connectedAt: Date.now() };
      writeJSON(K.accounts, [...list, acc]);
      return acc;
    },
    async reconnectAccount(id: string) {
      await ctx.wait();
      guard(ctx);
      const list = accounts().map((a) => (a.id === id ? { ...a, status: "connected" as const, connectedAt: Date.now() } : a));
      writeJSON(K.accounts, list);
      return list.find((a) => a.id === id)!;
    },
    async disconnectAccount(id: string) {
      await ctx.wait();
      guard(ctx);
      writeJSON(K.accounts, accounts().filter((a) => a.id !== id));
      // Las publicaciones pendientes en esa cuenta se quitan de su lista de destinos.
      writeJSON(
        K.posts,
        posts()
          .map((p) => (p.status === "scheduled" ? { ...p, accountIds: p.accountIds.filter((a) => a !== id) } : p))
          .filter((p) => p.status !== "scheduled" || p.accountIds.length > 0),
      );
    },

    async listPosts() {
      await ctx.wait();
      guard(ctx);
      return posts();
    },
    async schedulePost(input: SchedulePostInput) {
      await ctx.wait();
      guard(ctx);
      if (!input.accountIds.length) throw new ApiError("Elige al menos una red para publicar.");
      if (new Date(input.at).getTime() < Date.now() - 60_000) throw new ApiError("Esa fecha ya pasó. Elige una hora futura.");
      const post: ScheduledPost = { id: `post_${uid(6)}`, ...input, status: "scheduled" };
      writeJSON(K.posts, [...posts(), post]);
      return post;
    },
    async movePost(id: string, at: string) {
      await ctx.wait();
      guard(ctx);
      if (new Date(at).getTime() < Date.now() - 60_000) throw new ApiError("Esa fecha ya pasó. Elige una hora futura.");
      const list = posts().map((p) => (p.id === id ? { ...p, at, status: "scheduled" as const, failReason: undefined } : p));
      writeJSON(K.posts, list);
      return list.find((p) => p.id === id)!;
    },
    async cancelPost(id: string) {
      await ctx.wait();
      guard(ctx);
      writeJSON(K.posts, posts().filter((p) => p.id !== id));
    },
  };
}
