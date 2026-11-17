"use client";
import { Check, Copy, Download, ExternalLink } from "lucide-react";
import { useState, type ReactNode } from "react";
import { api, type ClipResult } from "@/lib/api";
import { PlatformIcon } from "../ui/PlatformPill";
import { Button } from "../ui/Button";
import { Dialog } from "../ui/Dialog";
import { useToast } from "../ui/Toast";

const clipText = (c: ClipResult) => `${c.caption || c.title}\n\n${c.hashtags.join(" ")}`.trim();

interface Net {
  id: string;
  label: string;
  url: string;
  tip: string;
  icon: ReactNode;
  color: string;
}

const svg = { viewBox: "0 0 24 24", className: "size-5 shrink-0", "aria-hidden": true, fill: "currentColor" } as const;
const NETS: Net[] = [
  { id: "tiktok", label: "TikTok", url: "https://www.tiktok.com/tiktokstudio/upload", tip: "Arrastra el video y pega el texto en la descripción.", icon: <PlatformIcon id="tiktok" className="size-5" />, color: "#25F4EE" },
  { id: "youtube", label: "YouTube Shorts", url: "https://www.youtube.com/upload", tip: "Sube el video (si dura menos de 3 min y es vertical, sale como Short) y pega el texto.", icon: <PlatformIcon id="youtube" className="size-5" />, color: "#FF3B3B" },
  {
    id: "instagram",
    label: "Instagram Reels",
    url: "https://www.instagram.com/",
    tip: "Pulsa el «+» (Crear), elige Reel, sube el video y pega el texto.",
    color: "#E1306C",
    icon: (
      <svg {...svg} fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
        <rect x="3.5" y="3.5" width="17" height="17" rx="5" />
        <circle cx="12" cy="12" r="4" />
        <circle cx="17.2" cy="6.8" r="0.6" fill="currentColor" />
      </svg>
    ),
  },
  {
    id: "facebook",
    label: "Facebook Reels",
    url: "https://www.facebook.com/reels/create",
    tip: "Sube el video y pega el texto como descripción.",
    color: "#1877F2",
    icon: (
      <svg {...svg}>
        <path d="M13.5 21v-7.5h2.6l.4-3h-3V8.700c0-.9.3-1.500 1.600-1.500h1.500V4.500c-.3 0-1.200-.1-2.200-.1-2.300 0-3.800 1.400-3.800 3.900v2.200H8v3h2.600V21h2.900Z" />
      </svg>
    ),
  },
  {
    id: "x",
    label: "X (Twitter)",
    url: "https://x.com/compose/post",
    tip: "Adjunta el video con el icono de imagen y pega el texto.",
    color: "#FFFFFF",
    icon: (
      <svg {...svg}>
        <path d="M17.800 3h3l-6.600 7.600L22 21h-6l-4.700-6.100L5.900 21h-3l7-8.100L2 3h6.200l4.300 5.600L17.800 3Zm-1 16.200h1.700L7.300 4.700H5.500l11.300 14.500Z" />
      </svg>
    ),
  },
];

/**
 * Publicación asistida: al elegir una red se abre en una ventana nueva su página de subir video,
 * se descarga el clip y se copia el texto (título, descripción y hashtags) para pegarlo.
 */
export function PublishDialog({ jobId, clip, onClose }: { jobId: string; clip: ClipResult; onClose: () => void }) {
  const toast = useToast();
  const [done, setDone] = useState<string | null>(null);

  const download = () => {
    const a = document.createElement("a");
    a.href = api.fileUrl(jobId, clip.file, { download: true });
    a.download = clip.file;
    document.body.appendChild(a);
    a.click();
    a.remove();
  };

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(clipText(clip));
      return true;
    } catch {
      return false;
    }
  };

  const go = async (n: Net) => {
    window.open(n.url, "_blank", "noopener,noreferrer"); // primero, dentro del clic: si no, el navegador bloquea la ventana
    download();
    const ok = await copy();
    setDone(n.id);
    toast(ok ? `${n.label}: video descargado y texto copiado.` : `${n.label}: video descargado. No pude copiar el texto: usa «Copiar texto».`, ok ? undefined : "bad");
  };

  const sel = NETS.find((n) => n.id === done);
  return (
    <Dialog open onClose={onClose} title="Publicar este clip">
      <div className="flex flex-col gap-4">
        <p className="text-ink-2">Elige la red: se abre en una ventana nueva la página para subir videos, se descarga el clip y se copia el texto para que solo tengas que arrastrar y pegar.</p>
        <ul className="grid gap-2 sm:grid-cols-2">
          {NETS.map((n) => (
            <li key={n.id}>
              <button
                type="button"
                onClick={() => go(n)}
                className="flex min-h-14 w-full items-center gap-3 rounded-2xl border border-line bg-raised-2/60 px-4 text-left font-bold transition-[border-color,background-color,transform] duration-150 hover:border-accent-hi hover:bg-accent-soft active:scale-[0.98] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent-hi"
              >
                <span style={{ color: n.color }}>{n.icon}</span>
                <span className="min-w-0 flex-1 truncate">{n.label}</span>
                {done === n.id ? <Check className="size-4 text-ok" aria-hidden /> : <ExternalLink className="size-4 text-ink-3" aria-hidden />}
              </button>
            </li>
          ))}
        </ul>
        {sel && (
          <p role="status" className="rounded-2xl border border-ok/30 bg-ok-soft/60 p-3.5 text-sm text-ink-2">
            <b className="text-ink">{sel.label}:</b> {sel.tip} Si la ventana no se abrió, permite las ventanas emergentes de esta página.
          </p>
        )}
        <div className="flex flex-wrap gap-2">
          <Button size="sm" onClick={download} icon={<Download className="size-4" aria-hidden />}>
            Descargar de nuevo
          </Button>
          <Button size="sm" onClick={async () => toast((await copy()) ? "Texto copiado." : "No pude copiar el texto.")} icon={<Copy className="size-4" aria-hidden />}>
            Copiar texto
          </Button>
        </div>
      </div>
    </Dialog>
  );
}
