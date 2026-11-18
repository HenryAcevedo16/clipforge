# Status

**Milestone:** M1 — NovoClip estable y editable
**Next WP:** M1.1 — Verificar en PC real (encoder AMF, TikTok live, Gemini 4, cámara del streamer)
**Last done:** Optimizar con IA arregla recomendaciones de la revisión (3a6d744)

## Start here (next session)

1. Lee `README.md` solo en la sección de la función tocada; localiza código con `docs/MAP.md`.
2. Si el usuario reporta error, pide la línea "Motivo:" / `[IA]` del log.

## Open questions for the owner

- ¿La IA analiza el video completo para elegir clips (gameplay)? ¿Optimizar sin mover los segundos del usuario?
- ¿Editar posición/tamaño/color del gancho? ¿Publicación por APIs oficiales (YouTube primero)? ¿Instalador .exe?

## Environment notes

- Sandbox: sin internet a Google/TikTok; Playwright + `testserver_repo.py`/`testserver_ai.py` en puerto 8795.
- PC del usuario: Windows, AMD RX 9060 XT; actualiza con `git pull origin main`, `pip install -r requirements.txt`, Ctrl+F5.

## Session log (newest first)

- 2026-11-18 — Instalada la skill token-optimization (.claude/, AGENTS.md, CLAUDE.md, scripts/start.py, docs/MAP.md).
