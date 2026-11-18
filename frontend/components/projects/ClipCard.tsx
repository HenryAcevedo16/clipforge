"use client";
import { Card } from "@heroui/react";
import { CalendarClock, Check, ChevronDown, Copy, Download, Pencil, Scissors, Send, TriangleAlert } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { api, type ClipResult, type ClipReview } from "@/lib/api";
import { formatDuration } from "@/lib/time";
import { Badge } from "../ui/Badge";
import { Button, buttonClass } from "../ui/Button";
import { cn } from "../ui/cn";
import { ScoreDial, scoreTone } from "../ui/ScoreDial";
import { useToast } from "../ui/Toast";
import { PublishDialog } from "./PublishDialog";

function isReview(r: ClipResult["review"]): r is ClipReview {
  return typeof (r as ClipReview).nota === "number";
}

const GRAV: Record<string, { tone: "bad" | "warn" | "neutral"; label: string }> = {
  alta: { tone: "bad", label: "Grave" },
  media: { tone: "warn", label: "Medio" },
  baja: { tone: "neutral", label: "Leve" },
};
const TIPO: Record<string, string> = { encuadre: "Encuadre", subtitulos: "Subtítulos", gancho: "Gancho", inicio: "Inicio", final: "Final", contenido: "Contenido", tecnico: "Técnico" };

