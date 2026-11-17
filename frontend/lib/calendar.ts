import type { ScheduledPost } from "./api/types";
import { fromSD, pad, toSD, ymd, type SDParts } from "./time";

export interface Day {
  y: number;
  m: number;
  d: number;
  key: string; // 2026-11-16
  inMonth: boolean;
}

/** Aritmética de días sin zona horaria (solo fecha): se usa UTC como "calendario neutro". */
const addDays = (y: number, m: number, d: number, n: number) => {
  const x = new Date(Date.UTC(y, m, d + n));
  return { y: x.getUTCFullYear(), m: x.getUTCMonth(), d: x.getUTCDate() };
};

const dowMon = (y: number, m: number, d: number) => (new Date(Date.UTC(y, m, d)).getUTCDay() + 6) % 7; // 0 = lunes

const mk = (p: { y: number; m: number; d: number }, month: number): Day => ({ ...p, key: ymd(p), inMonth: p.m === month });

/** Cuadrícula del mes: semanas completas, lunes primero. */
export function monthGrid(y: number, m: number): Day[] {
  const lead = dowMon(y, m, 1);
  const total = new Date(Date.UTC(y, m + 1, 0)).getUTCDate();
  const weeks = Math.ceil((lead + total) / 7);
  return Array.from({ length: weeks * 7 }, (_, i) => mk(addDays(y, m, 1, i - lead), m));
}

export function weekDays(c: { y: number; m: number; d: number }): Day[] {
  const start = addDays(c.y, c.m, c.d, -dowMon(c.y, c.m, c.d));
  return Array.from({ length: 7 }, (_, i) => mk(addDays(start.y, start.m, start.d, i), c.m));
}

export function shiftCursor(c: { y: number; m: number; d: number }, view: "month" | "week", dir: -1 | 1) {
  return view === "month" ? addDays(c.y, c.m + dir, 1, 0) : addDays(c.y, c.m, c.d, 7 * dir);
}

export function groupByDay(posts: ScheduledPost[]): Map<string, ScheduledPost[]> {
  const map = new Map<string, ScheduledPost[]>();
  for (const p of [...posts].sort((a, b) => +new Date(a.at) - +new Date(b.at))) {
    const k = ymd(toSD(p.at));
    map.set(k, [...(map.get(k) ?? []), p]);
  }
  return map;
}

export function keyOf(p: SDParts | Day) {
  return ymd(p);
}

/** "2026-11-16" + "18:30" (hora de RD) -> ISO UTC */
export function isoFromInputs(date: string, time: string): string | null {
  const m = date.match(/^(\d{4})-(\d{2})-(\d{2})$/);
  const t = time.match(/^(\d{2}):(\d{2})$/);
  if (!m || !t) return null;
  return fromSD(+m[1], +m[2] - 1, +m[3], +t[1], +t[2]).toISOString();
}

export function inputsFromIso(iso: string) {
  const p = toSD(iso);
  return { date: `${p.y}-${pad(p.m + 1)}-${pad(p.d)}`, time: `${pad(p.h)}:${pad(p.min)}` };
}
