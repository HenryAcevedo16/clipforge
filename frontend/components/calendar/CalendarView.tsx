"use client";
/**
 * CALENDARIO — [REQUIERE BACKEND NUEVO]
 * Las publicaciones se guardan en el navegador (lib/api/extras.ts). En la versión real el backend las guardaría y
 * un trabajador publicaría a la hora indicada usando las APIs oficiales de TikTok, YouTube e Instagram.
 * Zona horaria: America/Santo_Domingo (UTC-4, sin horario de verano) -> lib/time.ts.
 * Mover una publicación se hace con fecha y hora (funciona con teclado y con el dedo); no hay arrastrar y soltar.
 */
import { Card, Tabs } from "@heroui/react";
import { CalendarPlus, Check, ChevronLeft, ChevronRight, Clock, Link2, Trash2, X } from "lucide-react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { api, type Project, type ScheduledPost, type SocialAccount } from "@/lib/api";
import { groupByDay, inputsFromIso, isoFromInputs, monthGrid, shiftCursor, weekDays, type Day } from "@/lib/calendar";
import { NETWORK_META } from "@/lib/brand";
import { useResource } from "@/lib/hooks/useResource";
import { DIAS_CORTOS, DIAS_LARGOS, MESES, TZ, formatSD, formatTimeSD, nowSD, ymd, type SDParts } from "@/lib/time";
import { NetworkChip } from "../accounts/NetworkIcon";
import { Badge, type Tone } from "../ui/Badge";
import { Button, buttonClass } from "../ui/Button";
import { cn } from "../ui/cn";
import { Dialog } from "../ui/Dialog";
import { Field, inputClass } from "../ui/Field";
import { PageHeader } from "../ui/PageHeader";
import { PreviewNotice } from "../ui/PreviewNotice";
import { EmptyState, ErrorState, LoadingLabel, Skeleton } from "../ui/States";
import { useToast } from "../ui/Toast";

const STATUS: Record<ScheduledPost["status"], { label: string; tone: Tone; dot: string }> = {
  scheduled: { label: "Programado", tone: "accent", dot: "bg-accent-hi" },
  published: { label: "Publicado", tone: "ok", dot: "bg-ok" },
  failed: { label: "Falló", tone: "bad", dot: "bg-bad" },
};

type Cursor = { y: number; m: number; d: number };
const DOW_HEAD = ["lun", "mar", "mié", "jue", "vie", "sáb", "dom"];

const cap = (t: string) => t.charAt(0).toUpperCase() + t.slice(1);

function dayLabel(d: Cursor) {
  const dow = new Date(Date.UTC(d.y, d.m, d.d)).getUTCDay();
  return cap(`${DIAS_LARGOS[dow]} ${d.d} de ${MESES[d.m]}`);
}

