# Status

**Milestone:** M1 — NovoClip estable en el PC real del dueño
**Next WP:** M1.1 — Arreglar la descarga de YouTube ("Sign in to confirm you're not a bot") en su PC
**Last done:** clips de directo editables (gancho, Optimizar con IA, Editar corte); directo con nota mínima 60 (commit 0248c8b)

## Start here (sesión local nueva)

1. Eres Claude Code local en `C:\Users\emil-\Documents\novoclip` (Windows, AMD RX 9060 XT). Puedes ejecutar la app y probar de verdad.
2. Reproduce el problema: `.venv\Scripts\python -m yt_dlp -v -F "<url>"` (o `probar_youtube.bat`). Lee `yt_run()` en `pipeline.py` (cookies.txt → clientes tv/web_safari/mweb → navegadores).
3. Estado de ese bug: Deno instalado, yt-dlp actualizado con `--pre`, `cookies.txt` exportado (en la carpeta; NO subir a git). Aún falla; falta ver el informe `diagnostico_youtube.txt`. Si es la IP/VPN, la salida es subir el video como archivo.

## Preguntas abiertas para el dueño

- ¿La IA debe analizar el video completo para elegir clips (gameplay)? ¿Optimizar sin mover los segundos del usuario?
- ¿Editar posición/tamaño/color del gancho? ¿Publicar por APIs oficiales (YouTube primero)? ¿Instalador .exe?

## Notas de entorno

- Usuario: habla español, quiere ejecución directa (sin pedir confirmación), respuestas breves con el resultado.
- Todo lo de `README.md` por funciones. Actualizar: `actualizar_windows.bat`; arrancar: `iniciar_windows.bat`; el arranque imprime la versión (commit).
- Frontend: Next.js 16 estático en `frontend/` → compilado a `web/` (hay que reconstruir y copiar `out` → `web/`).
- Sin verificar en su PC: encoder AMF (BrokenPipe, pedir línea "Motivo:"), TikTok live plan B, Gemini 4 con video, zoom de cámara del streamer, Claude por suscripción.
- Skills instaladas: token-optimization, model-router (sin Fable), graphify (grafo en `graphify-out/`; `graphify update .` tras cambios).
- Commits: autor `Claude <noreply@anthropic.com>`; push a `main`.

## Session log (newest first)

- 2026-11-19 — YouTube bot-check: cookies.txt/clientes/Deno/yt-dlp --pre; probar_youtube.bat.
- 2026-11-18 — Directo editable; skills; banner Migajas Gaming (canal del dueño); versión al arrancar.
