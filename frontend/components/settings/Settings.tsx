"use client";
import { Card } from "@heroui/react";
import { CircleAlert, CircleCheck, CircleX, Cpu, KeyRound, MonitorCog, ShieldCheck, Sparkles } from "lucide-react";
import { useState } from "react";
import { api, type AiSource, type Config, type DiagItem } from "@/lib/api";
import { cn } from "../ui/cn";
import { useResource } from "@/lib/hooks/useResource";
import { Badge } from "../ui/Badge";
import { Button } from "../ui/Button";
import { Segmented } from "../ui/Controls";
import { Field, inputClass } from "../ui/Field";
import { PageHeader } from "../ui/PageHeader";
import { ErrorState, Skeleton } from "../ui/States";
import { useToast } from "../ui/Toast";

export const AI_LABEL: Record<AiSource, string> = { auto: "Automática", cli: "Mi suscripción de Claude", claude_api: "API de Claude", gemini: "Gemini", incluida: "IA incluida" };
const AI_SUB: Record<AiSource, string> = { auto: "la app elige", cli: "Claude Code", claude_api: "con clave", gemini: "con clave", incluida: "licencia de NovoClip" };

const TIER: Record<string, { tone: "ok" | "warn" | "neutral"; label: string }> = {
  potente: { tone: "ok", label: "Equipo potente" },
  medio: { tone: "warn", label: "Equipo medio" },
  básico: { tone: "neutral", label: "Equipo básico" },
};

