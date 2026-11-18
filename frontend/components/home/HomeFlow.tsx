"use client";
import { Card, Chip, Tabs } from "@heroui/react";
import { ArrowLeft, ArrowRight, Captions, ChevronDown, FileVideo, Film, Link2, Eye, Scissors, Send, Sparkles, Star, Upload, X } from "lucide-react";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";
import { api, ApiError, type AiSource, type BrandTemplate, type ClipResult, type Job, type SubtitleStyleId } from "@/lib/api";
import { readString, writeString } from "@/lib/api/storage";
import { ASPECT_META, FONT_META, STYLE_META, STYLE_ORDER } from "@/lib/brand";
import { useResource } from "@/lib/hooks/useResource";
import { formatDuration } from "@/lib/time";
import { detectPlatform, SUPPORTED_TEXT } from "@/lib/platform";
import { PlatformPill } from "../ui/PlatformPill";
import { ClipEditor } from "../projects/ClipEditor";
import { PublishDialog } from "../projects/PublishDialog";
import { FramingPreview } from "./FramingPreview";
import { ClipPreview } from "../brand/ClipPreview";
import { Button } from "../ui/Button";
import { Segmented, Switch } from "../ui/Controls";
import { cn } from "../ui/cn";
import { Field, inputClass } from "../ui/Field";
import { ErrorState, Skeleton } from "../ui/States";
import { RecentProjects } from "./RecentProjects";
import { ScoreDial } from "../ui/ScoreDial";
import { useToast } from "../ui/Toast";
import { currentStage, friendlyMessage, STAGES } from "@/lib/stages";
import { StageList } from "./StageList";
import { Stepper } from "./Stepper";

const JOB_KEY = "novoclip:home:job";

interface Settings {
  numClips: number;
  minLen: number;
  maxLen: number;
  aspect: string;
  captionStyle: SubtitleStyleId;
  review: boolean;
  templateId: string | null;
  layout: string;
  jumpcuts: boolean;
  zoom: boolean;
  progressBar: boolean;
  colorPop: boolean;
  music: boolean;
  captions: boolean; // subtítulos sí/no
  showHook: boolean; // titular arriba
  highlightKw: boolean; // palabras clave en color
  loudnorm: boolean; // igualar volumen
  useAi: boolean; // elegir momentos con IA
  refine: boolean; // afinar inicio/fin con IA
  completeIdeas: boolean; // que el clip termine cuando la idea queda cerrada
  videoAi: boolean; // la IA ve el video del clip (Gemini)
  snapSilence: boolean; // cortar en silencio natural
  live: boolean;
  liveEvery: number; // minutos entre análisis de la IA en un directo
  smartDownload: boolean;
  quality: "max" | "1080";
  aiProvider: AiSource; // IA para este video (auto = la de Ajustes)
  pick: "ia" | "manual"; // quién elige los cortes
  logoOn: boolean; // poner el logo de la plantilla como marca de agua
}

const DEFAULTS: Settings = {
  numClips: 5, minLen: 20, maxLen: 60, aspect: "9:16", captionStyle: "viral", review: true, templateId: null,
  layout: "auto", jumpcuts: true, zoom: true, progressBar: true, colorPop: true, music: true, captions: true, showHook: true, highlightKw: true, loudnorm: true, useAi: true, refine: true, completeIdeas: true, videoAi: true, snapSilence: true, live: false, liveEvery: 3, smartDownload: true, quality: "max", aiProvider: "auto", pick: "ia", logoOn: true,
};

const AI_NAMES: Record<AiSource, string> = { auto: "Automática", cli: "Mi suscripción de Claude", claude_api: "API de Claude", gemini: "Gemini", incluida: "IA incluida" };

/** "1:23", "01:02:03" o "83" (segundos) -> segundos. null si no se entiende. */
function parseTime(raw: string): number | null {
  const t = raw.trim().replace(",", ".");
  if (!t) return null;
  const parts = t.split(":");
  if (parts.length > 3 || parts.some((x) => x === "" || isNaN(Number(x)))) return null;
  return parts.reduce((acc, x) => acc * 60 + Number(x), 0);
}
const fmtTime = (n: number) => `${Math.floor(n / 60)}:${String(Math.round(n % 60)).padStart(2, "0")}`;

const LAYOUT_OPTIONS = [
  { value: "auto", label: "Automático", sub: "enfoca a quien habla" },
  { value: "split", label: "Dividido", sub: "uno arriba, otro abajo" },
  { value: "wide", label: "Abierto", sub: "casi todo el plano" },
  { value: "track", label: "Seguir la cara" },
  { value: "blur", label: "Completo", sub: "fondo desenfocado" },
];