export function CalendarView() {
  const router = useRouter();
  const params = useSearchParams();
  const toast = useToast();
  const posts = useResource(() => api.listPosts(), []);
  const accounts = useResource(() => api.listAccounts(), []);
  const projects = useResource(() => api.listProjects(), []);

  const [view, setView] = useState<"month" | "week">("month");
  const [cursor, setCursor] = useState<Cursor | null>(null);
  const [today, setToday] = useState<SDParts | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [openPost, setOpenPost] = useState<ScheduledPost | null>(null);
  const [scheduling, setScheduling] = useState<{ clip?: string; date?: string } | null>(null);

  useEffect(() => {
    const t = nowSD();
    setToday(t);
    setCursor({ y: t.y, m: t.m, d: t.d });
    setSelected(ymd(t));
  }, []);

  // "Programar" desde un clip: /calendario?clip=jobId::archivo -> abre el formulario con ese clip elegido.
  const clipParam = params.get("clip");
  useEffect(() => {
    if (clipParam && projects.data && accounts.data) {
      setScheduling({ clip: clipParam });
      router.replace("/calendario");
    }
  }, [clipParam, projects.data, accounts.data, router]);

  const byDay = useMemo(() => groupByDay(posts.data ?? []), [posts.data]);
  const accMap = useMemo(() => new Map((accounts.data ?? []).map((a) => [a.id, a])), [accounts.data]);
  const connected = (accounts.data ?? []).filter((a) => a.status === "connected");

  const loading = posts.loading || accounts.loading || !cursor || !today;
  const error = posts.error || accounts.error;
  const reloadAll = () => {
    posts.reload();
    accounts.reload();
    projects.reload();
  };

  const range = useMemo(() => {
    if (!cursor) return "";
    if (view === "month") return `${MESES[cursor.m]} de ${cursor.y}`;
    const w = weekDays(cursor);
    const a = w[0];
    const b = w[6];
    return a.m === b.m ? `${a.d}–${b.d} de ${MESES[b.m]} de ${b.y}` : `${a.d} de ${MESES[a.m].slice(0, 3)}. – ${b.d} de ${MESES[b.m].slice(0, 3)}. de ${b.y}`;
  }, [cursor, view]);

  const selectedDay = useMemo(() => {
    if (!selected) return null;
    const [y, m, d] = selected.split("-").map(Number);
    return { y, m: m - 1, d };
  }, [selected]);

  return (
    <div>
      <PageHeader
        title="Calendario"
        description="Programa cuándo se publica cada clip."
        actions={
          <Button variant="primary" onClick={() => setScheduling({})} icon={<CalendarPlus className="size-4" aria-hidden />}>
            Programar clip
          </Button>
        }
      />
      <PreviewNotice>Vista previa: por ahora el calendario solo guarda tus planes en este navegador y todavía no publica en TikTok, YouTube ni Instagram. Descarga el clip y súbelo desde cada app.</PreviewNotice>

      {loading && !error && (
        <>
          <LoadingLabel text="Cargando tu calendario…" />
          <Skeleton className="mb-4 h-12" />
          <Skeleton className="h-[28rem]" />
        </>
      )}

      {!loading && error && <ErrorState title="No pudimos cargar tu calendario" message={error} onRetry={reloadAll} />}

      {!loading && !error && cursor && today && (
        <>
          {connected.length === 0 && (
            <div className="mb-5 flex flex-col gap-3 rounded-3xl border border-accent/45 bg-accent-soft/60 p-4 sm:flex-row sm:items-center">
              <Link2 className="size-6 shrink-0 text-accent-hi" aria-hidden />
              <div className="min-w-0 flex-1">
                <p className="font-bold">Conecta una cuenta para poder programar</p>
                <p className="text-sm text-ink-2">{(accounts.data ?? []).length ? "Tus cuentas necesitan reconectarse antes de publicar." : "Aún no tienes cuentas de TikTok, YouTube Shorts ni Instagram Reels conectadas."}</p>
              </div>
              <Link href="/cuentas" className={buttonClass({ variant: "primary" })}>
                Ir a Cuentas de redes
              </Link>
            </div>
          )}

          <Tabs selectedKey={view} onSelectionChange={(k) => setView(String(k) as "month" | "week")} className="gap-0">
          <div className="mb-4 flex flex-wrap items-center gap-x-3 gap-y-3">
            <div className="flex items-center gap-1.5">
              <button type="button" aria-label={view === "month" ? "Mes anterior" : "Semana anterior"} onClick={() => setCursor(shiftCursor(cursor, view, -1))} className={cn(buttonClass({ variant: "secondary" }), "size-11 px-0")}>
                <ChevronLeft className="size-5" aria-hidden />
              </button>
              <button type="button" aria-label={view === "month" ? "Mes siguiente" : "Semana siguiente"} onClick={() => setCursor(shiftCursor(cursor, view, 1))} className={cn(buttonClass({ variant: "secondary" }), "size-11 px-0")}>
                <ChevronRight className="size-5" aria-hidden />
              </button>
              <Button onClick={() => { setCursor({ y: today.y, m: today.m, d: today.d }); setSelected(ymd(today)); }}>Hoy</Button>
            </div>
            <h2 className="order-last min-w-0 basis-full text-lg font-bold sm:order-none sm:basis-0 sm:flex-1 sm:text-xl" aria-live="polite">
              {cap(range)}
            </h2>
              <Tabs.ListContainer>
                <Tabs.List aria-label="Vista del calendario">
                  <Tabs.Tab id="month">
                    Mes
                    <Tabs.Indicator />
                  </Tabs.Tab>
                  <Tabs.Tab id="week">
                    Semana
                    <Tabs.Indicator />
                  </Tabs.Tab>
                </Tabs.List>
              </Tabs.ListContainer>
          </div>

          <p className="mb-4 flex items-center gap-1.5 text-sm text-ink-3">
            <Clock className="size-4" aria-hidden />
            Todas las horas son de República Dominicana ({TZ}, UTC−4).
          </p>

          <Tabs.Panel id={view}>
          {view === "month" ? (
            <MonthView cursor={cursor} today={today} byDay={byDay} selected={selected} onSelect={setSelected} onOpen={setOpenPost} accMap={accMap} />
          ) : (
            <WeekView cursor={cursor} today={today} byDay={byDay} onOpen={setOpenPost} accMap={accMap} onAdd={(k) => setScheduling({ date: k })} />
          )}

          {view === "month" && selectedDay && (
            <section aria-label={`Publicaciones del ${dayLabel(selectedDay)}`} className="mt-5 rounded-3xl border border-line bg-raised p-4 sm:p-5">
              <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
                <h3 className="text-base font-bold">{dayLabel(selectedDay)}</h3>
                <Button size="sm" onClick={() => setScheduling({ date: selected! })} icon={<CalendarPlus className="size-4" aria-hidden />}>
                  Programar este día
                </Button>
              </div>
              {(byDay.get(selected!) ?? []).length === 0 ? (
                <p className="text-ink-3">No hay publicaciones este día.</p>
              ) : (
                <ul className="flex flex-col gap-2">
                  {byDay.get(selected!)!.map((p) => (
                    <PostRow key={p.id} p={p} accMap={accMap} onOpen={() => setOpenPost(p)} />
                  ))}
                </ul>
              )}
            </section>
          )}

          </Tabs.Panel>
          </Tabs>

          {(posts.data ?? []).length === 0 && (
            <EmptyState className="mt-5" icon={<CalendarPlus />} title="Aún no has programado nada" text="Elige un clip de Mis proyectos y pulsa «Programar», o usa el botón de arriba." action={<Button variant="primary" onClick={() => setScheduling({})}>Programar mi primer clip</Button>} />
          )}
        </>
      )}

      <PostDialog
        post={openPost}
        accMap={accMap}
        onClose={() => setOpenPost(null)}
        onChanged={async (msg) => {
          await posts.reload(true);
          setOpenPost(null);
          toast(msg);
        }}
      />
      <ScheduleDialog
        open={!!scheduling}
        init={scheduling ?? {}}
        projects={projects.data ?? []}
        accounts={accounts.data ?? []}
        today={today}
        onClose={() => setScheduling(null)}
        onDone={async (iso) => {
          await posts.reload(true);
          const d = new Date(iso);
          const [y, m, dd] = ymd(toSDSafe(d)).split("-").map(Number);
          setCursor({ y, m: m - 1, d: dd });
          setSelected(ymd(toSDSafe(d)));
          setScheduling(null);
          toast("Listo: tu clip quedó programado.");
        }}
      />
    </div>
  );
}