/** Ajustes: de dónde viene la IA (incluida o clave propia) y qué usa la app según los componentes del equipo. */
export function Settings() {
  const res = useResource(() => api.getConfig(), []);
  const toast = useToast();
  const [gkey, setGkey] = useState("");
  const [gmodel, setGmodel] = useState<string | null>(null);
  const [akey, setAkey] = useState("");
  const [lic, setLic] = useState("");
  const [saving, setSaving] = useState(false);

  const save = async (s: Parameters<typeof api.saveSettings>[0], ok: string) => {
    setSaving(true);
    try {
      const c = await api.saveSettings(s);
      res.set(c);
      toast(ok);
    } catch (e) {
      toast(e instanceof Error ? e.message : "No se pudo guardar.", "bad");
    } finally {
      setSaving(false);
    }
  };

  if (res.loading)
    return (
      <div>
        <PageHeader title="Ajustes" />
        <Skeleton className="mb-5 h-40" />
        <Skeleton className="h-64" />
      </div>
    );
  if (res.error || !res.data)
    return (
      <div>
        <PageHeader title="Ajustes" />
        <ErrorState message={res.error ?? "Error desconocido"} onRetry={() => res.reload()} />
      </div>
    );

  const c: Config = res.data;
  const p = c.profile;
  const src: AiSource = c.ai_source ?? "auto";
  const tier = p ? (TIER[p.tier] ?? TIER["básico"]) : null;

  return (
    <div>
      <PageHeader title="Ajustes" description="Qué IA usa la app y cómo aprovecha tu equipo." />

      <Diagnostics />

      <Card className="mb-5 gap-4 border border-line p-5 sm:p-6">
        <div className="flex flex-wrap items-center gap-2.5">
          <MonitorCog className="size-5 text-accent-hi" aria-hidden />
          <h2 className="text-lg font-bold">Tu equipo</h2>
          {tier && <Badge tone={tier.tone}>{tier.label}</Badge>}
        </div>
        {p ? (
          <>
            <p className="text-ink-2 [overflow-wrap:anywhere]">{p.summary}</p>
            <dl className="grid gap-3 text-[15px] sm:grid-cols-3">
              <div className="rounded-2xl bg-raised-2 p-3.5">
                <dt className="text-sm text-ink-3">Transcribe con</dt>
                <dd className="mt-0.5 font-bold">{p.transcribe_on}</dd>
              </div>
              <div className="rounded-2xl bg-raised-2 p-3.5">
                <dt className="text-sm text-ink-3">Crea los videos con</dt>
                <dd className="mt-0.5 font-bold">{p.render_on}</dd>
              </div>
              <div className="rounded-2xl bg-raised-2 p-3.5">
                <dt className="text-sm text-ink-3">Precisión elegida</dt>
                <dd className="mt-0.5 font-bold">{p.recommended.whisper_model}</dd>
              </div>
            </dl>
            <p className="text-[13px] text-ink-3">La app lee tu procesador, tu memoria y tu tarjeta gráfica y elige sola lo más rápido que tu equipo aguanta.</p>
          </>
        ) : (
          <p className="text-ink-3">No se pudieron leer los componentes de este equipo.</p>
        )}
      </Card>

      <Card className="gap-5 border border-line p-5 sm:p-6">
        <div className="flex flex-wrap items-center gap-2.5">
          <Sparkles className="size-5 text-accent-hi" aria-hidden />
          <h2 className="text-lg font-bold">Inteligencia artificial</h2>
          <Badge tone={c.ai ? "ok" : "warn"}>{c.ai ? `Activa: ${c.ai_name ?? "IA"}` : "Sin IA: se usa el método básico"}</Badge>
        </div>

        <Segmented<AiSource>
          label="¿Qué IA quieres usar?"
          value={src}
          onChange={(v) => save({ ai_source: v }, `Ahora uso: ${AI_LABEL[v]}.`)}
          options={(Object.keys(AI_LABEL) as AiSource[]).map((k) => ({ value: k, label: AI_LABEL[k], sub: AI_SUB[k] }))}
        />
        <p className={cn("flex items-start gap-2 text-[15px]", c.ai_sources?.[src]?.ok ? "text-ok" : "text-warn")}>
          {c.ai_sources?.[src]?.ok ? <CircleCheck className="mt-0.5 size-4 shrink-0" aria-hidden /> : <CircleAlert className="mt-0.5 size-4 shrink-0" aria-hidden />}
          <span>{c.ai_sources?.[src]?.text}</span>
        </p>

        {src === "cli" && <p className="text-[13px] text-ink-3">Usa Claude Code con la cuenta que tengas iniciada en este equipo (modelo y esfuerzo en NOVOCLIP_CLAUDE_MODEL / NOVOCLIP_CLAUDE_EFFORT). Úsalo solo para tus propios videos: tu suscripción es personal.</p>}

        {src === "incluida" && (
          <div className="flex flex-col gap-3">
            {c.included?.source === "proxy" && (
              <form
                className="flex flex-col gap-2 sm:flex-row sm:items-end"
                onSubmit={(e) => {
                  e.preventDefault();
                  if (lic.trim()) save({ license_key: lic }, "Licencia guardada.").then(() => setLic(""));
                }}
              >
                <Field label="Clave de licencia de NovoClip" className="flex-1" hint={c.license ? "Ya hay una licencia guardada. Pega otra para cambiarla." : undefined}>
                  {(a) => <input {...a} type="password" autoComplete="off" value={lic} onChange={(e) => setLic(e.target.value)} className={inputClass} />}
                </Field>
                <Button type="submit" variant="primary" loading={saving} icon={<KeyRound className="size-4" aria-hidden />}>
                  Activar
                </Button>
              </form>
            )}
          </div>
        )}

        {(src === "gemini" || src === "claude_api" || src === "auto") && (
          <form
            className="flex flex-col gap-4"
            onSubmit={(e) => {
              e.preventDefault();
              save({ ...(gkey.trim() && { gemini_key: gkey }), ...(akey.trim() && { anthropic_key: akey }), gemini_model: gmodel ?? c.gemini_model ?? "" }, "Claves guardadas.").then(() => {
                setGkey("");
                setAkey("");
              });
            }}
          >
            <div className="grid gap-4 sm:grid-cols-2">
              {src !== "claude_api" && (
                <Field label="Clave de Gemini" hint={c.gemini ? "Guardada. Pega otra para cambiarla." : "Gratis en aistudio.google.com/apikey"}>
                  {(a) => <input {...a} type="password" autoComplete="off" value={gkey} onChange={(e) => setGkey(e.target.value)} className={inputClass} />}
                </Field>
              )}
              {src !== "claude_api" && (
                <Field label="Modelo de Gemini" hint="Déjalo así si no sabes cuál poner">
                  {(a) => <input {...a} value={gmodel ?? c.gemini_model ?? ""} onChange={(e) => setGmodel(e.target.value)} placeholder="gemini-flash-latest" className={inputClass} />}
                </Field>
              )}
              {src !== "gemini" && (
                <Field label="Clave de la API de Claude" hint={c.anthropic ? "Guardada. Pega otra para cambiarla." : "console.anthropic.com · se paga aparte"} className="sm:col-span-2">
                  {(a) => <input {...a} type="password" autoComplete="off" value={akey} onChange={(e) => setAkey(e.target.value)} className={inputClass} />}
                </Field>
              )}
            </div>
            <div>
              <Button type="submit" variant="primary" loading={saving} icon={<Cpu className="size-4" aria-hidden />}>
                Guardar claves
              </Button>
            </div>
            <p className="text-[13px] text-ink-3">Las claves se guardan solo en este equipo (archivo config.json) y nunca salen de él, salvo hacia Google o Anthropic cuando se usa la IA.</p>
          </form>
        )}
      </Card>
    </div>
  );
}


