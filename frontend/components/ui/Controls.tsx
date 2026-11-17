"use client";
import { Slider } from "@heroui/react";
import { useId, type ReactNode } from "react";
import { cn } from "./cn";

/** Grupo de opciones excluyentes (radios nativos con aspecto de píldoras). */
export function Segmented<T extends string>({ label, value, onChange, options, className }: { label: string; value: T; onChange: (v: T) => void; options: { value: T; label: ReactNode; sub?: string }[]; className?: string }) {
  const name = useId();
  return (
    <fieldset className={cn("min-w-0", className)}>
      <legend className="mb-2 text-sm font-semibold text-ink-2">{label}</legend>
      <div className="flex flex-wrap gap-2">
        {options.map((o) => (
          <label key={o.value} className="relative cursor-pointer">
            <input type="radio" name={name} value={o.value} checked={value === o.value} onChange={() => onChange(o.value)} className="peer sr-only" />
            <span className="flex min-h-12 min-w-16 flex-col items-center justify-center rounded-2xl border border-line bg-raised px-4 py-1.5 text-center text-[15px] font-bold text-ink-2 transition-[transform,border-color,background-color,color] duration-150 ease-[var(--ease-out)] active:scale-[0.97] hover:border-line-2 peer-checked:border-transparent peer-checked:bg-accent-soft peer-checked:text-ink peer-checked:shadow-[inset_0_0_0_1.5px_var(--accent)] peer-focus-visible:outline-2 peer-focus-visible:outline-offset-2 peer-focus-visible:outline-accent-hi">
              {o.label}
              {o.sub && <span className="text-xs font-medium text-ink-3">{o.sub}</span>}
            </span>
          </label>
        ))}
      </div>
    </fieldset>
  );
}

/**
 * Interruptor propio (no el de HeroUI): se puede pulsar tanto en el botón como en el texto.
 * Con el de HeroUI solo respondía el texto y pulsar el botón no hacía nada.
 */
export function Switch({ checked, onChange, label, hint, disabled }: { checked: boolean; onChange: (v: boolean) => void; label: string; hint?: string; disabled?: boolean }) {
  const id = useId();
  const toggle = () => !disabled && onChange(!checked);
  return (
    <div className={cn("flex w-full items-start gap-3", disabled && "opacity-50")}>
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        aria-labelledby={`${id}-l`}
        aria-describedby={hint ? `${id}-h` : undefined}
        disabled={disabled}
        onClick={toggle}
        className={cn(
          "relative mt-0.5 h-6 w-10 shrink-0 cursor-pointer rounded-full transition-colors duration-200 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent-hi disabled:cursor-not-allowed",
          checked ? "bg-accent" : "bg-line-2",
        )}
      >
        <span aria-hidden className={cn("absolute left-0.5 top-0.5 size-5 rounded-full bg-white shadow transition-transform duration-200 ease-[var(--ease-out)]", checked && "translate-x-4")} />
      </button>
      <div onClick={toggle} className={cn("flex min-w-0 flex-1 select-none flex-col items-start text-left", disabled ? "cursor-not-allowed" : "cursor-pointer")}>
        <span id={`${id}-l`} className="block text-[15px] font-semibold text-ink">{label}</span>
        {hint && <span id={`${id}-h`} className="block text-[13px] font-normal leading-snug text-ink-3">{hint}</span>}
      </div>
    </div>
  );
}

/** Deslizador de HeroUI. */
export function Range({ label, value, onChange, min, max, step = 1, unit = "" }: { label: string; value: number; onChange: (v: number) => void; min: number; max: number; step?: number; unit?: string }) {
  return (
    <Slider value={value} onChange={(v) => onChange(Array.isArray(v) ? v[0] : v)} minValue={min} maxValue={max} step={step} className="w-full">
      <div className="mb-1 flex items-baseline justify-between gap-2">
        <Slider.Output className="sr-only" />
        <span className="text-sm font-semibold text-ink-2">{label}</span>
        <span className="tnum text-sm font-bold text-ink">
          {value}
          {unit}
        </span>
      </div>
      <Slider.Track>
        <Slider.Fill />
        <Slider.Thumb aria-label={label} />
      </Slider.Track>
    </Slider>
  );
}
