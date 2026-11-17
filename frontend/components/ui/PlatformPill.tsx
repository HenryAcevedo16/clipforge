import type { PlatformId, PlatformInfo } from "@/lib/platform";
import { cn } from "./cn";

/** Ícono de cada plataforma (trazos simples, a un solo color). */
export function PlatformIcon({ id, className }: { id: PlatformId; className?: string }) {
  const p = { viewBox: "0 0 24 24", className: cn("size-4 shrink-0", className), "aria-hidden": true, fill: "currentColor" } as const;
  switch (id) {
    case "youtube":
      return (
        <svg {...p}>
          <path d="M21.6 7.2a2.5 2.5 0 0 0-1.76-1.77C18.3 5 12 5 12 5s-6.3 0-7.84.43A2.5 2.5 0 0 0 2.4 7.2C2 8.75 2 12 2 12s0 3.25.4 4.8a2.5 2.5 0 0 0 1.76 1.77C5.7 19 12 19 12 19s6.3 0 7.84-.43a2.5 2.5 0 0 0 1.76-1.77C22 15.25 22 12 22 12s0-3.25-.4-4.8ZM10 15V9l5.2 3L10 15Z" />
        </svg>
      );
    case "twitch":
      return (
        <svg {...p}>
          <path d="M4 3 3 6.5V19h4v2.5h2.5L12 19h3.5L21 13.5V3H4Zm15 9.5-3 3h-4.5l-2.5 2.5v-2.5H6.5V5H19v7.5ZM15 7.5h1.8v5H15v-5Zm-4.5 0h1.8v5h-1.8v-5Z" />
        </svg>
      );
    case "kick":
      return (
        <svg {...p}>
          <path d="M4 3h5v6l2.5-3H17l-4.2 5L17.5 18h-5.7L9 14.5V18H4V3Z" />
        </svg>
      );
    case "tiktok":
      return (
        <svg {...p}>
          <path d="M16.6 3a5.2 5.2 0 0 0 4 4.6v3.2a8.3 8.3 0 0 1-4-1.2v6.2a6 6 0 1 1-6-6c.3 0 .6 0 .9.1v3.3a2.8 2.8 0 1 0 1.9 2.6V3h3.2Z" />
        </svg>
      );
  }
}

/** Pastilla "YouTube · EN VIVO" que aparece junto al enlace cuando se reconoce la plataforma. */
export function PlatformPill({ info, className }: { info: PlatformInfo; className?: string }) {
  return (
    <span
      className={cn("inline-flex shrink-0 items-center gap-1.5 rounded-full border bg-raised-2 px-2.5 py-1 text-xs font-bold text-ink", className)}
      style={{ borderColor: `color-mix(in srgb, ${info.color} 55%, transparent)` }}
    >
      <span style={{ color: info.color }}>
        <PlatformIcon id={info.id} />
      </span>
      {info.label}
      {info.kind === "live" && (
        <span className="ml-0.5 inline-flex items-center gap-1 rounded-full bg-bad-soft px-1.5 py-px text-[10px] font-extrabold tracking-wide text-bad">
          <span className="size-1.5 rounded-full bg-bad motion-safe:animate-pulse" aria-hidden />
          EN VIVO
        </span>
      )}
    </span>
  );
}
