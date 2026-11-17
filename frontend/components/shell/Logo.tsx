export function LogoMark({ className = "size-8" }: { className?: string }) {
  return (
    <span className={`brand-bg inline-grid shrink-0 place-items-center rounded-[28%] ${className}`} aria-hidden>
      <svg viewBox="0 0 32 32" className="size-[62%]">
        <path d="M9.5 23V9h3.1l7.8 8.9V9h3.1v14h-3.1l-7.8-8.9V23z" fill="#fff" />
      </svg>
    </span>
  );
}