import { toSD } from "@/lib/time";
const toSDSafe = (d: Date) => toSD(d);

/** Estado con forma además de color: reloj = programado, check = publicado, X = falló. */
function StatusIcon({ status }: { status: ScheduledPost["status"] }) {
  const cls = cn("size-3.5 shrink-0", status === "scheduled" && "text-accent-hi", status === "published" && "text-ok", status === "failed" && "text-bad");
  return status === "published" ? <Check className={cls} strokeWidth={3} aria-hidden /> : status === "failed" ? <X className={cls} strokeWidth={3} aria-hidden /> : <Clock className={cls} aria-hidden />;
}

function Dots({ posts }: { posts: ScheduledPost[] }) {
  return (
    <span aria-hidden className="flex h-2 items-center gap-0.5">
      {posts.slice(0, 3).map((p) => (
        <span key={p.id} className={cn("size-1.5 rounded-full", STATUS[p.status].dot)} />
      ))}
      {posts.length > 3 && <span className="text-[10px] leading-none text-ink-3">+</span>}
    </span>
  );
}

function MonthView({ cursor, today, byDay, selected, onSelect, onOpen, accMap }: { cursor: Cursor; today: SDParts; byDay: Map<string, ScheduledPost[]>; selected: string | null; onSelect: (k: string) => void; onOpen: (p: ScheduledPost) => void; accMap: Map<string, SocialAccount> }) {
  const days = monthGrid(cursor.y, cursor.m);
  const todayKey = ymd(today);
  return (
    <Card className="gap-0 overflow-hidden border border-line p-0">
      <div className="grid grid-cols-7 border-b border-line bg-shell text-center text-xs font-bold text-ink-3" aria-hidden>
        {DOW_HEAD.map((d) => (
          <div key={d} className="py-2 uppercase tracking-wide">
            {d}
          </div>
        ))}
      </div>
      <div className="grid grid-cols-7">
        {days.map((day, i) => {
          const list = byDay.get(day.key) ?? [];
          const isToday = day.key === todayKey;
          const sel = day.key === selected;
          return (
            <div key={day.key} className={cn("flex min-w-0 flex-col border-line", i % 7 !== 6 && "border-r", i < days.length - 7 && "border-b", !day.inMonth && "bg-shell/60", sel && "bg-accent-soft/40")}>
              <button
                type="button"
                onClick={() => onSelect(day.key)}
                aria-pressed={sel}
                aria-label={`${dayLabel(day)}${list.length ? `, ${list.length} ${list.length === 1 ? "publicación" : "publicaciones"}` : ""}`}
                className="flex min-h-14 w-full flex-col items-center gap-1 px-1 pt-1.5 transition-colors hover:bg-raised-2/70 md:min-h-9 md:flex-row md:items-start md:justify-between md:px-2 md:pt-2"
              >
                <span className={cn("tnum grid size-7 place-items-center rounded-full text-sm font-bold", isToday ? "bg-accent text-white" : day.inMonth ? "text-ink" : "text-ink-3")}>{day.d}</span>
                <span className="md:hidden">
                  <Dots posts={list} />
                </span>
                {list.length > 3 && <span className="hidden text-xs font-bold text-ink-3 md:inline">{list.length}</span>}
              </button>
              <ul className="hidden min-h-[7.5rem] flex-col gap-1 px-1.5 pb-1.5 md:flex">
                {list.slice(0, 2).map((p) => (
                  <li key={p.id}>
                    <button type="button" onClick={() => onOpen(p)} className="flex w-full min-w-0 flex-col gap-0.5 rounded-md bg-raised-2 px-1.5 py-1 text-left text-xs transition-[background-color,transform] duration-150 ease-[var(--ease-out)] active:scale-[0.97] hover:bg-[oklch(0.3_0.02_265)]" title={`${formatTimeSD(p.at)} · ${p.clipTitle}`}>
                      <span className="flex items-center gap-1">
                        <StatusIcon status={p.status} />
                        <span className="tnum font-bold">{formatTimeSD(p.at)}</span>
                      </span>
                      <span className="line-clamp-2 leading-tight text-ink-2 [overflow-wrap:anywhere]">{p.clipTitle}</span>
                      <span className="sr-only">
                        {STATUS[p.status].label}; {p.accountIds.map((id) => accMap.get(id)?.handle).filter(Boolean).join(", ")}
                      </span>
                    </button>
                  </li>
                ))}
                {list.length > 2 && (
                  <li>
                    <button type="button" onClick={() => onSelect(day.key)} className="w-full rounded-md px-1.5 py-0.5 text-left text-xs font-bold text-accent-hi hover:underline">
                      +{list.length - 2} más
                    </button>
                  </li>
                )}
              </ul>
            </div>
          );
        })}
      </div>
    </Card>
  );
}

