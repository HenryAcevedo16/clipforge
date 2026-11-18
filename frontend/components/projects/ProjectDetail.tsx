"use client";
import { ArrowLeft, FileX2, Film, Plus, Square } from "lucide-react";
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { api, ApiError, type ProjectState } from "@/lib/api";
import { useResource } from "@/lib/hooks/useResource";
import { detectPlatform } from "@/lib/platform";
import { PlatformPill } from "../ui/PlatformPill";
import { jobTitle } from "@/lib/format";
import { formatDuration, timeAgo } from "@/lib/time";
import { StageList } from "../home/StageList";
import { Badge } from "../ui/Badge";
import { Button, buttonClass } from "../ui/Button";
import { EmptyState, ErrorState, LoadingLabel, Skeleton } from "../ui/States";
import { useToast } from "../ui/Toast";
import { ClipCard } from "./ClipCard";
import { ClipEditor } from "./ClipEditor";
import { STATE_META } from "./projectMeta";

export function ProjectDetail({ id }: { id: string }) {
  const res = useResource(() => api.getJob(id), [id]);
  const job = res.data;
  const [sort, setSort] = useState<"score" | "order">("score");
  const toast = useToast();
  const [editing, setEditing] = useState<number | null>(null);
  const [cancelling, setCancelling] = useState(false);

  const busy = job?.status === "running" || job?.status === "queued";
  useEffect(() => {
    if (!busy) return;
    const t = setInterval(() => res.reload(true), 1500);
    return () => clearInterval(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [busy]);

  const clips = useMemo(() => {
    const l = [...(job?.result?.clips ?? [])];
    return sort === "score" ? l.sort((a, b) => b.score - a.score) : l.sort((a, b) => a.index - b.index);
  }, [job, sort]);

  const cancel = async () => {
    if (!window.confirm(job?.result?.live ? "¿Detener el directo? Los clips ya hechos se conservan." : "¿Cancelar la generación de clips?")) return;
    setCancelling(true);
    try {
      await api.cancelJob(id);
      toast("Cancelando…");
      res.reload(true);
    } catch (e) {
      toast(e instanceof Error ? e.message : "No se pudo cancelar.", "bad");
    } finally {
      setCancelling(false);
    }
  };

  const back = (
    <Link href="/proyectos" className="mb-4 inline-flex min-h-11 items-center gap-1.5 rounded-xl pr-3 text-sm font-bold text-ink-2 transition-colors hover:text-ink">
      <ArrowLeft className="size-4" aria-hidden />
      Mis proyectos
    </Link>
  );

  if (res.loading) {
    return (
      <div>
        {back}
        <LoadingLabel text="Cargando el proyecto…" />
        <Skeleton className="mb-6 h-10 w-2/3" />
        <div className="flex flex-col gap-5" aria-hidden>
          {[0, 1].map((i) => (
            <Skeleton key={i} className="h-[26rem]" />
          ))}
        </div>
      </div>
    );
  }

  if (res.error || !job) {
    const notFound = res.error === "Trabajo no encontrado";
    return (
      <div>
        {back}
        {notFound ? (
          <EmptyState icon={<FileX2 />} title="No encontramos este proyecto" text="Puede que se haya borrado o que el link esté mal escrito." action={<Link href="/proyectos" className={buttonClass({ variant: "primary" })}>Ver mis proyectos</Link>} />
        ) : (
          <ErrorState title="No pudimos cargar este proyecto" message={res.error ?? "Error desconocido"} onRetry={() => res.reload()} />
        )}
      </div>
    );
  }

  const state: ProjectState = job.status === "done" ? (job.result && job.result.clips.length === 0 ? "empty" : "done") : job.status === "queued" || job.status === "running" || job.status === "live" ? (job.status === "queued" ? "queued" : "running") : "error";
  const meta = STATE_META[state];
  const title = jobTitle(job);

  return (
    <div>
      {back}
      <header className="mb-6 sm:mb-8">
        <div className="mb-2 flex flex-wrap items-center gap-2">
          <Badge tone={meta.tone} live={state === "running"}>
            {meta.label}
          </Badge>
          <span className="text-sm text-ink-3">{timeAgo(job.created * 1000)}</span>
        </div>
        <h1 className="text-[1.7rem] font-extrabold leading-tight tracking-tight [overflow-wrap:anywhere] sm:text-[2.1rem]">{title}</h1>
        {job.result && (
          <p className="mt-1.5 text-ink-2">
            Video de {formatDuration(job.result.source.duration)} · {job.result.source.width}×{job.result.source.height}
            {job.result.language ? ` · idioma: ${job.result.language === "es" ? "español" : job.result.language}` : ""}
          </p>
        )}
        <p className="mt-0.5 flex min-w-0 items-center gap-2 text-sm text-ink-3">
          {detectPlatform(job.source) && <PlatformPill info={detectPlatform(job.source)!} />}
          <span className="truncate">{job.source}</span>
        </p>
      </header>

      {(state === "running" || state === "queued") && (
        <section aria-label="Progreso" className="max-w-xl rounded-3xl border border-line bg-raised p-5 sm:p-6">
          <p className="mb-4 text-ink-2">{state === "queued" ? "Estás en la cola. Empezamos en cuanto llegue tu turno." : "Estamos creando tus clips. Esta página se actualiza sola."}</p>
          <StageList job={job} />
          <div className="mt-4">
            <Button variant="danger" size="sm" onClick={cancel} loading={cancelling || !!job.cancel_requested} icon={<Square className="size-4" aria-hidden />}>
              {job.cancel_requested ? "Cancelando…" : job.result?.live ? "Detener directo" : "Cancelar generación"}
            </Button>
          </div>
        </section>
      )}

      {state === "error" && (
        <div className="flex flex-col gap-4">
          <ErrorState title="No pudimos terminar este video" message={job.message} />
          <div>
            <Link href="/" className={buttonClass({ variant: "primary" })}>
              <Plus className="size-4" aria-hidden />
              Probar con otro video
            </Link>
          </div>
        </div>
      )}

      {state === "empty" && (
        <EmptyState icon={<Film />} title="Este video no dio ningún clip" text="No encontramos partes con voz para recortar. Prueba con otro video o con duraciones distintas." action={<Link href="/" className={buttonClass({ variant: "primary" })}>Procesar otro video</Link>} />
      )}

      {(state === "done" || ((state === "running" || state === "error") && clips.length > 0)) && (
        <section aria-label="Clips" className={state === "running" || state === "error" ? "mt-8" : undefined}>
          <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
            <h2 className="text-lg font-semibold">
              <span className="tnum">{clips.length}</span> {job.result?.partial && job.result.total ? `de ${job.result.total} clips listos` : clips.length === 1 ? "clip" : "clips"}
            </h2>
            <div className="flex items-center gap-2">
              <label htmlFor="orden" className="text-sm text-ink-3">
                Ordenar por
              </label>
              <select id="orden" value={sort} onChange={(e) => setSort(e.target.value as "score" | "order")} className="min-h-10 rounded-xl border border-line bg-raised px-3 text-base font-medium text-ink-2 hover:border-line-2 lg:text-sm">
                <option value="score">Potencial viral</option>
                <option value="order">Orden en el video</option>
              </select>
            </div>
          </div>
          <div className="flex flex-col gap-5">
            {clips.map((c) => (
              <ClipCard key={c.file} jobId={job.id} c={c} onEdit={!job.result?.live ? () => setEditing(c.index) : undefined} onChanged={() => res.reload(true)} />
            ))}
          </div>
        </section>
      )}
      {editing !== null && (
        <ClipEditor
          jobId={job.id}
          index={editing}
          onClose={() => setEditing(null)}
          onChanged={() => res.reload(true)}
        />
      )}
    </div>
  );
}
