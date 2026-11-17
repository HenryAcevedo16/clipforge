"use client";
import { useEffect, useState } from "react";
import type { FontId, SubtitleStyleId, WatermarkPosition } from "@/lib/api/types";
import { FONT_META, STYLE_META } from "@/lib/brand";
import { cn } from "../ui/cn";

export interface PreviewProps {
  style: SubtitleStyleId;
  fontId?: FontId;
  colors?: { text: string; highlight: string };
  logo?: string | null;
  watermark?: { enabled: boolean; position: WatermarkPosition; size: number; opacity: number };
  hook?: string;
  poster?: string;
  className?: string;
  /** Anima la palabra activa (se detiene con "reducir movimiento"). */
  animate?: boolean;
  words?: string[];
}

const POS: Record<WatermarkPosition, string> = {
  tl: "left-[6%] top-[5%]",
  tr: "right-[6%] top-[5%]",
  bl: "left-[6%] bottom-[5%]",
  br: "right-[6%] bottom-[5%]",
  center: "left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2",
};

/**
 * Vista previa en vivo de la plantilla sobre un clip vertical de ejemplo.
 * Dibuja los subtítulos con HTML/CSS; el render real lo hace FFmpeg (pipeline.build_ass), así que es una aproximación.
 */
export function ClipPreview({ style, fontId = "arial-black", colors, logo, watermark, hook = "PERDÍ 200 MIL EN UN MES", poster = "/mock/clips/a.jpg", className, animate = true, words = ["ESTO", "CAMBIÓ", "TODO", "PARA MÍ"] }: PreviewProps) {
  const [active, setActive] = useState(1);
  useEffect(() => {
    if (!animate || style === "none") return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const t = setInterval(() => setActive((a) => (a + 1) % words.length), 650);
    return () => clearInterval(t);
  }, [animate, style, words.length]);

  const font = FONT_META[fontId];
  const hi = colors?.highlight ?? STYLE_META[style].highlight;
  const txt = colors?.text ?? "#FFFFFF";
  const wm = watermark?.enabled ? watermark : null;

  const base: React.CSSProperties = { fontFamily: font.css, fontWeight: font.weight, textTransform: style === "minimal" && !font.upper ? "none" : "uppercase" };
  const outline = style === "neon" ? "#0A0A40" : "#000";
  const strokeW = style === "viral" ? 4 : style === "karaoke" ? 3.5 : style === "neon" ? 3 : style === "minimal" ? 1.8 : 0;

  return (
    <div className={cn("relative aspect-[9/16] overflow-hidden rounded-[18px] bg-black ring-1 ring-line [container-type:inline-size]", className)}>
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img src={poster} alt="" className="absolute inset-0 size-full object-cover" />
      <div aria-hidden className="absolute inset-0 bg-gradient-to-b from-black/45 via-transparent to-black/55" />
      {hook && (
        <p aria-hidden className={cn("absolute inset-x-[7%] text-center text-[clamp(10px,6.2cqw,26px)] leading-[1.05] text-white [text-shadow:0_2px_8px_rgb(0_0_0/0.8)]", wm && (wm.position === "tl" || wm.position === "tr") ? "top-[24%]" : "top-[9%]")} style={base}>
          {hook}
        </p>
      )}
      {style !== "none" && (
        <p
          aria-hidden
          className="absolute inset-x-[6%] bottom-[24%] flex flex-wrap justify-center gap-x-[0.45em] gap-y-[0.1em] text-center text-[clamp(14px,10cqw,44px)] leading-[1.08]"
          style={base}
        >
          {words.map((w, i) => {
            const on = i === active;
            const common: React.CSSProperties = {
              color: on ? hi : txt,
              WebkitTextStroke: strokeW ? `${strokeW / 2.2}px ${outline}` : undefined,
              paintOrder: "stroke fill",
              textShadow: style === "neon" ? `0 0 10px ${hi}, 0 0 22px ${hi}66` : style === "viral" ? "0 3px 0 rgb(0 0 0 / .6)" : style === "minimal" ? "0 2px 6px rgb(0 0 0 / .7)" : undefined,
              transform: on && style === "viral" ? "scale(1.08)" : undefined,
              transition: "transform 160ms var(--ease-out), color 120ms",
              display: "inline-block",
              fontSize: style === "minimal" ? "0.78em" : undefined,
            };
            if (style === "caja") return (
              <span key={i} className="rounded-[0.18em] px-[0.22em] py-[0.04em]" style={{ ...common, background: on ? hi : "rgb(0 0 0 / .78)", color: on ? "#000" : txt, WebkitTextStroke: undefined }}>
                {w}
              </span>
            );
            return (
              <span key={i} style={common}>
                {w}
              </span>
            );
          })}
        </p>
      )}
      {wm && (
        <div className={cn("absolute", POS[wm.position])} style={{ width: `${wm.size}%`, opacity: wm.opacity / 100 }}>
          {logo ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={logo} alt="" className="block w-full" />
          ) : (
            <div className="grid aspect-square w-full place-items-center rounded-lg border border-dashed border-white/70 text-[9px] font-bold text-white/80">LOGO</div>
          )}
        </div>
      )}
      <span className="absolute bottom-2 left-2 rounded bg-black/55 px-1.5 py-0.5 text-[10px] font-medium text-white/80">Ejemplo</span>
    </div>
  );
}
