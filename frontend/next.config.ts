import type { NextConfig } from "next";

/**
 * Producción (`npm run build`): páginas estáticas en `out/`, que el servidor de la app (app.py) sirve en el
 * mismo origen que la API: no hace falta Node para usarla ni configurar CORS.
 * Desarrollo (`npm run dev`): con NEXT_PUBLIC_USE_MOCK=false, /api y /files se reenvían a BACKEND_URL.
 */
const backend = process.env.BACKEND_URL ?? "http://127.0.0.1:8000";
const isProd = process.env.NODE_ENV === "production";

const config: NextConfig = {
  reactStrictMode: true,
  devIndicators: false,
  ...(isProd ? { output: "export" as const, trailingSlash: true, images: { unoptimized: true } } : {}),
  ...(!isProd && process.env.NEXT_PUBLIC_USE_MOCK === "false"
    ? {
        async rewrites() {
          return [
            { source: "/api/:path*", destination: `${backend}/api/:path*` },
            { source: "/files/:path*", destination: `${backend}/files/:path*` },
          ];
        },
      }
    : {}),
};

export default config;