/** Nota de la IA: número 0–100, veredicto, problemas y sugerencias. Maneja los 3 casos del backend: con nota, con error, vacía. */
export function ReviewPanel({ review }: { review: ClipResult["review"] }) {
  const [open, setOpen] = useState(false);
  if ("error" in review && typeof review.error === "string") {
    return (
      <div className="flex items-start gap-2.5 rounded-2xl border border-warn/30 bg-warn-soft px-4 py-3 text-sm text-warn">
        <TriangleAlert className="mt-0.5 size-4 shrink-0" aria-hidden />
        <p className="[overflow-wrap:anywhere]">La revisión con IA no estuvo disponible para este clip. {review.error}</p>
      </div>
    );
  }
  if (!isReview(review)) {
    return <p className="rounded-2xl border border-dashed border-line-2 px-4 py-3 text-sm text-ink-3">Este clip no tiene revisión de IA.</p>;
  }
  const items = review.problemas.length + review.sugerencias.length;
  // El veredicto sigue a la nota: lo que la IA llama "aprobado" no puede contradecir un 0 en rojo.
  const tone = scoreTone(review.nota);
  const verdict = tone === "bad" ? { tone: "bad" as const, label: "No publicar" } : tone === "ok" && review.aprobado ? { tone: "ok" as const, label: "Listo para publicar" } : { tone: "warn" as const, label: "Revisar antes de publicar" };
  return (
    <div className="rounded-2xl border border-line bg-raised-2/50">
      <div className="flex items-center gap-3.5 p-3.5">
        <ScoreDial score={review.nota} size={56} />
        <div className="min-w-0 flex-1">
          <Badge tone={verdict.tone} icon={verdict.tone === "ok" ? <Check className="size-3" strokeWidth={3} aria-hidden /> : <TriangleAlert className="size-3" aria-hidden />}>
            {verdict.label}
          </Badge>
          <p className="mt-1.5 text-sm leading-snug text-ink-2 [overflow-wrap:anywhere]">{review.resumen}</p>
        </div>
      </div>
      {items > 0 && (
        <>
          <button type="button" onClick={() => setOpen(!open)} aria-expanded={open} className="flex min-h-11 w-full items-center justify-between rounded-b-2xl border-t border-line px-4 text-sm font-bold text-accent-hi transition-colors hover:bg-raised-2">
            {open ? "Ocultar detalles" : `Ver ${review.problemas.length ? `${review.problemas.length} ${review.problemas.length === 1 ? "problema" : "problemas"}` : ""}${review.problemas.length && review.sugerencias.length ? " y " : ""}${review.sugerencias.length ? `${review.sugerencias.length} ${review.sugerencias.length === 1 ? "sugerencia" : "sugerencias"}` : ""}`}
            <ChevronDown className={cn("size-4 transition-transform duration-200 ease-[var(--ease-out)]", open && "rotate-180")} aria-hidden />
          </button>
          <div className={cn("grid transition-[grid-template-rows] duration-250 ease-[var(--ease-out)]", open ? "grid-rows-[1fr]" : "grid-rows-[0fr]")}>
            <div className="overflow-hidden" inert={!open || undefined}>
              <div className="flex flex-col gap-3 border-t border-line p-4 text-sm">
                {review.problemas.length > 0 && (
                  <ul className="flex flex-col gap-2.5">
                    {review.problemas.map((p, i) => {
                      const g = GRAV[p.gravedad] ?? GRAV.baja;
                      return (
                        <li key={i} className="flex flex-col gap-1">
                          <div className="flex flex-wrap items-center gap-1.5">
                            <Badge tone={g.tone}>{g.label}</Badge>
                            <span className="font-bold">{TIPO[p.tipo] ?? p.tipo}</span>
                            {p.segundo != null && <span className="tnum text-ink-3">· seg. {Math.round(p.segundo)}</span>}
                          </div>
                          <p className="text-ink-2 [overflow-wrap:anywhere]">{p.detalle}</p>
                        </li>
                      );
                    })}
                  </ul>
                )}
                {review.sugerencias.length > 0 && (
                  <div>
                    <p className="mb-1 font-bold">Qué mejorar</p>
                    <ul className="list-disc space-y-1 pl-5 text-ink-2 marker:text-ink-3">
                      {review.sugerencias.map((s, i) => (
                        <li key={i} className="[overflow-wrap:anywhere]">
                          {s}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

export function clipText(c: ClipResult) {
  return `${c.caption || c.title}\n\n${c.hashtags.join(" ")}`.trim();
}

/** Clip estilo OpusClip: video vertical a la izquierda; a la derecha título, potencial viral, gancho, hashtags, nota de la IA y acciones. */
export function ClipCard({ jobId, c, onEdit, onChanged }: { jobId: string; c: ClipResult; onEdit?: () => void; onChanged?: () => void }) {
  const rev = c.rev ?? 0;
  const toast = useToast();
  const [copied, setCopied] = useState(false);
  const [publishing, setPublishing] = useState(false);
  const [quick, setQuick] = useState(false); // edición rápida de título y hashtags
  const [title, setTitle] = useState(c.title);
  const [tags, setTags] = useState(c.hashtags.join(" "));
  const [saving, setSaving] = useState(false);
  const saveMeta = async () => {
    setSaving(true);
    try {
      await api.updateClipMeta(jobId, c.index, { title: title.trim() || c.title, hashtags: tags.split(/\s+/).filter(Boolean) });
      toast("Guardado.");
      setQuick(false);
      onChanged?.();
    } catch (e) {
      toast(e instanceof Error ? e.message : "No se pudo guardar.", "bad");
    } finally {
      setSaving(false);
    }
  };

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(clipText(c));
      setCopied(true);
      toast("Texto copiado. Pégalo en tu publicación.");
      setTimeout(() => setCopied(false), 1800);
    } catch {
      toast("No pudimos copiar. Selecciona el texto y cópialo a mano.", "bad");
    }
  };

  return (
    <Card className="min-w-0 flex-col gap-0 overflow-hidden border border-line p-0 sm:flex-row" aria-label={`Clip ${c.index}: ${c.title}`}>
      <div className="relative shrink-0 bg-black sm:w-[15rem]">
        <video key={c.file + rev} src={`${api.fileUrl(jobId, c.file)}${rev ? `?v=${rev}` : ""}`} poster={c.thumb ? `${api.fileUrl(jobId, c.thumb)}${rev ? `?v=${rev}` : ""}` : undefined} controls playsInline preload="metadata" className="mx-auto block aspect-[9/16] max-h-[26rem] w-full bg-black object-contain sm:max-h-none sm:h-full" aria-label={`Reproducir clip ${c.index}`} />
        <span className="tnum pointer-events-none absolute left-2.5 top-2.5 rounded-lg bg-black/70 px-2 py-0.5 text-sm font-bold text-white">{formatDuration(c.duration)}</span>
      </div>
      <div className="flex min-w-0 flex-1 flex-col gap-3.5 p-4 sm:p-5">
        <div className="flex items-start gap-3">
          <span className="brand-bg num grid size-11 shrink-0 place-items-center rounded-2xl text-xl text-white" title="Potencial viral" aria-label={`Potencial viral: ${Math.round(c.score)}`}>
            {Math.round(c.score)}
          </span>
          <div className="min-w-0">
            {quick ? (
              <div className="flex flex-col gap-2">
                <input value={title} onChange={(e) => setTitle(e.target.value)} aria-label="Título del clip" className="min-h-11 w-full rounded-xl border border-line bg-raised-2 px-3 text-base font-bold text-ink focus-visible:outline-2 focus-visible:outline-accent-hi" />
                <input value={tags} onChange={(e) => setTags(e.target.value)} aria-label="Hashtags (separados por espacios)" placeholder="#hashtag1 #hashtag2" className="min-h-11 w-full rounded-xl border border-line bg-raised-2 px-3 text-sm text-ink focus-visible:outline-2 focus-visible:outline-accent-hi" />
                <div className="flex gap-2">
                  <Button size="sm" variant="primary" onClick={saveMeta} loading={saving}>Guardar</Button>
                  <Button size="sm" onClick={() => { setQuick(false); setTitle(c.title); setTags(c.hashtags.join(" ")); }}>Cancelar</Button>
                </div>
              </div>
            ) : (
            <h3 className="line-clamp-3 text-lg font-extrabold leading-snug [overflow-wrap:anywhere]">
              {c.title}
              {(c.edited || c.meta_edited) && <span className="ml-2 align-middle text-xs font-semibold text-ink-3">(editado)</span>}
            </h3>
            )}
            <p className="mt-0.5 text-sm text-ink-3">
              Potencial viral · {formatDuration(c.start)}–{formatDuration(c.end)} del video
            </p>
          </div>
        </div>
        {c.hook && (
          <p className="rounded-2xl bg-raised-2 px-3.5 py-2.5 text-sm [overflow-wrap:anywhere]">
            <span className="text-ink-3">Gancho: </span>
            <span className="font-bold">{c.hook}</span>
          </p>
        )}
        {c.hashtags.length > 0 && (
          <ul className="flex max-h-[4.5rem] flex-wrap gap-1.5 overflow-hidden" aria-label="Hashtags">
            {c.hashtags.slice(0, 8).map((h, i) => (
              <li key={i} className="max-w-full truncate rounded-full bg-accent-soft px-2.5 py-0.5 text-[13px] font-semibold text-accent-hi">
                {h}
              </li>
            ))}
            {c.hashtags.length > 8 && <li className="px-1 py-0.5 text-[13px] text-ink-3">+{c.hashtags.length - 8}</li>}
          </ul>
        )}
        <ReviewPanel review={c.review} />
        <div className="mt-auto flex flex-wrap gap-2 pt-1">
          <Button size="sm" onClick={() => { setTitle(c.title); setTags(c.hashtags.join(" ")); setQuick(true); }} icon={<Pencil className="size-4" aria-hidden />} className="max-sm:flex-1">
            Título y hashtags
          </Button>
          <Button size="sm" variant="primary" onClick={() => setPublishing(true)} icon={<Send className="size-4" aria-hidden />} className="max-sm:w-full">
            Publicar
          </Button>
          {onEdit && (
            <Button size="sm" onClick={onEdit} icon={<Scissors className="size-4" aria-hidden />} className="max-sm:flex-1">
              Editar corte
            </Button>
          )}
          <Link href={`/calendario?clip=${encodeURIComponent(jobId)}::${encodeURIComponent(c.file)}`} className={cn(buttonClass({ size: "sm" }), "max-sm:flex-1")}>
            <CalendarClock className="size-4" aria-hidden />
            Programar
          </Link>
          <a href={api.fileUrl(jobId, c.file, { download: true })} download={c.file} className={cn(buttonClass({ size: "sm" }), "max-sm:flex-1")}>
            <Download className="size-4" aria-hidden />
            Descargar
          </a>
          <Button size="sm" onClick={copy} icon={copied ? <Check className="size-4 text-ok" aria-hidden /> : <Copy className="size-4" aria-hidden />} className="max-sm:flex-1">
            {copied ? "Copiado" : "Copiar texto"}
          </Button>
        </div>
      </div>
      {publishing && <PublishDialog jobId={jobId} clip={c} onClose={() => setPublishing(false)} />}
    </Card>
  );
}