export function HomeFlow() {
  const router = useRouter();
  const toast = useToast();
  const [step, setStep] = useState(1);
  const [mode, setMode] = useState<"url" | "file">("url");
  const [url, setUrl] = useState("");
  const platform = detectPlatform(url);
  const [file, setFile] = useState<File | null>(null);
  const [srcError, setSrcError] = useState<string | null>(null);
  const [s, setS] = useState<Settings>(DEFAULTS);
  const [formError, setFormError] = useState<string | null>(null);
  const [sending, setSending] = useState(false);
  const [job, setJob] = useState<Job | null>(null);
  const [editing, setEditing] = useState<number | null>(null);
  const [previewing, setPreviewing] = useState(false);
  const [ranges, setRanges] = useState<{ a: string; b: string }[]>([{ a: "", b: "" }]);
  const manual = s.pick === "manual" && !s.live;
  const parsedRanges = ranges.map((r) => ({ a: parseTime(r.a), b: parseTime(r.b) }));
  const refreshJob = useCallback(async () => {
    if (!jobId0.current) return;
    try {
      setJob(await api.getJob(jobId0.current));
    } catch {
      /* se reintenta en el siguiente avance */
    }
  }, []);
  const jobId0 = useRef<string | null>(null);
  const [pollError, setPollError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const config = useResource(() => api.getConfig(), []);
  const templates = useResource(() => api.listTemplates(), []);
  const tpl: BrandTemplate | undefined = templates.data?.find((t) => t.id === s.templateId) ?? undefined;

  // Plantilla predeterminada: se elige sola una vez que cargan las plantillas.
  useEffect(() => {
    if (!templates.data || s.templateId !== null) return;
    const d = templates.data.find((t) => t.isDefault);
    if (d) setS((p) => ({ ...p, templateId: d.id, captionStyle: d.captionStyle }));
  }, [templates.data, s.templateId]);

  // Retomar un trabajo al recargar la página.
  useEffect(() => {
    const id = readString(JOB_KEY, "", "session");
    if (!id) return;
    api.getJob(id).then(
      (j) => {
        setJob(j);
        setStep(j.status === "done" ? 4 : 3);
      },
      () => writeString(JOB_KEY, "", "session"),
    );
  }, []);

  // Consulta el progreso mientras el trabajo está en cola o procesando.
  const jobId = job?.id;
  jobId0.current = jobId ?? null;
  const active = step === 3 && !!jobId && job?.status !== "done" && job?.status !== "error";
  useEffect(() => {
    if (!active || !jobId) return;
    let stop = false;
    let fails = 0;
    const tick = async () => {
      try {
        const j = await api.getJob(jobId);
        if (stop) return;
        fails = 0;
        setPollError(null);
        setJob(j);
        if (j.status === "done") setStep(4);
        if (j.status === "done" || j.status === "error") return;
      } catch (e) {
        fails++;
        if (stop) return;
        setPollError(e instanceof Error ? e.message : "Se perdió la conexión.");
        if (fails >= 6) return;
      }
      setTimeout(tick, 1200);
    };
    const t = setTimeout(tick, 900);
    return () => {
      stop = true;
      clearTimeout(t);
    };
  }, [active, jobId]);

  const pickFile = (f: File | null | undefined) => {
    if (!f) return;
    if (!f.type.startsWith("video/")) {
      setSrcError("Ese archivo no parece un video. Prueba con un .mp4, .mov o .mkv.");
      return;
    }
    setFile(f);
    setMode("file");
    setSrcError(null);
  };

  const goStep2 = () => {
    if (mode === "file") {
      if (!file) return setSrcError("Elige el video que quieres subir.");
    } else {
      const v = url.trim();
      if (!v) return setSrcError(`Pega un link de ${SUPPORTED_TEXT}, o sube un video para continuar.`);
      if (!platform) return setSrcError(`No reconozco ese link. Pega uno de ${SUPPORTED_TEXT} (por ejemplo https://twitch.tv/canal o https://kick.com/canal).`);
    }
    setSrcError(null);
    setStep(2);
  };

  const submit = async () => {
    setFormError(null);
    if (manual) {
      const used = parsedRanges.filter((r, i) => ranges[i].a.trim() || ranges[i].b.trim());
      if (used.length === 0) return setFormError("Pon al menos un clip con su inicio y su fin (por ejemplo 1:20 y 1:55).");
      for (const [i, r] of used.entries()) {
        if (r.a === null || r.b === null) return setFormError(`Clip ${i + 1}: escribe el inicio y el fin como minutos:segundos (1:20) o en segundos (80).`);
        if (r.b - r.a < 1) return setFormError(`Clip ${i + 1}: el fin tiene que ser mayor que el inicio (mínimo 1 segundo).`);
        if (r.b - r.a > 300) return setFormError(`Clip ${i + 1}: dura más de 5 minutos. Los clips cortos funcionan mejor.`);
      }
    } else {
      if (s.minLen < 5 || s.maxLen > 180) return setFormError("Las duraciones deben estar entre 5 y 180 segundos.");
      if (s.minLen >= s.maxLen) return setFormError("La duración mínima debe ser menor que la máxima.");
    }
    setSending(true);
    try {
      const v = url.trim();
      let logo: File | null = null;
      if (s.logoOn && tpl?.logo && tpl.watermark.enabled) {
        try {
          const blob = await (await fetch(tpl.logo.dataUrl)).blob();
          logo = new File([blob], tpl.logo.name || "logo.png", { type: blob.type });
        } catch {
          logo = null;
        }
      }
      const { id } = await api.createJob({
        logo,
        manual_ranges: manual ? JSON.stringify(parsedRanges.filter((r) => r.a !== null && r.b !== null && (r.b as number) - (r.a as number) >= 1).map((r) => [r.a, r.b])) : undefined,
        logo_pos: tpl?.watermark.position,
        logo_size: tpl?.watermark.size,
        logo_opacity: tpl?.watermark.opacity,
        url: mode === "file" ? undefined : /^https?:\/\//i.test(v) ? v : "https://" + v,
        file: mode === "file" ? file : null,
        num_clips: s.numClips,
        min_len: s.minLen,
        max_len: s.maxLen,
        aspect: s.aspect,
        caption_style: s.captions ? s.captionStyle : "none",
        show_hook: s.showHook,
        use_ai: s.useAi,
        highlight_keywords: s.highlightKw,
        loudnorm: s.loudnorm,
        refine: s.refine,
        complete_ideas: s.completeIdeas,
        video_ai: s.videoAi,
        snap_silence: s.snapSilence,
        review: s.review && !!config.data?.ai,
        layout: s.layout,
        jumpcuts: s.jumpcuts,
        zoom: s.zoom,
        progress_bar: s.progressBar,
        color_pop: s.colorPop,
        music: s.music,
        live: s.live && mode === "url",
        live_window: s.liveEvery * 60,
        smart_download: s.smartDownload,
        source_quality: s.quality,
        ai_provider: s.aiProvider,
      });
      writeString(JOB_KEY, id, "session");
      setJob({ id, status: "queued", progress: 0, message: "En cola...", log: [], source: mode === "file" && file ? file.name : v, created: Date.now() / 1000, result: null });
      setPollError(null);
      setStep(3);
    } catch (e) {
      setFormError(e instanceof ApiError || e instanceof Error ? e.message : "No pudimos empezar. Inténtalo de nuevo.");
    } finally {
      setSending(false);
    }
  };

  const reset = () => {
    writeString(JOB_KEY, "", "session");
    setJob(null);
    setUrl("");
    setFile(null);
    setStep(1);
  };

  const sendToProjects = useCallback(
    async (goTo: "project" | "list") => {
      if (!job) return;
      setSaving(true);
      try {
        await api.addProject(job.id);
        writeString(JOB_KEY, "", "session");
        toast(goTo === "project" ? "Listo: tus clips ya están en Mis proyectos." : "Seguimos procesando. Lo verás en Mis proyectos.");
        router.push(goTo === "project" ? `/proyecto/?id=${job.id}` : "/proyectos");
      } catch (e) {
        toast(e instanceof Error ? e.message : "No pudimos guardarlo.", "bad");
        setSaving(false);
      }
    },
    [job, router, toast],
  );

  return (
    <div>
      {step === 1 ? null : (
        <header className="mb-6">
          <h1 className="text-[1.9rem] font-extrabold leading-tight tracking-tight sm:text-[2.25rem]">Crea tus clips</h1>
        </header>
      )}
      {step > 1 && <Stepper step={step} onGo={(n) => (step < 3 ? setStep(n) : undefined)} />}

      {step === 1 && (
        <>
          <section aria-labelledby="h-src" className="hero-aurora anim-rise -mx-4 -mt-6 px-4 pb-4 pt-12 text-center sm:-mx-6 sm:px-6 lg:-mx-10 lg:-mt-10 lg:px-10 lg:pt-20">
            <h1 id="h-src" className="mx-auto max-w-[18ch] text-[2.4rem] font-extrabold leading-[1.05] tracking-tight sm:text-[3.4rem]">
              Convierte un video largo en clips que enganchan
            </h1>
            <p className="mx-auto mt-4 max-w-[52ch] text-base text-ink-2 sm:text-lg">Pega un link de YouTube, Twitch, Kick o TikTok (también directos) o sube un video. Te devolvemos clips verticales con subtítulos y una nota de la IA, listos para publicar.</p>

            <div className="glow-ring mx-auto mt-9 max-w-3xl p-3 text-left sm:p-4">
              <Tabs selectedKey={mode} onSelectionChange={(k) => { setMode(String(k) as "url" | "file"); setSrcError(null); }} className="w-full">
                <Tabs.ListContainer>
                  <Tabs.List aria-label="Cómo quieres darnos el video">
                    <Tabs.Tab id="url">
                      <span className="inline-flex items-center gap-2">
                        <Link2 className="size-4" aria-hidden />
                        Link de video o directo
                      </span>
                      <Tabs.Indicator />
                    </Tabs.Tab>
                    <Tabs.Tab id="file">
                      <span className="inline-flex items-center gap-2">
                        <Upload className="size-4" aria-hidden />
                        Subir video
                      </span>
                      <Tabs.Indicator />
                    </Tabs.Tab>
                  </Tabs.List>
                </Tabs.ListContainer>

                <Tabs.Panel id="url" className="pt-3">
                  <Field label="Link del video" error={srcError} hint={srcError ? undefined : "Funciona con videos y directos de YouTube, Twitch, Kick y TikTok."}>
                    {(p) => (
                      <div className="flex flex-col gap-2 sm:flex-row">
                        <div className="relative min-w-0 flex-1">
                          <Link2 className="pointer-events-none absolute left-4 top-1/2 size-5 -translate-y-1/2 text-ink-3" aria-hidden />
                          <input
                            {...p}
                            type="url"
                            inputMode="url"
                            autoComplete="off"
                            value={url}
                            onChange={(e) => {
                              setUrl(e.target.value);
                              setSrcError(null);
                              const d = detectPlatform(e.target.value);
                              if (d?.kind === "live") setS((prev) => (prev.live ? prev : { ...prev, live: true }));
                              else if (d && platform?.kind === "live") setS((prev) => ({ ...prev, live: false }));
                            }}
                            onKeyDown={(e) => e.key === "Enter" && goStep2()}
                            placeholder="Link de YouTube, Twitch, Kick o TikTok"
                            className={cn(inputClass, "min-h-14 pl-12 text-[17px]", platform && "sm:pr-52")}
                          />
                          {platform && <PlatformPill info={platform} className="pointer-events-none absolute right-3 top-1/2 hidden -translate-y-1/2 sm:inline-flex" />}
                        </div>
                        {platform && <PlatformPill info={platform} className="self-start sm:hidden" />}
                        <Button variant="primary" onClick={goStep2} icon={<Sparkles className="size-4" aria-hidden />} className="min-h-14 px-7 text-base max-sm:w-full">
                          Obtener clips
                        </Button>
                      </div>
                    )}
                  </Field>
                </Tabs.Panel>

                <Tabs.Panel id="file" className="pt-3">
                  {file ? (
                    <div className="flex items-center gap-3 rounded-2xl border border-accent/50 bg-accent-soft p-4">
                      <FileVideo className="size-8 shrink-0 text-accent-hi" aria-hidden />
                      <div className="min-w-0 flex-1">
                        <p className="truncate font-bold">{file.name}</p>
                        <p className="text-sm text-ink-2">{(file.size / 1024 / 1024).toFixed(1)} MB</p>
                      </div>
                      <Button variant="ghost" size="sm" onClick={() => setFile(null)} icon={<X className="size-4" aria-hidden />}>
                        Quitar
                      </Button>
                    </div>
                  ) : (
                    <label
                      onDragOver={(e) => e.preventDefault()}
                      onDrop={(e) => {
                        e.preventDefault();
                        pickFile(e.dataTransfer.files[0]);
                      }}
                      className="group relative flex cursor-pointer flex-col items-center gap-2 rounded-2xl border-2 border-dashed border-line-2 bg-raised-2/40 px-6 py-9 text-center transition-[border-color,background-color] duration-200 hover:border-accent-hi hover:bg-accent-soft focus-within:border-accent-hi focus-within:outline-2 focus-within:outline-offset-2 focus-within:outline-accent-hi"
                    >
                      <input type="file" accept="video/*" className="sr-only" onChange={(e) => pickFile(e.target.files?.[0])} />
                      <span className="brand-bg grid size-12 place-items-center rounded-2xl text-white transition-transform duration-200 ease-[var(--ease-out)] group-hover:-translate-y-0.5">
                        <Upload className="size-6" aria-hidden />
                      </span>
                      <span className="font-bold">Sube un video desde tu equipo</span>
                      <span className="text-sm text-ink-3">Arrástralo aquí o toca para elegirlo (.mp4, .mov, .mkv)</span>
                    </label>
                  )}
                  {srcError && mode === "file" && (
                    <p role="alert" className="mt-2 text-[13px] text-bad">
                      {srcError}
                    </p>
                  )}
                  <div className="mt-3 flex justify-end">
                    <Button variant="primary" onClick={goStep2} icon={<Sparkles className="size-4" aria-hidden />} className="min-h-12 px-7 max-sm:w-full">
                      Obtener clips
                    </Button>
                  </div>
                </Tabs.Panel>
              </Tabs>
            </div>

            <ul className="mx-auto mt-6 flex max-w-3xl flex-wrap justify-center gap-2" aria-label="Qué incluye cada clip">
              {[
                { icon: Captions, t: "Subtítulos animados" },
                { icon: Star, t: "Nota de la IA de 0 a 100" },
                { icon: Film, t: "9:16 · 4:5 · 1:1 · 16:9" },
              ].map(({ icon: I, t }) => (
                <li key={t}>
                  <Chip variant="secondary" size="lg" className="gap-1.5 font-semibold">
                    <I className="size-4" aria-hidden />
                    <Chip.Label>{t}</Chip.Label>
                  </Chip>
                </li>
              ))}
            </ul>
          </section>
          <RecentProjects />
        </>
      )}

      {step === 2 && (
        <div className="grid grid-cols-[minmax(0,1fr)] gap-6 lg:grid-cols-[minmax(0,1fr)_17rem]">
          <section aria-labelledby="h-cfg" className="anim-rise flex flex-col gap-5">
            <h2 id="h-cfg" className="sr-only">
              Personaliza tus clips
            </h2>

            <Card className="flex-row items-center gap-3 border border-line p-4">
              {mode === "file" ? <FileVideo className="size-5 shrink-0 text-ink-2" aria-hidden /> : <Link2 className="size-5 shrink-0 text-ink-2" aria-hidden />}
              {mode === "url" && platform && <PlatformPill info={platform} />}
              <span className="min-w-0 flex-1 truncate text-ink-2">{mode === "file" && file ? file.name : url}</span>
              <button type="button" onClick={() => setStep(1)} className="min-h-10 shrink-0 rounded-xl px-3 font-bold text-accent-hi transition-colors hover:bg-raised-2">
                Cambiar
              </button>
            </Card>

            <Card className="gap-5 border border-line p-5">
              <h3 className="text-lg font-extrabold">Tus clips</h3>
              {!s.live && (
                <Segmented<"ia" | "manual">
                  label="¿Quién elige los cortes?"
                  value={s.pick}
                  onChange={(v) => setS({ ...s, pick: v })}
                  options={[
                    { value: "ia", label: "La IA", sub: "busca los mejores momentos" },
                    { value: "manual", label: "Yo elijo los segundos", sub: "se respetan exactos" },
                  ]}
                />
              )}
              {manual && (
                <div className="flex flex-col gap-3 rounded-2xl border border-line bg-raised-2/40 p-4">
                  <p className="text-sm text-ink-2">Escribe el inicio y el fin de cada clip (por ejemplo <b className="text-ink">1:20</b> a <b className="text-ink">1:55</b>, o en segundos). La app los hace <b className="text-ink">exactamente</b> con esos segundos. Después, en cada clip, puedes pulsar <b className="text-ink">Optimizar con IA</b>.</p>
                  <ul className="flex flex-col gap-2">
                    {ranges.map((r, i) => {
                      const pa = parsedRanges[i].a, pb = parsedRanges[i].b;
                      const bad = (r.a.trim() && pa === null) || (r.b.trim() && pb === null) || (pa !== null && pb !== null && pb - pa < 1);
                      return (
                        <li key={i} className="flex flex-wrap items-end gap-2">
                          <span className="tnum mb-3 w-14 text-sm font-bold text-ink-3">Clip {i + 1}</span>
                          <Field label="Inicio" className="w-28">{(p) => <input {...p} value={r.a} onChange={(e) => setRanges(ranges.map((x, k) => (k === i ? { ...x, a: e.target.value } : x)))} placeholder="1:20" inputMode="text" className={cn(inputClass, bad && "border-bad")} />}</Field>
                          <Field label="Fin" className="w-28">{(p) => <input {...p} value={r.b} onChange={(e) => setRanges(ranges.map((x, k) => (k === i ? { ...x, b: e.target.value } : x)))} placeholder="1:55" inputMode="text" className={cn(inputClass, bad && "border-bad")} />}</Field>
                          <span className="tnum mb-3 min-w-16 text-sm text-ink-2">{pa !== null && pb !== null && pb > pa ? `${fmtTime(pb - pa)} (${Math.round(pb - pa)} s)` : ""}</span>
                          {ranges.length > 1 && (
                            <Button size="sm" variant="ghost" onClick={() => setRanges(ranges.filter((_, k) => k !== i))} icon={<X className="size-4" aria-hidden />} className="mb-1">
                              Quitar
                            </Button>
                          )}
                        </li>
                      );
                    })}
                  </ul>
                  <div>
                    <Button size="sm" onClick={() => setRanges([...ranges, { a: "", b: "" }])} disabled={ranges.length >= 30}>
                      + Añadir otro clip
                    </Button>
                  </div>
                </div>
              )}
              {!manual && (
              <div className="grid gap-5 sm:grid-cols-3">
                <Field label="¿Cuántos clips?" hint="Entre 1 y 30">
                  {(p) => <input {...p} type="number" inputMode="numeric" min={1} max={30} value={s.numClips} onChange={(e) => setS({ ...s, numClips: Math.max(1, Math.min(30, Number(e.target.value) || 1)) })} className={inputClass} />}
                </Field>
                <Field label="Duración mínima (seg)" hint="Desde 5 s">
                  {(p) => <input {...p} type="number" inputMode="numeric" min={5} max={170} value={s.minLen} onChange={(e) => setS({ ...s, minLen: Number(e.target.value) })} className={inputClass} />}
                </Field>
                <Field label="Duración máxima (seg)" hint="Hasta 180 s">
                  {(p) => <input {...p} type="number" inputMode="numeric" min={10} max={180} value={s.maxLen} onChange={(e) => setS({ ...s, maxLen: Number(e.target.value) })} className={inputClass} />}
                </Field>
              </div>
              )}
              <Segmented
                label="Formato"
                value={s.aspect}
                onChange={(v) => setS({ ...s, aspect: v })}
                options={(config.data?.aspects ?? ["9:16", "4:5", "1:1", "16:9"]).map((a) => ({ value: a, label: ASPECT_META[a]?.label ?? a, sub: ASPECT_META[a]?.sub }))}
              />
            </Card>

            <Card className="gap-5 border border-line p-5">
              <h3 className="text-lg font-extrabold">Edición</h3>
              <Segmented label="Encuadre" value={s.layout} onChange={(v) => setS({ ...s, layout: v })} options={LAYOUT_OPTIONS} />
              <div className="flex flex-wrap items-center gap-3 rounded-2xl border border-line bg-raised-2/40 p-3.5">
                <Button size="sm" onClick={() => setPreviewing(true)} icon={<Eye className="size-4" aria-hidden />}>
                  Probar el encuadre (10 s)
                </Button>
                <p className="min-w-0 flex-1 text-[13px] text-ink-3">Mira cómo queda una muestra corta antes de procesar el video entero.</p>
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                <Switch checked={s.jumpcuts} onChange={(v) => setS({ ...s, jumpcuts: v })} label="Quitar silencios" hint="Corta las pausas largas: ritmo más rápido." />
                <Switch checked={s.zoom} onChange={(v) => setS({ ...s, zoom: v })} label="Zoom dinámico" hint="Cambio de plano en cada corte y golpe en las palabras clave." />
                <Switch checked={s.progressBar} onChange={(v) => setS({ ...s, progressBar: v })} label="Barra de progreso" hint="Una barra arriba que invita a ver hasta el final." />
                <Switch checked={s.colorPop} onChange={(v) => setS({ ...s, colorPop: v })} label="Color más vivo" hint="Más contraste, color y nitidez." />
                <Switch checked={s.music} onChange={(v) => setS({ ...s, music: v })} label="Música de fondo" hint="Usa las canciones de la carpeta music/ y baja cuando hablan." />
                <Switch checked={s.loudnorm} onChange={(v) => setS({ ...s, loudnorm: v })} label="Igualar el volumen" hint="Normaliza el audio para que suene parejo en TikTok y Reels." />
                <Switch checked={s.showHook} onChange={(v) => setS({ ...s, showHook: v })} label="Título arriba" hint="Muestra el gancho en la parte de arriba los primeros segundos." />
              </div>
            </Card>

            <Card className="gap-4 border border-line p-5">
              <h3 className="text-lg font-extrabold">Origen del video</h3>
              {mode === "url" && (
                <div className={cn("flex flex-col gap-4 rounded-2xl border p-4 transition-colors", s.live ? "border-accent/50 bg-accent-soft/40" : "border-line")}>
                  <Switch checked={s.live} onChange={(v) => setS({ ...s, live: v })} label="Es un directo en vivo" hint={platform?.kind === "live" ? `Detectado: directo de ${platform.label}. Saca los clips mientras sigue en vivo.` : "Saca los clips mientras el directo sigue. Solo si el enlace está en vivo ahora mismo (YouTube, Twitch, Kick o TikTok)."} />
                  {s.live && (
                    <Segmented<"1" | "3" | "5" | "10">
                      label="La IA busca clips cada"
                      value={String(s.liveEvery) as "1" | "3" | "5" | "10"}
                      onChange={(v) => setS({ ...s, liveEvery: Number(v) })}
                      options={[
                        { value: "1", label: "1 min", sub: "casi al instante" },
                        { value: "3", label: "3 min", sub: "recomendado" },
                        { value: "5", label: "5 min", sub: "equilibrado" },
                        { value: "10", label: "10 min", sub: "menos gasto de IA" },
                      ]}
                    />
                  )}
                </div>
              )}
              <Switch checked={s.smartDownload} onChange={(v) => setS({ ...s, smartDownload: v })} label="Descarga rápida" hint="No baja el video entero: usa los subtítulos o el audio para elegir los clips y baja solo esos trozos." />
              <Segmented<"max" | "1080"> label="Resolución a descargar" value={s.quality} onChange={(v) => setS({ ...s, quality: v })} options={[{ value: "max", label: "La mejor", sub: "hasta 4K · más nítido" }, { value: "1080", label: "Hasta 1080p", sub: "más rápido" }]} />
            </Card>

            <Card className="gap-4 border border-line p-5">
              <h3 className="text-lg font-extrabold">Tu marca</h3>
              <fieldset className="min-w-0">
                <legend className="mb-2 text-sm font-semibold text-ink-2">Plantilla del Kit de marca</legend>
                {templates.loading ? (
                  <Skeleton className="h-16" />
                ) : templates.error ? (
                  <ErrorState title="No pudimos cargar tus plantillas" message={templates.error} onRetry={templates.reload} />
                ) : (templates.data ?? []).length === 0 ? (
                  <p className="rounded-2xl border border-dashed border-line-2 bg-raised-2/40 px-4 py-3.5 text-ink-2">
                    Aún no tienes plantillas. <a href="/marca" className="font-bold text-accent-hi hover:underline">Crea la primera en Kit de marca</a> o sigue con el estilo de abajo.
                  </p>
                ) : (
                  <div className="grid gap-2 sm:grid-cols-2">
                    <label className="relative cursor-pointer">
                      <input type="radio" name="tpl" className="peer sr-only" checked={s.templateId === null} onChange={() => setS({ ...s, templateId: null })} />
                      <span className="flex min-h-16 items-center gap-3 rounded-2xl border border-line bg-raised-2/50 px-4 py-2.5 transition-[border-color,background-color] duration-150 peer-checked:border-accent peer-checked:bg-accent-soft peer-focus-visible:outline-2 peer-focus-visible:outline-accent-hi">
                        <span className="font-bold">Sin plantilla</span>
                        <span className="text-[13px] text-ink-3">usa solo el estilo de abajo</span>
                      </span>
                    </label>
                    {templates.data!.map((t) => (
                      <label key={t.id} className="relative cursor-pointer">
                        <input type="radio" name="tpl" className="peer sr-only" checked={s.templateId === t.id} onChange={() => setS({ ...s, templateId: t.id, captionStyle: t.captionStyle })} />
                        <span className="flex min-h-16 items-center gap-3 rounded-2xl border border-line bg-raised-2/50 px-4 py-2.5 transition-[border-color,background-color,transform] duration-150 active:scale-[0.99] hover:border-line-2 peer-checked:border-transparent peer-checked:bg-accent-soft peer-checked:shadow-[inset_0_0_0_1.5px_var(--accent)] peer-focus-visible:outline-2 peer-focus-visible:outline-offset-2 peer-focus-visible:outline-accent-hi">
                          <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-black text-xs font-extrabold" style={{ color: STYLE_META[t.captionStyle].highlight }} aria-hidden>
                            Aa
                          </span>
                          <span className="min-w-0">
                            <span className="block truncate font-bold">{t.name}</span>
                            <span className="block truncate text-[13px] text-ink-3">
                              {STYLE_META[t.captionStyle].label}
                              {t.isDefault ? " · Predeterminada" : ""}
                            </span>
                          </span>
                        </span>
                      </label>
                    ))}
                  </div>
                )}
              </fieldset>

              {tpl?.logo && tpl.watermark.enabled && (
                <div className="flex items-center gap-3 rounded-2xl border border-line bg-raised-2/40 p-3.5">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src={tpl.logo.dataUrl} alt="" className="size-12 shrink-0 rounded-xl bg-black/40 object-contain p-1" />
                  <div className="min-w-0 flex-1">
                    <Switch checked={s.logoOn} onChange={(v) => setS({ ...s, logoOn: v })} label="Poner mi logo como marca de agua" hint="Sale en todos los clips, en la esquina que elegiste en el Kit de marca." />
                  </div>
                </div>
              )}
              <div className="grid gap-4 sm:grid-cols-2">
                <Switch checked={s.captions} onChange={(v) => setS({ ...s, captions: v })} label="Subtítulos" hint="Apágalo si quieres el clip sin texto en pantalla." />
                <Switch checked={s.highlightKw} onChange={(v) => setS({ ...s, highlightKw: v })} disabled={!s.captions} label="Resaltar palabras clave" hint="Pinta de otro color las palabras importantes." />
              </div>
              <fieldset className={cn("min-w-0 transition-opacity", !s.captions && "pointer-events-none opacity-40")} disabled={!s.captions}>
                <legend className="mb-2 text-sm font-semibold text-ink-2">Estilo de subtítulos</legend>
                <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
                  {(config.data?.styles ?? STYLE_ORDER).map((id) => {
                    const m = STYLE_META[id as SubtitleStyleId];
                    if (!m) return null;
                    return (
                      <label key={id} className="relative cursor-pointer">
                        <input type="radio" name="style" className="peer sr-only" checked={s.captionStyle === id} onChange={() => setS({ ...s, captionStyle: id as SubtitleStyleId })} />
                        <span className="flex min-h-[4.5rem] flex-col justify-center gap-0.5 rounded-2xl border border-line bg-raised-2/50 px-4 py-2 transition-[border-color,background-color,transform] duration-150 active:scale-[0.98] hover:border-line-2 peer-checked:border-transparent peer-checked:bg-accent-soft peer-checked:shadow-[inset_0_0_0_1.5px_var(--accent)] peer-focus-visible:outline-2 peer-focus-visible:outline-offset-2 peer-focus-visible:outline-accent-hi">
                          <span className="font-extrabold" style={id === "none" ? undefined : { color: m.highlight }}>
                            {m.label}
                          </span>
                          <span className="text-xs leading-tight text-ink-3">{m.hint}</span>
                        </span>
                      </label>
                    );
                  })}
                </div>
              </fieldset>

              <details className="group rounded-2xl border border-line bg-raised-2/40 lg:hidden">
                <summary className="flex min-h-12 cursor-pointer list-none items-center justify-between px-4 font-bold [&::-webkit-details-marker]:hidden">
                  Ver vista previa
                  <ChevronDown className="size-4 text-ink-3 transition-transform duration-200 ease-[var(--ease-out)] group-open:rotate-180" aria-hidden />
                </summary>
                <div className="mx-auto w-40 pb-4" aria-hidden>
                  <ClipPreview style={s.captionStyle} fontId={tpl?.fontId} colors={tpl && tpl.captionStyle === s.captionStyle ? tpl.colors : undefined} logo={tpl?.logo?.dataUrl} watermark={tpl?.watermark} className="w-full" />
                </div>
              </details>
            </Card>

            <Card className="gap-4 border border-line p-5">
              <h3 className="text-lg font-extrabold">Inteligencia artificial y cortes</h3>
              {s.useAi && (config.data?.ai_sources ? (
                <Segmented<AiSource>
                  label="IA para este video"
                  value={s.aiProvider}
                  onChange={(v) => setS({ ...s, aiProvider: v })}
                  options={[
                    { value: "auto" as AiSource, label: "Como en Ajustes", sub: config.data.ai_name || "sin IA" },
                    ...(["cli", "claude_api", "gemini", "incluida"] as AiSource[])
                      .filter((k) => config.data!.ai_sources![k]?.ok)
                      .map((k) => ({ value: k, label: AI_NAMES[k] })),
                  ]}
                />
              ) : null)}
              <Switch checked={s.useAi} onChange={(v) => setS({ ...s, useAi: v })} label="Elegir los mejores momentos con IA" hint="Si lo apagas, usa un método básico sin IA (más rápido, menos preciso)." />
              <Switch checked={s.refine} onChange={(v) => setS({ ...s, refine: v })} disabled={!s.useAi} label="Afinar inicio y final con IA" hint="Una segunda pasada para que el clip empiece y termine justo." />
              <Switch checked={s.completeIdeas} onChange={(v) => setS({ ...s, completeIdeas: v })} label="Terminar siempre la idea" hint="El clip no se corta a mitad de frase: si quien habla sigue explicando, se alarga hasta cerrar la idea (sin pasar del máximo)." />
              <Switch checked={s.snapSilence} onChange={(v) => setS({ ...s, snapSilence: v })} label="Cortar en silencios naturales" hint="Evita cortar a mitad de palabra." />
              <Switch
                checked={s.review && !!config.data?.ai}
                disabled={!config.data?.ai}
                onChange={(v) => setS({ ...s, review: v })}
                label="Revisar clips con IA"
                hint={config.data && !config.data.ai ? "La IA no está activada en este servidor, así que los clips saldrán sin nota." : "Cada clip recibe una nota de 0 a 100, con problemas y sugerencias."}
              />
              <Switch checked={s.videoAi && s.review && !!config.data?.ai} disabled={!s.review || !config.data?.ai} onChange={(v) => setS({ ...s, videoAi: v })} label="Que la IA vea el video del clip (con audio)" hint="Con Gemini, la revisión mira y escucha el clip entero y no solo unos fotogramas: detecta mejor cortes bruscos, voz que se corta y encuadres raros. Gasta algo más de cupo. Mejor con un modelo Gemini 4." />
            </Card>

            {formError && (
              <p role="alert" className="rounded-2xl border border-bad/40 bg-bad-soft/60 px-4 py-3 text-bad">
                {formError}
              </p>
            )}

            <div className="flex flex-col-reverse gap-2 sm:flex-row sm:justify-between">
              <Button variant="ghost" onClick={() => setStep(1)} icon={<ArrowLeft className="size-4" aria-hidden />}>
                Atrás
              </Button>
              <Button variant="primary" onClick={submit} loading={sending} icon={<Sparkles className="size-4" aria-hidden />} className="min-h-12 px-7">
                Generar {manual ? Math.max(1, parsedRanges.filter((r, i) => ranges[i].a.trim() || ranges[i].b.trim()).length) : s.numClips} {(manual ? parsedRanges.filter((r, i) => ranges[i].a.trim() || ranges[i].b.trim()).length : s.numClips) === 1 ? "clip" : "clips"}
              </Button>
            </div>
          </section>

          <aside className="hidden lg:block" aria-hidden>
            <p className="mb-2 text-sm font-semibold text-ink-3">Vista previa</p>
            <div className="sticky top-8">
              <ClipPreview style={s.captionStyle} fontId={tpl?.fontId} colors={tpl && tpl.captionStyle === s.captionStyle ? tpl.colors : undefined} logo={tpl?.logo?.dataUrl} watermark={tpl?.watermark} className="w-full" />
            </div>
          </aside>
        </div>
      )}

      {step === 3 && job && (
        <section aria-labelledby="h-prog" className="anim-rise mx-auto max-w-xl">
          <h2 id="h-prog" className="mb-1 text-2xl font-extrabold">
            {job.status === "error" ? "No pudimos terminar este video" : job.status === "queued" ? "Estás en la cola" : "Estamos creando tus clips"}
          </h2>
          <p className="mb-6 text-ink-2">{job.status === "error" ? "Puedes intentarlo de nuevo con otro video o con otros ajustes." : "Puedes dejar esta pantalla: el trabajo sigue y lo verás en Mis proyectos."}</p>

          {pollError && (
            <p role="status" className="mb-4 rounded-2xl border border-warn/30 bg-warn-soft px-4 py-3 text-sm text-warn">
              Perdimos la conexión un momento. Seguimos intentando… ({pollError})
            </p>
          )}

          <Card className="gap-4 border border-line p-5 sm:p-6">
            {job.status !== "error" && (
              <p className="flex items-baseline gap-2 text-ink-2">
                <span className="num text-4xl text-ink">
                  {Math.max(1, currentStage(job) + 1)}
                  <span className="text-ink-3"> / {STAGES.length}</span>
                </span>
                <span className="font-semibold">{job.status === "queued" ? "En cola" : STAGES[Math.max(0, currentStage(job))].label}</span>
              </p>
            )}
            <div aria-live="polite" className="sr-only">
              {friendlyMessage(job.message)}
            </div>
            <StageList job={job} />
          </Card>

          {!!job.result?.clips?.length && (
            <div className="mt-6">
              <h3 className="mb-1 text-lg font-extrabold">Clips que ya están listos</h3>
              <p className="mb-3 text-sm text-ink-2">
                Puedes editarlos mientras se generan los demás{job.result.live ? "" : " (los cambios se aplican cuando termine el trabajo actual)"}.
              </p>
              <ul className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
                {job.result.clips.map((c) => (
                  <ResultThumb key={c.file} jobId={job.id} c={c} onEdit={job.result?.live ? undefined : () => setEditing(c.index)} />
                ))}
              </ul>
            </div>
          )}

          <div className="mt-6 flex flex-col gap-2 sm:flex-row">
            {job.status === "error" ? (
              <>
                <Button variant="primary" onClick={() => { writeString(JOB_KEY, "", "session"); setJob(null); setStep(2); }}>
                  Cambiar los ajustes
                </Button>
                <Button onClick={reset}>Elegir otro video</Button>
              </>
            ) : (
              <Button onClick={() => sendToProjects("list")} loading={saving} icon={<Film className="size-4" aria-hidden />}>
                Seguir en Mis proyectos
              </Button>
            )}
          </div>
        </section>
      )}

      {step === 4 && job?.result && <ResultStep job={job} saving={saving} onSend={() => sendToProjects("project")} onAgain={reset} onEdit={job.result.live ? undefined : setEditing} />}

      {previewing && (
        <FramingPreview
          onClose={() => setPreviewing(false)}
          input={{ url: mode === "url" ? (/^https?:\/\//i.test(url.trim()) ? url.trim() : "https://" + url.trim()) : undefined, file: mode === "file" ? file : null, layout: s.layout, aspect: s.aspect, zoom: s.zoom, jumpcuts: s.jumpcuts, color_pop: s.colorPop, progress_bar: s.progressBar, source_quality: s.quality }}
        />
      )}

      {job && editing !== null && <ClipEditor jobId={job.id} index={editing} onClose={() => setEditing(null)} onChanged={refreshJob} />}
    </div>
  );
}

function ResultStep({ job, saving, onSend, onAgain, onEdit }: { job: Job; saving: boolean; onSend: () => void; onAgain: () => void; onEdit?: (index: number) => void }) {
  const r = job.result!;
  const empty = r.clips.length === 0;
  return (
    <section aria-labelledby="h-res" className="anim-rise">
      <div className="mb-6 flex flex-wrap items-start justify-between gap-4">
        <div className="min-w-0">
          <h2 id="h-res" className="text-2xl font-extrabold [overflow-wrap:anywhere]">
            {empty ? "Terminó, pero no salió ningún clip" : `¡Listo! ${r.clips.length} ${r.clips.length === 1 ? "clip" : "clips"} de «${r.title}»`}
          </h2>
          <p className="mt-1 text-ink-2">{empty ? "No encontramos partes con voz para recortar. Prueba con otro video." : `Video de ${formatDuration(r.source.duration)} · ${r.source.width}×${r.source.height}`}</p>
        </div>
        <div className="flex w-full flex-col gap-2 sm:w-auto sm:flex-row">
          <Button onClick={onAgain}>Procesar otro video</Button>
          <Button variant="primary" onClick={onSend} loading={saving} icon={<Film className="size-4" aria-hidden />}>
            Enviar a Mis proyectos
          </Button>
        </div>
      </div>
      {!empty && (
        <ul className="grid grid-cols-2 gap-3 sm:grid-cols-3 sm:gap-4 lg:grid-cols-5">
          {r.clips.slice(0, 10).map((c) => (
            <ResultThumb key={c.file} jobId={job.id} c={c} onEdit={onEdit ? () => onEdit(c.index) : undefined} />
          ))}
        </ul>
      )}
      {r.clips.length > 10 && <p className="mt-4 text-sm text-ink-3">…y {r.clips.length - 10} más en Mis proyectos.</p>}
    </section>
  );
}

export function ResultThumb({ jobId, c, onEdit }: { jobId: string; c: ClipResult; onEdit?: () => void }) {
  const rev = c.review as { nota?: number };
  const [publishing, setPublishing] = useState(false);
  return (
    <li className="min-w-0">
      <Card className="h-full flex-col gap-0 overflow-hidden border border-line p-0">
        <div className="relative aspect-[9/16] bg-black">
          {c.thumb && (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={api.fileUrl(jobId, c.thumb)} alt="" className="size-full object-cover" loading="lazy" />
          )}
          <span className="tnum absolute bottom-2 right-2 rounded-lg bg-black/70 px-1.5 py-0.5 text-xs font-bold text-white">{formatDuration(c.duration)}</span>
          {typeof rev.nota === "number" && (
            <span className="absolute left-2 top-2">
              <ScoreDial score={rev.nota} size={40} className="rounded-full bg-black/60 backdrop-blur-sm" />
            </span>
          )}
        </div>
        <p className="line-clamp-3 p-3 pb-2 text-[13px] font-semibold leading-snug [overflow-wrap:anywhere]">{c.title}</p>
        <div className="mt-auto flex flex-col gap-1.5 px-3 pb-3">
          <Button size="sm" variant="primary" onClick={() => setPublishing(true)} icon={<Send className="size-4" aria-hidden />} className="w-full">
            Publicar
          </Button>
          {onEdit && (
            <Button size="sm" onClick={onEdit} icon={<Scissors className="size-4" aria-hidden />} className="w-full">
              Editar
            </Button>
          )}
        </div>
        {publishing && <PublishDialog jobId={jobId} clip={c} onClose={() => setPublishing(false)} />}
      </Card>
    </li>
  );
}
