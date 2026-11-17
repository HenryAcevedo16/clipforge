"use client";
import { Card, Skeleton as HSkeleton } from "@heroui/react";
import { AlertTriangle, RotateCw } from "lucide-react";
import type { ReactNode } from "react";
import { Button } from "./Button";
import { cn } from "./cn";

export function EmptyState({ icon, title, text, action, className }: { icon: ReactNode; title: string; text: string; action?: ReactNode; className?: string }) {
  return (
    <Card className={cn("anim-fade items-center gap-3 border border-dashed border-line-2 bg-raised/60 px-6 py-14 text-center shadow-none", className)}>
      <div className="brand-bg grid size-14 place-items-center rounded-2xl text-white shadow-[0_10px_30px_-10px_var(--brand-glow)] [&_svg]:size-7" aria-hidden>
        {icon}
      </div>
      <h2 className="text-xl font-bold">{title}</h2>
      <p className="max-w-[44ch] text-ink-2">{text}</p>
      {action && <div className="mt-1">{action}</div>}
    </Card>
  );
}

export function ErrorState({ message, onRetry, title = "No pudimos cargar esto" }: { message: string; onRetry?: () => void; title?: string }) {
  return (
    <div role="alert" className="anim-fade flex flex-col items-start gap-3 rounded-3xl border border-bad/40 bg-bad-soft/60 p-5 sm:flex-row sm:items-center">
      <AlertTriangle className="size-6 shrink-0 text-bad" aria-hidden />
      <div className="min-w-0 flex-1">
        <h2 className="font-bold">{title}</h2>
        <p className="break-words text-ink-2">{message}</p>
      </div>
      {onRetry && (
        <Button onClick={onRetry} icon={<RotateCw className="size-4" aria-hidden />}>
          Intentar de nuevo
        </Button>
      )}
    </div>
  );
}

export function Skeleton({ className }: { className?: string }) {
  return <HSkeleton aria-hidden className={cn("rounded-3xl", className)} />;
}

export function LoadingLabel({ text = "Cargando…" }: { text?: string }) {
  return (
    <p role="status" className="sr-only">
      {text}
    </p>
  );
}