function WeekView({ cursor, today, byDay, onOpen, accMap, onAdd }: { cursor: Cursor; today: SDParts; byDay: Map<string, ScheduledPost[]>; onOpen: (p: ScheduledPost) => void; accMap: Map<string, SocialAccount>; onAdd: (key: string) => void }) {
  const days = weekDays(cursor);
  const todayKey = ymd(today);
  return (
    <div className="grid gap-3 md:grid-cols-7 md:gap-0 md:overflow-hidden md:rounded-3xl md:border md:border-line md:bg-raised">
      {days.map((day, i) => {
        const list = byDay.get(day.key) ?? [];
        const isToday = day.key === todayKey;
        return (
          <section key={day.key} aria-label={dayLabel(day)} className={cn("flex min-w-0 flex-col rounded-3xl border border-line bg-raised md:min-h-72 md:rounded-none md:border-0", i < 6 && "md:border-r md:border-line")}>
            <header className={cn("flex items-center justify-between gap-2 border-b border-line px-3 py-2.5 md:flex-col md:items-start md:gap-0", isToday && "bg-accent-soft/50")}>
              <span className="text-xs font-bold uppercase tracking-wide text-ink-3">{DIAS_CORTOS[(i + 1) % 7]}</span>
              <span className={cn("tnum grid size-7 place-items-center rounded-full text-sm font-bold", isToday && "bg-accent text-white")}>{day.d}</span>
            </header>
            <ul className="flex flex-1 flex-col gap-1.5 p-2 md:max-h-[34rem] md:overflow-y-auto">
              {list.length === 0 && <li className="px-1 py-1 text-sm text-ink-3 md:hidden">Sin publicaciones</li>}
              {list.map((p) => (
                <PostRow key={p.id} p={p} accMap={accMap} onOpen={() => onOpen(p)} compact />
              ))}
            </ul>
            <button type="button" onClick={() => onAdd(day.key)} className="m-2 mt-0 flex min-h-10 items-center justify-center gap-1.5 rounded-xl border border-dashed border-line-2 text-sm font-bold text-ink-3 transition-colors hover:border-accent-hi hover:text-accent-hi">
              <CalendarPlus className="size-4" aria-hidden />
              <span className="md:sr-only">Programar</span>
              <span className="sr-only md:not-sr-only md:text-xs">Añadir</span>
            </button>
          </section>
        );
      })}
    </div>
  );
}

