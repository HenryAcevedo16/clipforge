"use client";
import { CalendarDays, Film, House, Palette, Plus, Settings, Share2 } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";
import { buttonClass } from "../ui/Button";
import { cn } from "../ui/cn";
import { LogoMark } from "./Logo";
import { MockSwitcher } from "./MockSwitcher";

const NAV = [
  { href: "/", label: "Inicio", short: "Inicio", icon: House },
  { href: "/proyectos", label: "Mis proyectos", short: "Proyectos", icon: Film },
  { href: "/marca", label: "Kit de marca", short: "Marca", icon: Palette },
  { href: "/calendario", label: "Calendario", short: "Calendario", icon: CalendarDays },
  { href: "/cuentas", label: "Cuentas de redes", short: "Cuentas", icon: Share2 },
  { href: "/ajustes", label: "Ajustes", short: "Ajustes", icon: Settings },
];

function isActive(path: string, href: string) {
  return href === "/" ? path === "/" : path === href || path.startsWith(href + "/");
}

export function AppShell({ children }: { children: ReactNode }) {
  const path = usePathname();
  return (
    <>
      {/* Escritorio: barra lateral */}
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-[var(--rail-w)] flex-col border-r border-line bg-shell px-4 py-5 lg:flex">
        <Link href="/" className="mb-6 flex items-center gap-3 rounded-xl px-1.5 py-1">
          <LogoMark className="size-10" />
          <span className="text-[1.4rem] font-extrabold tracking-tight">NovoClip</span>
        </Link>
        <Link href="/" className={cn(buttonClass({ variant: "primary", full: true }), "mb-6")}>
          <Plus className="size-5" aria-hidden />
          Nuevo proyecto
        </Link>
        <nav aria-label="Secciones" className="flex flex-col gap-1">
          {NAV.map(({ href, label, icon: Icon }) => {
            const on = isActive(path, href);
            return (
              <Link
                key={href}
                href={href}
                aria-current={on ? "page" : undefined}
                className={cn(
                  "flex min-h-12 items-center gap-3 rounded-2xl px-3.5 text-[15px] font-semibold transition-[background-color,color,transform] duration-150 ease-[var(--ease-out)] active:scale-[0.98]",
                  on ? "bg-surface-secondary text-ink shadow-[inset_0_0_0_1px_var(--color-line)]" : "text-ink-2 hover:bg-raised hover:text-ink",
                )}
              >
                <span className={cn("grid size-8 shrink-0 place-items-center rounded-xl transition-colors", on ? "brand-bg text-white" : "bg-raised text-ink-2")}>
                  <Icon className="size-[18px]" aria-hidden />
                </span>
                {label}
              </Link>
            );
          })}
        </nav>
        <div className="mt-auto rounded-2xl border border-line bg-raised p-3.5">
          <MockSwitcher />
        </div>
      </aside>

      {/* Celular: barra superior mínima */}
      <header className="sticky top-0 z-30 flex items-center justify-between gap-3 border-b border-line bg-shell/90 px-4 py-2.5 pt-[max(0.625rem,env(safe-area-inset-top))] backdrop-blur-md lg:hidden">
        <Link href="/" className="flex items-center gap-2">
          <LogoMark className="size-8" />
          <span className="text-lg font-extrabold tracking-tight">NovoClip</span>
        </Link>
        <MockSwitcher className="w-44" />
      </header>

      <main className="min-h-dvh pb-[calc(var(--bar-h)+env(safe-area-inset-bottom)+2rem)] lg:pb-14 lg:pl-[var(--rail-w)]">
        <div className="mx-auto w-full max-w-[1180px] px-4 pb-4 pt-6 sm:px-6 lg:px-10 lg:pt-10">{children}</div>
      </main>

      {/* Celular: barra inferior flotante de 5 secciones */}
      <nav aria-label="Secciones" className="fixed inset-x-3 bottom-[max(0.75rem,env(safe-area-inset-bottom))] z-30 select-none rounded-3xl border border-line bg-shell/92 shadow-[0_16px_40px_-12px_rgb(0_0_0/0.7)] backdrop-blur-md lg:hidden">
        <ul className="grid h-[calc(var(--bar-h)-0.5rem)] grid-cols-6 p-1.5">
          {NAV.map(({ href, short, icon: Icon }) => {
            const on = isActive(path, href);
            return (
              <li key={href}>
                <Link
                  href={href}
                  aria-current={on ? "page" : undefined}
                  className={cn("flex h-full flex-col items-center justify-center gap-0.5 rounded-2xl text-[11px] font-semibold transition-[background-color,color,transform] duration-150 active:scale-[0.95]", on ? "bg-surface-secondary text-ink" : "text-ink-3")}
                >
                  <Icon className={cn("size-[21px]", on && "text-accent-hi")} aria-hidden />
                  <span>{short}</span>
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>
    </>
  );
}
