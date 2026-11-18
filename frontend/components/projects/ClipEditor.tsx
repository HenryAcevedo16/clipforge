"use client";
import { Check, Eraser, Highlighter, Sparkles, Loader2, Scissors, SpellCheck, Trash2 } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import { waitJob } from "@/lib/api/wait";
import { api, ApiError, type ClipEditData, type ClipToggles, type EditWord } from "@/lib/api";
import { formatDuration } from "@/lib/time";
import { Button } from "../ui/Button";
import { Segmented, Switch } from "../ui/Controls";
import { cn } from "../ui/cn";
import { Dialog } from "../ui/Dialog";
import { Field, inputClass } from "../ui/Field";
import { LoadingLabel, Skeleton } from "../ui/States";
import { useToast } from "../ui/Toast";

type Tool = "range" | "fix" | "key";

const TOGGLE_DEFAULTS: ClipToggles = { zoom: true, jumpcuts: true, progress_bar: true, color_pop: true, music: true, highlight_keywords: true, loudnorm: true, logo_on: true };
const TOGGLE_LABELS: { key: keyof ClipToggles; label: string; hint: string }[] = [
  { key: "jumpcuts", label: "Quitar silencios", hint: "Corta las pausas largas." },
  { key: "zoom", label: "Zoom dinámico", hint: "Cambio de plano y golpe en palabras clave." },
  { key: "progress_bar", label: "Barra de progreso", hint: "Barra arriba hasta el final." },
  { key: "color_pop", label: "Color más vivo", hint: "Más contraste y nitidez." },
  { key: "music", label: "Música de fondo", hint: "Baja cuando hablan." },
  { key: "loudnorm", label: "Igualar el volumen", hint: "Audio parejo." },
];

const LAYOUTS = [
  { value: "auto", label: "Automático (quien habla)" },
  { value: "split", label: "Dividido (uno arriba, otro abajo)" },
  { value: "wide", label: "Abierto (casi todo el plano)" },
  { value: "track", label: "Seguir la cara" },
  { value: "blur", label: "Completo con fondo desenfocado" },
  { value: "gaming", label: "Stream: webcam arriba, juego abajo" },
  { value: "gamecenter", label: "Solo el juego" },
];
const STYLE_LABEL: Record<string, string> = { viral: "Viral", caja: "Caja", karaoke: "Karaoke", neon: "Neón", minimal: "Minimal", none: "Sin subtítulos" };

const norm = (w: string) => w.toLowerCase().normalize("NFC").replace(/[^\p{L}\p{N}]/gu, "");
const sec = (s: number) => {
  const m = Math.floor(s / 60);
  return `${m}:${(s - m * 60).toFixed(1).padStart(4, "0")}`;
};

/**
 * Editor de cortes: la transcripción de alrededor del clip, donde se marca el inicio y el final con un clic,
 * se corrigen palabras de los subtítulos y se resaltan las importantes. "Volver a generar" rehace solo ese clip.
 */