function PostRow({ p, accMap, onOpen, compact }: { p: ScheduledPost; accMap: Map<string, SocialAccount>; onOpen: () => void; compact?: boolean }) {
  const nets = Array.from(new Set(p.accountIds.map((id) => accMap.get(id)?.network).filter(Boolean))) as ("tiktok" | "youtube" | "instagram")[];
  return (
    <li>
      <button type="button" onClick={onOpen} className="flex w-full min-w-0 flex-col gap-1.5 rounded-2xl border border-line bg-shell px-3 py-2.5 text-left transition-[border-color,transform] duration-150 hover:border-line-2 active:scale-[0.99]">
        <span className="flex flex-wrap items-center justify-between gap-x-2 gap-y-1">
          <span className="tnum text-sm font-bold">{formatTimeSD(p.at)}</span>
          <Badge tone={STATUS[p.status].tone}>{STATUS[p.status].label}</Badge>
        </span>
        <span className={cn("block font-medium leading-snug [overflow-wrap:anywhere]", compact ? "line-clamp-2 text-[13px]" : "line-clamp-2 text-[15px]")}>{p.clipTitle}</span>
        <span className="flex flex-wrap gap-x-3 gap-y-0.5">
          {nets.map((n) => (
            <NetworkChip key={n} network={n} />
          ))}
          {nets.length === 0 && <span className="text-xs text-ink-3">Sin cuenta</span>}
        </span>
      </button>
    </li>
  );
}