const DIAG_ICON = {
  ok: <CircleCheck className="size-5 shrink-0 text-ok" aria-label="Bien" />,
  warn: <CircleAlert className="size-5 shrink-0 text-warn" aria-label="Aviso" />,
  bad: <CircleX className="size-5 shrink-0 text-bad" aria-label="Problema" />,
} as const;

/** Revisa que todo lo necesario esté instalado (FFmpeg, yt-dlp, GPU, IA, conexión con cada red) y dice cómo arreglar lo que falte. */
function Diagnostics() {
  const toast = useToast();
  const [items, setItems] = useState<DiagItem[] | null>(null);
  const [busy, setBusy] = useState(false);

  const run = async () => {
    setBusy(true);
    try {
      setItems(await api.getDiagnostics());
    } catch (e) {
      toast(e instanceof Error ? e.message : "No pude hacer el diagnóstico.", "bad");
    } finally {
      setBusy(false);
    }
  };

  const bad = items?.filter((i) => i.status === "bad").length ?? 0;
  const warn = items?.filter((i) => i.status === "warn").length ?? 0;
  return (
    <Card className="mb-5 gap-4 border border-line p-5 sm:p-6">
      <div className="flex flex-wrap items-center gap-2.5">
        <ShieldCheck className="size-5 text-accent-hi" aria-hidden />
        <h2 className="text-lg font-bold">Diagnóstico</h2>
        {items && <Badge tone={bad ? "bad" : warn ? "warn" : "ok"}>{bad ? `${bad} problema${bad > 1 ? "s" : ""}` : warn ? `${warn} aviso${warn > 1 ? "s" : ""}` : "Todo en orden"}</Badge>}
        <Button size="sm" variant="primary" onClick={run} loading={busy} className="ml-auto">
          {items ? "Revisar otra vez" : "Revisar mi equipo"}
        </Button>
      </div>
      {!items ? (
        <p className="text-ink-2">Comprueba FFmpeg, las descargas, la GPU, la IA y la conexión con YouTube, Twitch, Kick y TikTok. Si algo falla, te dice cómo arreglarlo.</p>
      ) : (
        <ul className="grid gap-2">
          {items.map((i) => (
            <li key={i.id} className="flex items-start gap-3 rounded-2xl bg-raised-2/60 px-4 py-3">
              {DIAG_ICON[i.status]}
              <div className="min-w-0">
                <p className="font-bold">{i.name}</p>
                <p className="text-sm text-ink-2 [overflow-wrap:anywhere]">{i.detail}</p>
                {i.fix && <p className="mt-1 text-[13px] text-ink-3 [overflow-wrap:anywhere]">Cómo arreglarlo: <code className="rounded bg-black/40 px-1.5 py-0.5 text-ink-2">{i.fix}</code></p>}
              </div>
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}
