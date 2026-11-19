# AGENTS.md

Guía para agentes de IA en **NovoClip / ClipForge** (repo `HenryAcevedo16/clipforge`): aplicación que convierte videos y directos (YouTube, Twitch, Kick, TikTok o archivos) en clips con selección IA, subtítulos, encuadre inteligente y edición. Backend Python/FastAPI (`app.py`, `pipeline.py`); frontend Next.js 16, React 19 y TypeScript exportado a `web/`. El usuario habla español; responde en español y ejecuta decisiones pequeñas y reversibles sin pedir confirmación.

## Equipo de desarrollo

- **Opus — Arquitecto/coordinador:** define solución, criterios de aceptación, riesgos y descomposición para tareas no triviales.
- **Haiku — Investigador:** localiza código, contratos, documentación, logs y pruebas. Trabajo acotado y verificable; no diseña arquitectura.
- **Sonnet — Desarrollador:** implementación principal, pruebas y correcciones.
- **Sonnet — Revisor:** revisa el diff de forma independiente, no implementa arreglos y devuelve hallazgos con archivo:línea.
- Flujo y reglas completas: `docs/AI_TEAM.md`. Asignación: `.claude/skills/model-router/SKILL.md`.

## Reglas de coste (siempre)

1. **Lo mínimo de mayor impacto:** la menor salida que cumple el objetivo y lo demuestra.
2. Correctitud primero; no recortes lo que la tarea necesita.
3. No invoques subagentes cuando una lectura pequeña o un comando resuelvan la tarea más barato.
4. Limita las respuestas de subagentes a hallazgos, rutas/líneas, decisiones y próximos pasos; no copies archivos completos.
5. Un checkpoint al terminar una tarea grande: actualizar `docs/STATUS.md` (≤ 40 líneas), revisar `/usage` y la skill `token-optimization`; recomendar `/clear` o seguir. Solo el usuario puede ejecutar `/clear`.

## Protocolo

1. **Inicio:** `python3 scripts/start.py --entry AGENTS.md` (STATUS + mapa), luego solo lo necesario.
2. **Exploración:** consulta Graphify según `CLAUDE.md`; localiza con `docs/MAP.md` y `grep -n`. `pipeline.py` es grande: nunca lo leas entero, usa rangos.
3. **Plan:** para cambios no triviales, Opus define alcance y criterios; Haiku investiga si hay exploración mecánica relevante.
4. **Implementación:** Sonnet modifica una unidad coherente y añade/actualiza pruebas.
5. **Revisión:** Sonnet Reviewer inspecciona el diff y no modifica archivos. Sonnet corrige hallazgos confirmados. Opus participa de nuevo solo ante riesgo arquitectónico, seguridad o alto impacto.
6. **Verificación en escalera:** archivo tocado → prueba dirigida → un chequeo completo al final. No afirmes que una prueba pasó si no se ejecutó.
7. **Cierre:** actualizar docs de estado/mapa cuando corresponda y Graphify después de cambios de código. No hacer push ni operaciones destructivas sin instrucción expresa del usuario.

## Reglas de tokens y archivos

- No leas `web/` (compilado), `frontend/node_modules`, `.next`, `models/`, `jobs/` ni lockfiles salvo necesidad concreta.
- Comandos silenciosos: `npx tsc --noEmit | head -30`, `python -m py_compile pipeline.py app.py`, `pytest -q -x`.
- Una llamada, no cinco: agrupa búsquedas y llamadas independientes; no releas contenido sin cambios que ya esté en contexto.
- Frontend: edita `frontend/`, compila según su guía y copia `out` → `web/` solo mediante el workflow documentado.
- No añadas dependencias de vídeo ni frameworks de render sin un plan que justifique el cambio.

## Mapa de documentos

| Necesidad | Leer |
|---|---|
| Estado y siguiente paso | `docs/STATUS.md` |
| Equipo y flujo de agentes | `docs/AI_TEAM.md` |
| Dónde está el código | `docs/MAP.md` |
| Uso y funciones de la app | `README.md` (secciones por función) |
| Coste y sesiones | `.claude/skills/token-optimization/SKILL.md` |
| Pipeline de medios | `.claude/skills/clipforge-media-pipeline/SKILL.md` |
| Frontend | `.claude/skills/clipforge-frontend/SKILL.md` |
