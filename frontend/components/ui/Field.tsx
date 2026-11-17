"use client";
import { inputVariants } from "@heroui/react";
import { useId, type ReactNode } from "react";
import { cn } from "./cn";

/** Campo de texto con el estilo de Input de HeroUI (borde visible en modo oscuro). */
export const inputClass = cn(
  inputVariants(),
  "w-full min-h-12 !rounded-2xl !border !border-line bg-raised px-4 text-base text-ink placeholder:text-ink-3 hover:!border-line-2 focus:!border-accent-hi aria-[invalid=true]:!border-bad disabled:opacity-50",
);

interface FieldProps {
  label: string;
  hint?: string;
  error?: string | null;
  className?: string;
  children: (a: { id: string; "aria-describedby"?: string; "aria-invalid"?: boolean }) => ReactNode;
}

export function Field({ label, hint, error, className, children }: FieldProps) {
  const id = useId();
  const descId = hint || error ? `${id}-d` : undefined;
  return (
    <div className={cn("flex flex-col gap-1.5", className)}>
      <label htmlFor={id} className="text-sm font-semibold text-ink-2">
        {label}
      </label>
      {children({ id, "aria-describedby": descId, "aria-invalid": error ? true : undefined })}
      {(error || hint) && (
        <p id={descId} className={cn("text-[13px] leading-snug", error ? "text-bad" : "text-ink-3")} role={error ? "alert" : undefined}>
          {error || hint}
        </p>
      )}
    </div>
  );
}
