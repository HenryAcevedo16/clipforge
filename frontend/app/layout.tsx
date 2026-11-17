import type { Metadata, Viewport } from "next";
import "@fontsource-variable/manrope";
import "./globals.css";
import { AppShell } from "@/components/shell/AppShell";
import { ToastProvider } from "@/components/ui/Toast";

export const metadata: Metadata = {
  title: { default: "NovoClip", template: "%s · NovoClip" },
  description: "Convierte un video largo en clips verticales listos para TikTok, Shorts y Reels.",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
  themeColor: "#0c0b12",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es" className="dark" data-theme="dark">
      <body>
        <a href="#contenido" className="sr-only focus:not-sr-only focus:fixed focus:left-3 focus:top-3 focus:z-50 focus:rounded-lg focus:bg-accent focus:px-4 focus:py-2 focus:text-white">
          Saltar al contenido
        </a>
        <ToastProvider>
          <AppShell>
            <div id="contenido" tabIndex={-1}>
              {children}
            </div>
          </AppShell>
        </ToastProvider>
      </body>
    </html>
  );
}
