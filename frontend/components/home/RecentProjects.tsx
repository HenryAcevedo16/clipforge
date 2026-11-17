"use client";
import { Card } from "@heroui/react";
import { ArrowRight, Film } from "lucide-react";
import Link from "next/link";
import { api } from "@/lib/api";
import { jobTitle } from "@/lib/format";
import { useResource } from "@/lib/hooks/useResource";
import { timeAgo } from "@/lib/time";
import { Badge } from "../ui/Badge";
import { STATE_META } from "../projects/projectMeta";
import { Skeleton } from "../ui/States";

/** Fila "Tus proyectos recientes" del Home (estilo OpusClip): hasta 4 proyectos con su miniatura. */
export function RecentProjects() {
  const res = useResource(() => api.listProjects(), []);
  const list = (res.data ?? []).slice(0, 4);
  if (res.error || (!res.loading && list.length === 0)) return null;
  return (
    <section aria-labelledby="h-recent" className="mt-14">
      <div className="mb-4 flex items-center justify-between gap-3">
        <h2 id="h-recent" className="text-xl font-extrabold">
          Tus proyectos recientes
        </h2>
        <Link href="/proyectos" className="inline-flex min-h-11 items-center gap-1 rounded-xl px-2 text-sm font-bold text-accent-hi hover:underline">
          Ver todos <ArrowRight className="size-4" aria-hidden />
        </Link>
      </div>
      {res.loading ? (
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-4" aria-hidden>
          {[0, 1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-56" />
          ))}
        </div>
      ) : (
        <ul className="grid grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-4">
          {list.map((p) => {
            const first = p.job.result?.clips[0];
            const meta = STATE_META[p.state];
            return (
              <li key={p.jobId} className="min-w-0">
                <Link href={`/proyecto/?id=${p.jobId}`} className="group block rounded-3xl transition-transform duration-150 ease-[var(--ease-out)] active:scale-[0.98]">
                  <Card className="h-full gap-0 overflow-hidden border border-line p-0 transition-colors group-hover:border-line-2">
                    <div className="relative aspect-video bg-shell">
                      {first?.thumb ? (
                        // eslint-disable-next-line @next/next/no-img-element
                        <img src={api.fileUrl(p.jobId, first.thumb)} alt="" className="absolute inset-0 size-full object-cover" loading="lazy" />
                      ) : (
                        <div className="grid size-full place-items-center text-ink-3">
                          <Film className="size-7" aria-hidden />
                        </div>
                      )}
                      <div className="absolute left-2 top-2 rounded-full bg-black/60 backdrop-blur-sm">
                        <Badge tone={meta.tone} live={p.state === "running"}>
                          {meta.label}
                        </Badge>
                      </div>
                    </div>
                    <div className="p-3.5">
                      <h3 title={jobTitle(p.job)} className="line-clamp-2 text-sm font-bold leading-snug [overflow-wrap:anywhere]">
                        {jobTitle(p.job)}
                      </h3>
                      <p className="mt-1 text-xs text-ink-3">
                        {p.state === "done" ? `${p.job.result?.clips.length ?? 0} clips · ` : ""}
                        {timeAgo(p.addedAt)}
                      </p>
                    </div>
                  </Card>
                </Link>
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}