function PostDialog({ post, accMap, onClose, onChanged }: { post: ScheduledPost | null; accMap: Map<string, SocialAccount>; onClose: () => void; onChanged: (msg: string) => Promise<void> }) {
  const [mode, setMode] = useState<"view" | "move" | "cancel">("view");
  const [date, setDate] = useState("");
  const [time, setTime] = useState("");
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!post) return;
    setMode("view");
    setErr(null);
    const i = inputsFromIso(post.at);
    setDate(i.date);
    setTime(i.time);
  }, [post]);

  const run = async (fn: () => Promise<void>, msg: string) => {
    setBusy(true);
    setErr(null);
    try {
      await fn();
      await onChanged(msg);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Algo salió mal. Inténtalo de nuevo.");
    } finally {
      setBusy(false);
    }
  };

  const editable = post && post.status !== "published";
  return (
    <Dialog
      open={!!post}
      onClose={onClose}
      title="Publicación"
      footer={
        post && mode === "view" ? (
          <>
            {editable && (
              <Button variant="danger" onClick={() => setMode("cancel")} icon={<Trash2 className="size-4" aria-hidden />}>
                Cancelar publicación
              </Button>
            )}
            {editable && <Button onClick={() => setMode("move")}>{post.status === "failed" ? "Reprogramar" : "Mover"}</Button>}
            <Button variant={editable ? "ghost" : "secondary"} onClick={onClose}>
              Cerrar
            </Button>
          </>
        ) : post && mode === "move" ? (
          <>
            <Button variant="ghost" onClick={() => setMode("view")}>
              Volver
            </Button>
            <Button
              variant="primary"
              loading={busy}
              onClick={() => {
                const iso = isoFromInputs(date, time);
                if (!iso) return setErr("Elige una fecha y una hora válidas.");
                run(async () => void (await api.movePost(post.id, iso)), "Publicación movida.");
              }}
            >
              Guardar nueva fecha
            </Button>
          </>
        ) : post ? (
          <>
            <Button variant="ghost" onClick={() => setMode("view")}>
              No, volver
            </Button>
            <Button variant="danger" loading={busy} onClick={() => run(() => api.cancelPost(post.id), "Publicación cancelada.")}>
              Sí, cancelar
            </Button>
          </>
        ) : null
      }
    >
      {post && (
        <div className="flex flex-col gap-4">
          <div>
            <h3 className="text-base font-bold [overflow-wrap:anywhere]">{post.clipTitle}</h3>
            <p className="mt-1 flex flex-wrap items-center gap-2 text-ink-2">
              <Badge tone={STATUS[post.status].tone}>{STATUS[post.status].label}</Badge>
              <span>{cap(formatSD(post.at))}</span>
            </p>
          </div>
          {post.status === "failed" && post.failReason && (
            <p role="alert" className="rounded-xl border border-bad/40 bg-bad-soft/60 px-3 py-2.5 text-sm text-bad [overflow-wrap:anywhere]">
              {post.failReason}
            </p>
          )}
          {mode === "cancel" && (
            <p role="alert" className="rounded-xl border border-warn/40 bg-warn-soft px-3 py-2.5 text-warn">
              ¿Seguro que quieres cancelar esta publicación? El clip no se borra, solo deja de estar programado.
            </p>
          )}
          {mode === "move" && (
            <div className="grid gap-4 sm:grid-cols-2">
              <Field label="Fecha">{(p) => <input {...p} type="date" value={date} onChange={(e) => setDate(e.target.value)} className={inputClass} />}</Field>
              <Field label="Hora (RD)">{(p) => <input {...p} type="time" value={time} onChange={(e) => setTime(e.target.value)} className={inputClass} />}</Field>
            </div>
          )}
          {err && (
            <p role="alert" className="text-sm text-bad">
              {err}
            </p>
          )}
          <div>
            <p className="mb-1.5 text-sm font-medium text-ink-2">Se publica en</p>
            <ul className="flex flex-col gap-1.5">
              {post.accountIds.map((id) => {
                const a = accMap.get(id);
                return (
                  <li key={id} className="flex flex-wrap items-center gap-x-2 text-sm">
                    {a ? <NetworkChip network={a.network} label={NETWORK_META[a.network].label} /> : <span className="text-ink-3">Cuenta desconectada</span>}
                    {a && <span className="truncate text-ink-3">{a.handle}</span>}
                  </li>
                );
              })}
            </ul>
          </div>
          <div>
            <p className="mb-1.5 text-sm font-medium text-ink-2">Descripción</p>
            <p className="rounded-xl bg-raised-2 px-3 py-2.5 text-sm text-ink-2 [overflow-wrap:anywhere]">{post.caption}</p>
          </div>
        </div>
      )}
    </Dialog>
  );
}

