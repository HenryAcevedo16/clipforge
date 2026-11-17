"use client";
import { Button as HButton, buttonVariants } from "@heroui/react";
import { Loader2 } from "lucide-react";
import type { ReactNode } from "react";
import { cn } from "./cn";

export type Variant = "primary" | "secondary" | "ghost" | "danger";
export type Size = "md" | "sm";

const MAP = { primary: "primary", secondary: "secondary", ghost: "ghost", danger: "danger-soft" } as const;

/** Clases de HeroUI para <Link> con aspecto de botón. El primario lleva el degradado violeta→azul de la marca. */
export function buttonClass({ variant = "secondary", size = "md", full = false }: { variant?: Variant; size?: Size; full?: boolean } = {}) {
  return cn(
    buttonVariants({ variant: MAP[variant], size: size === "sm" ? "sm" : "md", fullWidth: full }),
    "font-semibold no-underline",
    variant === "primary" && "!bg-[image:var(--brand-gradient)] !text-white shadow-[0_8px_28px_-10px_var(--brand-glow)] hover:brightness-110",
    size === "md" ? "min-h-11" : "min-h-10",
  );
}

interface Props {
  variant?: Variant;
  size?: Size;
  full?: boolean;
  loading?: boolean;
  icon?: ReactNode;
  className?: string;
  children?: ReactNode;
  disabled?: boolean;
  onClick?: () => void;
  type?: "button" | "submit";
  "aria-label"?: string;
}

export function Button({ variant = "secondary", size = "md", full, loading, icon, className, children, disabled, onClick, type = "button", ...rest }: Props) {
  return (
    <HButton type={type} variant={MAP[variant]} size={size === "sm" ? "sm" : "md"} fullWidth={full} isDisabled={disabled || loading} onPress={() => onClick?.()} className={cn(buttonClass({ variant, size, full }), className)} {...rest}>
      {loading ? <Loader2 className="size-4 animate-spin motion-reduce:animate-none" aria-hidden /> : icon}
      {children}
    </HButton>
  );
}
