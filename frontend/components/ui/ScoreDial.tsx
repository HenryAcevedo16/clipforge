import { cn } from "./cn";

export function scoreTone(n: number) {
  return n >= 80 ? "ok" : n >= 50 ? "warn" : "bad";
}

/**
 * Puntaje 0–100 como anillo (como el "puntaje de viralidad" de OpusClip). El arco se llena en proporción al número;
 * el color sigue el nivel: verde ≥ 80, ámbar 50–79, rojo < 50.
 */
export function ScoreDial({ score, size = 56, label = "Nota de la IA", className }: { score: number; size?: number; label?: string; className?: string }) {
  const n = Math.max(0, Math.min(100, Math.round(score)));
  const r = 20;
  const c = 2 * Math.PI * r;
  const tone = scoreTone(n);
  const color = tone === "ok" ? "var(--color-ok)" : tone === "warn" ? "var(--color-warn)" : "var(--color-bad)";
  return (
    <div className={cn("relative shrink-0", className)} style={{ width: size, height: size }} role="img" aria-label={`${label}: ${n} de 100`}>
      <svg viewBox="0 0 48 48" className="size-full -rotate-90">
        <circle cx="24" cy="24" r={r} fill="none" stroke="var(--color-line)" strokeWidth="4.5" />
        <circle cx="24" cy="24" r={r} fill="none" stroke={color} strokeWidth="4.5" strokeLinecap="round" strokeDasharray={`${(n / 100) * c} ${c}`} className="transition-[stroke-dasharray] duration-500 ease-[var(--ease-out)]" />
      </svg>
      <span className="num absolute inset-0 grid place-items-center text-ink" style={{ fontSize: size * 0.36 }}>
        {n}
      </span>
    </div>
  );
}
