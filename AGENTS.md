# AGENTS.md

Guía para agentes de IA en **NovoClip** (repo `HenryAcevedo16/clipforge`): app que convierte videos/directos (YouTube, Twitch, Kick, TikTok o archivos) en clips verticales con subtítulos, encuadre inteligente, selección por IA y edición. Backend Python FastAPI (`app.py`, `pipeline.py`), frontend Next.js 16 exportado estático a `web/`. El usuario habla español; responde en español, breve, y ejecuta sin pedir confirmación en decisiones razonables.

## Reglas de coste (siempre)

1. **Lo mínimo de mayor impacto:** la menor salida que cumple el objetivo y lo demuestra.
2. Correctitud primero; no recortes lo que la tarea necesita.
3. Un checkpoint al terminar una tarea grande: commit + push, reescribe `docs/STATUS.md` (≤ 40 líneas) y decide `/clear` o seguir (skill `token-optimization`). Solo el usuario puede hacer `/clear`.
4. Decide tú los detalles pequeños y reversibles; pregunta solo si algo bloquea del todo.

## Protocolo

1. **Inicio:** `python3 scripts/start.py --entry AGENTS.md` (STATUS + mapa), luego solo lo necesario.
2. **Localiza** con `docs/MAP.md` y `grep -n`; `pipeline.py` tiene ~4500 líneas: nunca lo leas entero, usa rangos.
3. **Verifica en escalera:** archivo tocado → prueba dirigida → un chequeo completo al final.
4. **Cierre:** commit (autor `Claude <noreply@anthropic.com>`) → `git -c push.negotiate=true push -q origin main` → checkpoint.

## Reglas de tokens

- No leas: `web/` (compilado), `frontend/node_modules`, `.next`, `models/`, `jobs/`, lockfiles.
- Comandos silenciosos: `npx tsc --noEmit | head -30`, `python -m py_compile pipeline.py app.py`, `pytest -q -x`.
- Una llamada, no cinco: agrupa búsquedas y llamadas independientes; no releas lo que ya está en contexto.
- Frontend: edita `frontend/`, compila (copia a scratchpad con node_modules, `npx next build`) y copia `out` → `web/`.

## Mapa de documentos

| Necesidad | Leer |
|---|---|
| Estado y siguiente paso | `docs/STATUS.md` |
| Dónde está el código | `docs/MAP.md` (generado: `python3 scripts/gen_map.py --out docs/MAP.md`) |
| Uso y funciones de la app | `README.md` (secciones por función) |
| Optimizar coste/sesiones | `.claude/skills/token-optimization/SKILL.md` |