function ScheduleDialog({ open, init, projects, accounts, today, onClose, onDone }: { open: boolean; init: { clip?: string; date?: string }; projects: Project[]; accounts: SocialAccount[]; today: SDParts | null; onClose: () => void; onDone: (iso: string) => Promise<void> }) {
  const options = useMemo(() => projects.filter((p) => p.state === "done").flatMap((p) => (p.job.result?.clips ?? []).map((c) => ({ value: `${p.jobId}::${c.file}`, jobId: p.jobId, c, project: p.job.result!.title }))), [projects]);
  const [clip, setClip] = useState("");
  const [date, setDate] = useState("");
  const [time, setTime] = useState("18:00");
  const [accIds, setAccIds] = useState<string[]>([]);
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const ready = accounts.filter((a) => a.status === "connected");

  useEffect(() => {
    if (!open) return;
    setErr(null);
    setClip(init.clip && options.some((o) => o.value === init.clip) ? init.clip : (options[0]?.value ?? ""));
    if (init.date) setDate(init.date);
    else if (today) {
      const t = new Date(Date.UTC(today.y, today.m, today.d + 1));
      setDate(ymd({ y: t.getUTCFullYear(), m: t.getUTCMonth(), d: t.getUTCDate() }));
    }
    setTime("18:00");
    setAccIds(ready.map((a) => a.id));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);

  const submit = async () => {
    const sel = options.find((o) => o.value === clip);
    if (!sel) return setErr("Elige el clip que quieres publicar.");
    if (!accIds.length) return setErr("Elige al menos una red para publicar.");
    const iso = isoFromInputs(date, time);
    if (!iso) return setErr("Elige una fecha y una hora válidas.");
    setBusy(true);
    setErr(null);
    try {
      await api.schedulePost({ jobId: sel.jobId, clipFile: sel.c.file, clipTitle: sel.c.title, caption: `${sel.c.caption}\n\n${sel.c.hashtags.join(" ")}`.trim(), accountIds: accIds, at: iso });
      await onDone(iso);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "No pudimos programar la publicación.");
    } finally {
      setBusy(false);
    }
  };

  const noAccounts = ready.length === 0;
  const noClips = options.length === 0;

  return (
    <Dialog
      open={open}
      onClose={onClose}
      title="Programar un clip"
      footer={
        noAccounts ? (
          <>
            <Button variant="ghost" onClick={onClose}>
              Cerrar
            </Button>
            <Link href="/cuentas" className={buttonClass({ variant: "primary" })}>
              Ir a Cuentas de redes
            </Link>
          </>
        ) : (
          <>
            <Button variant="ghost" onClick={onClose}>
              Cancelar
            </Button>
            <Button variant="primary" onClick={submit} loading={busy} disabled={noClips}>
              Programar
            </Button>
          </>
        )
      }
    >
      {noAccounts ? (
        <div className="flex flex-col items-start gap-3 text-ink-2">
          <Link2 className="size-8 text-accent-hi" aria-hidden />
          <p className="font-bold text-ink">Primero conecta una cuenta</p>
          <p>Para programar un clip necesitas al menos una cuenta conectada de TikTok, YouTube Shorts o Instagram Reels.</p>
        </div>
      ) : noClips ? (
        <div className="flex flex-col items-start gap-3 text-ink-2">
          <p className="font-bold text-ink">Aún no tienes clips terminados</p>
          <p>Procesa un video en Inicio y vuelve aquí para programar sus clips.</p>
          <Link href="/" className={buttonClass({ variant: "primary" })}>
            Crear clips
          </Link>
        </div>
      ) : (
        <div className="flex flex-col gap-5">
          <Field label="Clip">
            {(p) => (
              <select {...p} value={clip} onChange={(e) => setClip(e.target.value)} className={inputClass}>
                {Array.from(new Set(options.map((o) => o.project))).map((proj) => (
                  <optgroup key={proj} label={proj.length > 60 ? proj.slice(0, 57) + "…" : proj}>
                    {options
                      .filter((o) => o.project === proj)
                      .map((o) => (
                        <option key={o.value} value={o.value}>
                          {o.c.title.length > 70 ? o.c.title.slice(0, 67) + "…" : o.c.title}
                        </option>
                      ))}
                  </optgroup>
                ))}
              </select>
            )}
          </Field>
          <div className="grid gap-4 sm:grid-cols-2">
            <Field label="Fecha">{(p) => <input {...p} type="date" value={date} onChange={(e) => setDate(e.target.value)} className={inputClass} />}</Field>
            <Field label="Hora (República Dominicana)">{(p) => <input {...p} type="time" value={time} onChange={(e) => setTime(e.target.value)} className={inputClass} />}</Field>
          </div>
          <fieldset className="min-w-0">
            <legend className="mb-1.5 text-sm font-medium text-ink-2">Publicar en</legend>
            <ul className="flex flex-col gap-2">
              {accounts.map((a) => {
                const off = a.status !== "connected";
                return (
                  <li key={a.id}>
                    <label className={cn("flex min-h-12 items-center gap-3 rounded-2xl border border-line bg-shell px-3.5 py-2", off ? "opacity-55" : "cursor-pointer hover:border-line-2 has-[:checked]:border-accent-hi has-[:checked]:bg-accent-soft/60")}>
                      <input type="checkbox" disabled={off} checked={accIds.includes(a.id)} onChange={(e) => setAccIds(e.target.checked ? [...accIds, a.id] : accIds.filter((x) => x !== a.id))} className="size-5 shrink-0 accent-[var(--color-accent-strong)]" />
                      <span className="min-w-0 flex-1">
                        <span className="block truncate font-medium">{NETWORK_META[a.network].label}</span>
                        <span className="block truncate text-[13px] text-ink-3">{off ? `${a.handle} · requiere reconexión` : a.handle}</span>
                      </span>
                    </label>
                  </li>
                );
              })}
            </ul>
          </fieldset>
          <p className="text-sm text-ink-3">Se publica con la descripción y los hashtags del clip.</p>
          {err && (
            <p role="alert" className="rounded-xl border border-bad/40 bg-bad-soft/60 px-3 py-2.5 text-sm text-bad">
              {err}
            </p>
          )}
        </div>
      )}
    </Dialog>
  );
}
