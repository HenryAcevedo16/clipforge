"use client";
import { Card, Tabs } from "@heroui/react";
import { Film, Plus, Search, SearchX, Trash2 } from "lucide-react";
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { api, type Project } from "@/lib/api";
import { useResource } from "@/lib/hooks/useResource";
import { currentStage, friendlyMessage } from "@/lib/stages";
import { timeAgo } from "@/lib/time";
import { Badge } from "../ui/Badge";
import { buttonClass } from "../ui/Button";
import { cn } from "../ui/cn";
import { inputClass } from "../ui/Field";
import { PageHeader } from "../ui/PageHeader";
import { EmptyState, ErrorState, LoadingLabel, Skeleton } from "../ui/States";
import { FILTERS, projectTitle, STATE_META } from "./projectMeta";
import { Ring } from "../home/StageList";

function expiryText(ms?: number | null): string | null {
  if (!ms) return null;
  const days = Math.ceil((ms - Date.now()) / 86400000);
  return days <= 1 ? "Se borra solo hoy o mañana" : `Se borra solo en ${days} días`;
}

function ProjectCard({ p, onDelete }: { p: Project; onDelete: (p: Project) => void }) {
  const [confirm, setConfirm] = useState(false);
  const meta = STATE_META[p.state];
  const first = p.job.result?.clips[0];
  const n = p.job.result?.clips.length ?? 0;
  return (
    <li className="relative min-w-0">
      <Link href={`/proyecto/?id=${p.jobId}`} className="group block h-full rounded-3xl transition-transform duration-150 ease-[var(--ease-out)] active:scale-[0.985]">
        <Card className="h-full gap-0 overflow-hidden border border-line p-0 transition-colors group-hover:border-line-2">
          <div className="relative aspect-video bg-shell">
            {first?.thumb ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={api.fileUrl(p.jobId, first.thumb)} alt="" className="absolute inset-0 size-full object-cover transition-transform duration-300 ease-[var(--ease-out)] group-hover:scale-[1.03]" loading="lazy" />
            ) : p.state === "running" ? (
              <div className="grid size-full place-items-center" aria-hidden>
                <Ring n={currentStage(p.job) + 1} state="active" />
              </div>
            ) : (
              <div className="grid size-full place-items-center text-ink-3">
                <Film className="size-8" aria-hidden />
              </div>
            )}
            <div className="absolute left-2.5 top-2.5 rounded-full bg-black/60 backdrop-blur-sm">
              <Badge tone={meta.tone} live={p.state === "running"}>
                {meta.label}
              </Badge>
            </div>
            {p.state === "done" && (
              <span className="absolute bottom-2.5 right-2.5 rounded-full bg-black/65 px-2.5 py-1 text-xs font-bold text-white backdrop-blur-sm">
                <span className="tnum">{n}</span> {n === 1 ? "clip" : "clips"}
              </span>
            )}
          </div>
          <div className="flex flex-1 flex-col gap-1.5 p-4">
            <h2 title={projectTitle(p)} className="line-clamp-2 text-base font-extrabold leading-snug [overflow-wrap:anywhere] group-hover:text-accent-hi">
              {projectTitle(p)}
            </h2>
            <p className="line-clamp-2 text-sm text-ink-3 [overflow-wrap:anywhere]">
              {p.state === "running" ? friendlyMessage(p.job.message) : p.state === "error" ? p.job.message : p.state === "queued" ? "Esperando turno para empezar" : p.state === "empty" ? "No salió ningún clip de este video" : p.job.source}
            </p>
            <p className="mt-auto pt-1 text-xs font-medium text-ink-3">
              {timeAgo(p.addedAt)}
              {expiryText(p.expiresAt) && <span> · {expiryText(p.expiresAt)}</span>}
            </p>
          </div>
        </Card>
      </Link>
      <button
        type="button"
        aria-label={confirm ? "Confirmar: eliminar proyecto" : "Eliminar proyecto"}
        onClick={() => (confirm ? onDelete(p) : setConfirm(true))}
        onBlur={() => setConfirm(false)}
        className="absolute right-2.5 top-2.5 z-10 flex items-center gap-1 rounded-full bg-black/65 px-2.5 py-1.5 text-xs font-bold text-white backdrop-blur-sm transition-colors hover:bg-red-600"
      >
        <Trash2 className="size-3.5" aria-hidden />
        {confirm ? "¿Seguro? Pulsa otra vez" : null}
      </button>
    </li>
  );
}

