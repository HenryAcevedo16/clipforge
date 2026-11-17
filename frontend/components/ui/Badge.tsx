import { Chip } from "@heroui/react";
import type { ReactNode } from "react";
import { cn } from "./cn";

export type Tone = "neutral" | "ok" | "warn" | "bad" | "accent";

const COLOR = { neutral: "default", ok: "success", warn: "warning", bad: "danger", accent: "accent" } as const;

/** Etiqueta de estado: Chip de HeroUI. `live` agrega un punto que parpadea (proceso en curso). */
export function Badge({ tone = "neutral", children, icon, live, className }: { tone?: Tone; children: ReactNode; icon?: ReactNode; live?: boolean; className?: string }) {
  return (
    <Chip color={COLOR[tone]} variant="soft" size="sm" className={cn("max-w-full font-semibold", className)}>
      {live ? <span aria-hidden className="size-1.5 shrink-0 rounded-full bg-current motion-safe:animate-[pulse-dot_1.4s_ease-in-out_infinite]" /> : icon}
      <Chip.Label className="truncate">{children}</Chip.Label>
    </Chip>
  );
}
