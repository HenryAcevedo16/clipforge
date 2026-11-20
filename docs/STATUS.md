# Status

**Milestone:** M1 â€” NovoClip estable en el PC real del dueÃ±o
**Next WP:** M1.2 — Verificar en su PC lo pendiente (encoder AMF, TikTok live, Gemini con video)
**Last done:** clips de directo editables (gancho, Optimizar con IA, Editar corte); directo con nota mÃ­nima 60 (commit 0248c8b)

## Start here (sesiÃ³n local nueva)

1. Eres Claude Code local en `C:\Users\emil-\Documents\novoclip` (Windows, AMD RX 9060 XT). Puedes ejecutar la app y probar de verdad.
2. Reproduce el problema: `.venv\Scripts\python -m yt_dlp -v -F "<url>"` (o `probar_youtube.bat`). Lee `yt_run()` en `pipeline.py` (cookies.txt â†’ clientes tv/web_safari/mweb â†’ navegadores).
3. YouTube bot-check ARREGLADO: la causa era que cookies.txt estaba en Descargas como www.youtube.com_cookies.txt; ahora pipeline lo busca ahí también (_find_cookies_file) y recuerda yt_cookies=file.

## Preguntas abiertas para el dueÃ±o

- Â¿La IA debe analizar el video completo para elegir clips (gameplay)? Â¿Optimizar sin mover los segundos del usuario?
- Â¿Editar posiciÃ³n/tamaÃ±o/color del gancho? Â¿Publicar por APIs oficiales (YouTube primero)? Â¿Instalador .exe?

## Notas de entorno

- Usuario: habla espaÃ±ol, quiere ejecuciÃ³n directa (sin pedir confirmaciÃ³n), respuestas breves con el resultado.
- Todo lo de `README.md` por funciones. Actualizar: `actualizar_windows.bat`; arrancar: `iniciar_windows.bat`; el arranque imprime la versiÃ³n (commit).
- Frontend: Next.js 16 estÃ¡tico en `frontend/` â†’ compilado a `web/` (hay que reconstruir y copiar `out` â†’ `web/`).
- Sin verificar en su PC: encoder AMF (BrokenPipe, pedir lÃ­nea "Motivo:"), TikTok live plan B, Gemini 4 con video, zoom de cÃ¡mara del streamer, Claude por suscripciÃ³n.
- Skills instaladas: token-optimization, model-router (sin Fable), graphify (grafo en `graphify-out/`; `graphify update .` tras cambios).
- Commits: autor `Claude <noreply@anthropic.com>`; push a `main`.

## Session log (newest first)

- 2026-11-20 — Reglas editables (reglas/, rules.py): glosario, plantillas de gancho (hook_options + botones), resaltado, guia_ia.md. 43 pruebas. Pendiente: probar en el PC y ajustar plantillas con videos reales.

- 2026-11-20 — Optimizar con IA repartido: Sonnet (corte), Haiku (textos), Opus (verifica); respaldo al modelo de siempre; env NOVOCLIP_MODEL_TECH/COPY/VERIFY. 30 pruebas. Pendiente probar en el PC que la suscripción permita --model opus/haiku y medir latencia/tokens.

- 2026-11-20 — Editar/Optimizar en videos normales sin volver a descargar (clip_src/), ganchos con sentido sin IA (_best_hook), nota absoluta sin IA. Revisado por Opus; 19 pruebas en verde. Pendiente: probar con un YouTube real en el PC; vigilar disco (≈20 s extra por clip).

- 2026-11-19 â€” YouTube bot-check: cookies.txt/clientes/Deno/yt-dlp --pre; probar_youtube.bat.
- 2026-11-18 â€” Directo editable; skills; banner Migajas Gaming (canal del dueÃ±o); versiÃ³n al arrancar.