export function ProjectsList() {
  const res = useResource(() => api.listProjects(), []);
  const [q, setQ] = useState("");
  const [filter, setFilter] = useState<(typeof FILTERS)[number]["v"]>("all");

  // Mientras haya trabajos en curso, refresca solo cada 3 s.
  const busy = res.data?.some((p) => p.state === "running" || p.state === "queued");
  useEffect(() => {
    if (!busy) return;
    const t = setInterval(() => res.reload(true), 3000);
    return () => clearInterval(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [busy]);

  const remove = async (p: Project) => {
    try {
      await api.removeProject(p.jobId);
    } finally {
      res.reload(true);
    }
  };

  const shown = useMemo(() => {
    const term = q.trim().toLowerCase();
    return (res.data ?? []).filter((p) => {
      if (filter === "active" ? !(p.state === "running" || p.state === "queued") : filter !== "all" && p.state !== filter) return false;
      return !term || projectTitle(p).toLowerCase().includes(term) || p.job.source.toLowerCase().includes(term);
    });
  }, [res.data, q, filter]);

  const counts = useMemo(() => {
    const c: Record<string, number> = { all: res.data?.length ?? 0, active: 0, done: 0, empty: 0, error: 0 };
    for (const p of res.data ?? []) {
      if (p.state === "running" || p.state === "queued") c.active++;
      else c[p.state]++;
    }
    return c;
  }, [res.data]);

  return (
    <div>
      <PageHeader
        title="Mis proyectos"
        description="Todos los videos que has procesado y los clips de cada uno. Los proyectos se borran solos a los 5 días."
        actions={
          <Link href="/" className={buttonClass({ variant: "primary" })}>
            <Plus className="size-4" aria-hidden />
            Nuevo proyecto
          </Link>
        }
      />

      {res.loading && (
        <>
          <LoadingLabel text="Cargando tus proyectos…" />
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3" aria-hidden>
            {[0, 1, 2, 3].map((i) => (
              <Skeleton key={i} className="h-64" />
            ))}
          </div>
        </>
      )}

      {!res.loading && res.error && <ErrorState title="No pudimos cargar tus proyectos" message={res.error} onRetry={() => res.reload()} />}

      {!res.loading && !res.error && res.data && res.data.length === 0 && (
        <EmptyState
          icon={<Film />}
          title="Aún no tienes proyectos"
          text="Cuando proceses tu primer video, aparecerá aquí con todos sus clips."
          action={
            <Link href="/" className={buttonClass({ variant: "primary" })}>
              Crear mi primer clip
            </Link>
          }
        />
      )}

      {!res.loading && !res.error && res.data && res.data.length > 0 && (
        <>
          <Tabs selectedKey={filter} onSelectionChange={(k) => setFilter(String(k) as (typeof FILTERS)[number]["v"])} className="gap-0">
          <div className="mb-5 flex flex-col gap-3 lg:flex-row lg:items-center">
            <div className="relative lg:w-80">
              <label htmlFor="buscar" className="sr-only">
                Buscar proyectos
              </label>
              <Search className="pointer-events-none absolute left-3.5 top-1/2 size-[18px] -translate-y-1/2 text-ink-3" aria-hidden />
              <input id="buscar" type="search" value={q} onChange={(e) => setQ(e.target.value)} placeholder="Buscar por título o link" className={cn(inputClass, "pl-10")} />
            </div>
            <div className="-mx-4 min-w-0 overflow-x-auto px-4 pb-1 lg:mx-0 lg:overflow-visible lg:px-0 lg:pb-0">
                <Tabs.ListContainer>
                  <Tabs.List aria-label="Filtrar por estado">
                    {FILTERS.map((f) => (
                      <Tabs.Tab key={f.v} id={f.v} className="whitespace-nowrap">
                        {f.label} <span className="tnum ml-1 text-xs font-semibold opacity-70">{counts[f.v]}</span>
                        <Tabs.Indicator />
                      </Tabs.Tab>
                    ))}
                  </Tabs.List>
                </Tabs.ListContainer>
            </div>
          </div>

          <Tabs.Panel id={filter}>
          <p role="status" className="sr-only">
            {shown.length} {shown.length === 1 ? "proyecto" : "proyectos"}
          </p>

          {shown.length === 0 ? (
            <EmptyState
              icon={<SearchX />}
              title="No encontramos proyectos así"
              text="Prueba con otra palabra o quita el filtro de estado."
              action={
                <button type="button" onClick={() => { setQ(""); setFilter("all"); }} className={buttonClass()}>
                  Quitar filtros
                </button>
              }
            />
          ) : (
            <ul className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
              {shown.map((p) => (
                <ProjectCard key={p.jobId} p={p} onDelete={remove} />
              ))}
            </ul>
          )}
          </Tabs.Panel>
          </Tabs>
        </>
      )}
    </div>
  );
}