export function ClipEditor({ jobId, index, onClose, onChanged }: { jobId: string; index: number; onClose: () => void; onChanged: () => void }) {
  const toast = useToast();
  const [data, setData] = useState<ClipEditData | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [words, setWords] = useState<EditWord[]>([]);
  const [start, setStart] = useState(0);
  const [end, setEnd] = useState(0);
  const [orig, setOrig] = useState<[number, number]>([0, 0]);
  const [next, setNext] = useState<"s" | "e">("s");
  const [tool, setTool] = useState<Tool>("range");
  const [kws, setKws] = useState<Set<string>>(new Set());
  const [fixing, setFixing] = useState<number | null>(null);
  const [fixText, setFixText] = useState("");
  const [title, setTitle] = useState("");
  const [hook, setHook] = useState("");
  const [showHook, setShowHook] = useState(true);
  const [caption, setCaption] = useState("");
  const [tags, setTags] = useState("");
  const [layout, setLayout] = useState("auto");
  const [style, setStyle] = useState("viral");
  const [capOn, setCapOn] = useState(true);
  const [tg, setTg] = useState<ClipToggles>(TOGGLE_DEFAULTS);

  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState("");
  const [pct, setPct] = useState(0);
  const [confirmDel, setConfirmDel] = useState(false);
  const startRef = useRef<HTMLSpanElement | null>(null);
  const alive = useRef(true);

  useEffect(() => {
    alive.current = true;
    return () => {
      alive.current = false;
    };
  }, []);

  const fill = (d: ClipEditData) => {
    const c = d.clip;
    setData(d);
    setWords(d.words.map((w) => ({ ...w })));
    setStart(c.start);
    setEnd(c.end);
    setOrig([c.start, c.end]);
    setNext("s");
    setKws(new Set((c.keywords ?? []).map(norm)));
    setTitle(c.title);
    setHook(c.hook);
    setShowHook(d.show_hook !== false && !!c.hook);
    setCaption(c.caption);
    setTags(c.hashtags.join(" "));
    setLayout(d.layout);
    setStyle(d.caption_style === "none" ? "viral" : d.caption_style);
    setCapOn(d.caption_style !== "none");
    setTg({ ...TOGGLE_DEFAULTS, ...(d.toggles ?? {}) });
  };

  useEffect(() => {
    api.getClipEdit(jobId, index).then(
      (d) => (d.editable ? fill(d) : setError("Este clip no se puede editar: es de una versión anterior o de un directo que no guardó su video. Genera los clips de nuevo.")),
      (e) => setError(e instanceof Error ? e.message : "No pudimos abrir el clip."),
    );
  }, [jobId, index]);

  useEffect(() => {
    startRef.current?.scrollIntoView({ block: "center" });
  }, [data]);

  const lo = words.length ? Math.max(0, Math.floor(words[0].s * 10) / 10) : 0;
  const hi = words.length ? Math.ceil(words[words.length - 1].e * 10) / 10 : 0;
  const first = useMemo(() => words.findIndex((w) => w.e > start + 0.05), [words, start]);
  const last = useMemo(() => words.reduce((acc, w, k) => (w.s < end - 0.2 ? k : acc), -1), [words, end]);

  const pick = (k: number) => {
    const w = words[k];
    if (tool === "fix") {
      setFixing(k);
      setFixText(w.w);
      return;
    }
    if (tool === "key") {
      const n = norm(w.w);
      setKws((p) => {
        const q = new Set(p);
        if (q.has(n)) q.delete(n);
        else q.add(n);
        return q;
      });
      return;
    }
    if (next === "s") {
      const s = Math.max(0, w.s - 0.1);
      setStart(s);
      if (end <= s + 1) setEnd(s + 5);
      setNext("e");
    } else {
      const e = w.e + 0.35;
      if (e > start + 1) {
        setEnd(e);
        setNext("s");
      }
    }
  };

  const applyFix = () => {
    if (fixing === null) return;
    const t = fixText.trim();
    if (t) setWords((p) => p.map((w, k) => (k === fixing ? { ...w, w: t } : w)));
    setFixing(null);
  };

  const nudge = (which: "s" | "e", d: number) => {
    if (which === "s") setStart((s) => Math.max(0, Math.min(end - 1, s + d)));
    else setEnd((e) => Math.max(start + 1, e + d));
  };

  const regenerate = async () => {
    setBusy(true);
    setPct(0);
    setMsg("Enviando…");
    try {
      const { id } = await api.renderClip(jobId, index, {
        start,
        end,
        title,
        hook: showHook ? hook : "",
        show_hook: showHook,
        caption,
        hashtags: tags.split(/\s+/).filter(Boolean),
        keywords: [...kws],
        words,
        layout,
        caption_style: capOn ? style : "none",
        ...tg,
      });
      // El backend rehace el clip en segundo plano: se consulta su avance.
      for (;;) {
        await new Promise((r) => setTimeout(r, 1000));
        if (!alive.current) return;
        const j = await api.getJob(id);
        setPct(j.progress);
        setMsg(j.message);
        if (j.status === "done") break;
        if (j.status === "error") throw new ApiError(j.message || "No se pudo rehacer el clip.");
      }
      const d = await api.getClipEdit(jobId, index);
      fill(d);
      onChanged();
      toast("Clip actualizado. Revísalo en el reproductor.");
    } catch (e) {
      toast(e instanceof Error ? e.message : "No se pudo rehacer el clip.", "bad");
    } finally {
      if (alive.current) setBusy(false);
    }
  };

  const optimize = async () => {
    setBusy(true);
    setPct(0);
    setMsg("La IA está optimizando el clip…");
    try {
      const { id } = await api.optimizeClip(jobId, index);
      await waitJob(id, (p, m) => {
        setPct(p);
        setMsg(m);
      }, () => alive.current);
      if (!alive.current) return;
      fill(await api.getClipEdit(jobId, index));
      onChanged();
      toast("Clip optimizado con IA. Revisa los cambios abajo.");
    } catch (e) {
      toast(e instanceof Error ? e.message : "No se pudo optimizar.", "bad");
    } finally {
      if (alive.current) setBusy(false);
    }
  };

  const saveText = async () => {
    try {
      await api.updateClipMeta(jobId, index, { title, caption, hashtags: tags.split(/\s+/).filter(Boolean) });
      toast("Título, descripción y hashtags guardados.");
      onChanged();
    } catch (e) {
      toast(e instanceof Error ? e.message : "No se pudo guardar.", "bad");
    }
  };

  const remove = async () => {
    if (!confirmDel) {
      setConfirmDel(true);
      setTimeout(() => alive.current && setConfirmDel(false), 4000);
      return;
    }
    try {
      await api.deleteClip(jobId, index);
      toast("Clip eliminado.");
      onChanged();
      onClose();
    } catch (e) {
      toast(e instanceof Error ? e.message : "No se pudo eliminar.", "bad");
    }
  };

  const videoSrc = data ? `${api.fileUrl(jobId, data.clip.file)}${data.clip.rev ? `?v=${data.clip.rev}` : ""}` : "";
  const changed = data && (Math.abs(start - orig[0]) > 0.01 || Math.abs(end - orig[1]) > 0.01);

  return (
    <Dialog
      open
      wide
      onClose={() => !busy && onClose()}
      title={`Editar clip ${index}`}
      footer={
        data ? (
          <>
            <Button variant="danger" onClick={remove} icon={<Trash2 className="size-4" aria-hidden />} disabled={busy}>
              {confirmDel ? "¿Seguro? Pulsa otra vez" : "Eliminar clip"}
            </Button>
            <Button onClick={optimize} disabled={busy} icon={<Sparkles className="size-4" aria-hidden />}>
              Optimizar con IA
            </Button>
            <Button onClick={saveText} disabled={busy} icon={<Check className="size-4" aria-hidden />}>
              Guardar título y hashtags
            </Button>
            <Button variant="primary" onClick={regenerate} loading={busy} icon={<Scissors className="size-4" aria-hidden />}>
              Volver a generar (recorte y efectos)
            </Button>
          </>
        ) : undefined
      }
    >
      {error ? (
        <p role="alert" className="rounded-2xl border border-bad/40 bg-bad-soft/60 p-4 text-ink-2">
          {error}
        </p>
      ) : !data ? (
        <>
          <LoadingLabel text="Abriendo el editor…" />
          <Skeleton className="h-64" />
        </>
      ) : (
        <div className="flex flex-col gap-5">
          {busy && (
            <div role="status" className="rounded-2xl border border-line bg-raised-2 p-3.5 text-sm">
              <div className="mb-2 flex items-center gap-2 font-semibold">
                <Loader2 className="size-4 animate-spin motion-reduce:animate-none" aria-hidden />
                <span className="truncate">{msg || "Trabajando…"}</span>
                <span className="tnum ml-auto text-ink-3">{Math.round(pct)}%</span>
              </div>
              <div className="h-1.5 overflow-hidden rounded-full bg-raised">
                <div className="brand-bg h-full rounded-full transition-[width] duration-500" style={{ width: `${pct}%` }} />
              </div>
            </div>
          )}

          <div className="grid gap-5 sm:grid-cols-[13rem_1fr]">
            <div>
              <video key={videoSrc} src={videoSrc} controls playsInline preload="metadata" className="mx-auto block aspect-[9/16] max-h-[24rem] w-full rounded-2xl bg-black object-contain" aria-label="Así está el clip ahora" />
              <p className="mt-2 text-center text-[13px] text-ink-3">Así está ahora. Al volver a generarlo verás aquí la nueva versión.</p>
            </div>

            <div className="min-w-0">
              <Segmented<Tool>
                label="¿Qué quieres hacer al tocar una palabra?"
                value={tool}
                onChange={setTool}
                options={[
                  { value: "range", label: <span className="flex items-center gap-1.5"><Scissors className="size-4" aria-hidden />Cortar</span>, sub: next === "s" ? "marca el inicio" : "marca el final" },
                  { value: "fix", label: <span className="flex items-center gap-1.5"><SpellCheck className="size-4" aria-hidden />Corregir</span>, sub: "una palabra" },
                  { value: "key", label: <span className="flex items-center gap-1.5"><Highlighter className="size-4" aria-hidden />Resaltar</span>, sub: "palabra clave" },
                ]}
              />
              <p className="tnum mt-3 text-sm text-ink-2">
                Empieza en <b className="text-ink">{sec(start)}</b> · termina en <b className="text-ink">{sec(end)}</b> · dura <b className="text-ink">{formatDuration(end - start)}</b>
                {changed && <span className="ml-2 text-warn">(cambiado)</span>}
              </p>
              {words.length > 0 && (
                <div className="mt-3 grid gap-3 rounded-2xl border border-line bg-raised-2/50 p-3.5 sm:grid-cols-2">
                  <label className="flex flex-col gap-1 text-sm font-semibold text-ink-2">
                    <span className="flex justify-between"><span>Empieza en</span><span className="tnum text-ink">{sec(start)}</span></span>
                    <input type="range" min={lo} max={hi} step={0.1} value={Math.min(start, hi)} onChange={(e) => setStart(Math.max(lo, Math.min(end - 1, Number(e.target.value))))} className="accent-[var(--color-accent-hi)]" aria-label="Inicio del clip" />
                  </label>
                  <label className="flex flex-col gap-1 text-sm font-semibold text-ink-2">
                    <span className="flex justify-between"><span>Termina en</span><span className="tnum text-ink">{sec(end)}</span></span>
                    <input type="range" min={lo} max={hi} step={0.1} value={Math.min(end, hi)} onChange={(e) => setEnd(Math.min(hi, Math.max(start + 1, Number(e.target.value))))} className="accent-[var(--color-accent-hi)]" aria-label="Final del clip" />
                  </label>
                </div>
              )}
              <div className="mt-2 flex flex-wrap items-center gap-1.5 text-sm">
                <span className="text-ink-3">Inicio</span>
                <Button size="sm" onClick={() => nudge("s", -0.5)}>−0,5 s</Button>
                <Button size="sm" onClick={() => nudge("s", 0.5)}>+0,5 s</Button>
                <span className="ml-2 text-ink-3">Fin</span>
                <Button size="sm" onClick={() => nudge("e", -0.5)}>−0,5 s</Button>
                <Button size="sm" onClick={() => nudge("e", 0.5)}>+0,5 s</Button>
                <Button size="sm" variant="ghost" onClick={() => { setStart(orig[0]); setEnd(orig[1]); setNext("s"); }} icon={<Eraser className="size-4" aria-hidden />}>
                  Deshacer corte
                </Button>
              </div>

              {fixing !== null && (
                <form
                  className="mt-3 flex gap-2"
                  onSubmit={(e) => {
                    e.preventDefault();
                    applyFix();
                  }}
                >
                  <input autoFocus value={fixText} onChange={(e) => setFixText(e.target.value)} aria-label="Corregir palabra" className={cn(inputClass, "min-h-11")} />
                  <Button type="submit" variant="primary" size="sm">Aplicar</Button>
                  <Button size="sm" onClick={() => setFixing(null)}>Cancelar</Button>
                </form>
              )}

              <div className="mt-3 max-h-72 overflow-auto rounded-2xl border border-line bg-raised-2/60 p-3 leading-[2.15] text-[15px]" aria-label="Transcripción alrededor del clip">
                {words.length === 0 && <p className="text-ink-3">No hay transcripción guardada para este clip.</p>}
                {words.map((w, k) => {
                  const newLine = k === 0 || w.s - words[k - 1].e > 0.8;
                  const inside = k >= first && k <= last;
                  return (
                    <span key={k}>
                      {newLine && (
                        <>
                          {k > 0 && <br />}
                          <span className="tnum mr-1.5 text-[11px] text-ink-3 select-none">{sec(w.s)}</span>
                        </>
                      )}
                      <span
                        ref={k === first ? startRef : undefined}
                        role="button"
                        tabIndex={0}
                        onClick={() => pick(k)}
                        onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && (e.preventDefault(), pick(k))}
                        className={cn(
                          "cursor-pointer rounded px-0.5 transition-colors hover:bg-white/10",
                          inside ? "text-ink" : "text-ink-3",
                          kws.has(norm(w.w)) && "font-bold text-warn",
                          k === first && "bg-ok/25 text-ink shadow-[-3px_0_0_var(--color-ok)]",
                          k === last && "bg-bad/25 text-ink shadow-[3px_0_0_var(--color-bad)]",
                        )}
                      >
                        {w.w}
                      </span>{" "}
                    </span>
                  );
                })}
              </div>
              <p className="mt-2 text-[13px] text-ink-3">Verde = empieza · Rojo = termina · Naranja = palabra resaltada en los subtítulos.</p>
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <Field label="Título">{(a) => <input {...a} value={title} onChange={(e) => setTitle(e.target.value)} className={inputClass} />}</Field>
            <div className="flex flex-col gap-2">
              <Field label="Titular de arriba (gancho)">{(a) => <input {...a} value={hook} onChange={(e) => setHook(e.target.value)} disabled={!showHook} className={inputClass} />}</Field>
              <Switch checked={showHook} onChange={setShowHook} label="Mostrar el titular en el video" />
            </div>
            <Field label="Encuadre">
              {(a) => (
                <select {...a} value={layout} onChange={(e) => setLayout(e.target.value)} className={cn(inputClass, "pr-8")}>
                  {LAYOUTS.map((l) => (
                    <option key={l.value} value={l.value}>{l.label}</option>
                  ))}
                </select>
              )}
            </Field>
            <div className="flex flex-col gap-2">
              <Field label="Estilo de subtítulos">
                {(a) => (
                <select {...a} value={style} onChange={(e) => setStyle(e.target.value)} disabled={!capOn} className={cn(inputClass, "pr-8")}>
                  {data.styles.filter((s) => s !== "none").map((s) => (
                    <option key={s} value={s}>{STYLE_LABEL[s] ?? s}</option>
                  ))}
                </select>
                )}
              </Field>
              <Switch checked={capOn} onChange={setCapOn} label="Mostrar subtítulos" />
            </div>
            <fieldset className="sm:col-span-2">
              <legend className="mb-2 text-sm font-semibold text-ink-2">Efectos de este clip (apaga los que no quieras)</legend>
              <div className="grid gap-3 sm:grid-cols-2">
                <Switch checked={tg.highlight_keywords} onChange={(v) => setTg({ ...tg, highlight_keywords: v })} disabled={!capOn} label="Resaltar palabras clave" hint="Color en las palabras importantes." />
                {data.has_logo && <Switch checked={tg.logo_on} onChange={(v) => setTg({ ...tg, logo_on: v })} label="Mostrar mi logo" hint="La marca de agua del Kit de marca." />}
                {TOGGLE_LABELS.map((t) => (
                  <Switch key={t.key} checked={tg[t.key]} onChange={(v) => setTg({ ...tg, [t.key]: v })} label={t.label} hint={t.hint} />
                ))}
              </div>
            </fieldset>
            <Field label="Descripción para publicar" className="sm:col-span-2">{(a) => <textarea {...a} value={caption} onChange={(e) => setCaption(e.target.value)} rows={3} className={cn(inputClass, "py-3")} />}</Field>
            <Field label="Hashtags" hint="Separados por espacios" className="sm:col-span-2">{(a) => <input {...a} value={tags} onChange={(e) => setTags(e.target.value)} className={inputClass} />}</Field>
          </div>
        </div>
      )}
    </Dialog>
  );
}
