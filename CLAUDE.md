@AGENTS.md

## Claude Code — equipo de cuatro roles

- Para trabajo no trivial, usa Opus como coordinador/arquitecto: entiende el objetivo, fija criterios de aceptación y divide el trabajo. En Desktop selecciona Opus para la sesión de coordinación; en terminal puedes iniciar con `claude --model opus`.
- Haiku (`haiku-worker`) investiga de forma acotada: encuentra símbolos, contratos, docs, logs y pruebas. No decide arquitectura ni hace cambios ambiguos.
- Sonnet (`sonnet-worker`) es el implementador predeterminado: backend Python/FastAPI, pipeline FFmpeg/Whisper/yt-dlp y frontend Next.js/React/TypeScript.
- Sonnet (`sonnet-reviewer`) revisa de forma independiente los cambios tras la implementación. No edita; informa hallazgos con archivo:línea. Sonnet implementa las correcciones.
- No invoques los cuatro agentes para cada tarea pequeña. Sigue `.claude/skills/model-router/SKILL.md` y `docs/AI_TEAM.md`.
- Carga `clipforge-media-pipeline` solo para ingesta, transcripción, clipping, timestamps, encuadre, audio, FFmpeg, GPU o directos. Carga `clipforge-frontend` solo para Next.js, React, TypeScript, editor o UI.
- Usa `token-optimization` para sesiones largas, auditorías y checkpoints. Prefiere `/clear` + `docs/STATUS.md` cuando el contexto anterior ya no sea útil.
- Para clasificar una tarea: `python3 .claude/skills/model-router/scripts/route.py "descripción" --files N`.

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

Rules:
- When graphify-out/graph.json exists, run `graphify query "<question>"` before your first grep, search or source-file read for a codebase question, and include this rule in every subagent prompt that explores code. Read raw files only for lines the graph or an earlier read located.
- Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. Use `graphify section "<heading>"` for a scoped Markdown section.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).
- A committed graphify-out/graph.json is rewritten whole on every build; do not flag its expected generated diff as churn.
