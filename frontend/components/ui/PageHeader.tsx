import type { ReactNode } from "react";

export function PageHeader({ title, description, actions }: { title: string; description?: string; actions?: ReactNode }) {
  return (
    <header className="mb-7 flex flex-wrap items-end justify-between gap-x-6 gap-y-3 sm:mb-9">
      <div className="min-w-0">
        <h1 className="text-[1.9rem] font-extrabold leading-tight tracking-tight sm:text-[2.25rem]">{title}</h1>
        {description && <p className="mt-1.5 max-w-[60ch] text-[15px] text-ink-2">{description}</p>}
      </div>
      {actions && <div className="flex shrink-0 flex-wrap items-center gap-2">{actions}</div>}
    </header>
  );
}
