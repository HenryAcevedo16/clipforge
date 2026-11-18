@AGENTS.md

## Claude Code

- Lee los archivos grandes por rango: `grep -n '^def \|^class ' pipeline.py`, luego Read con offset/limit. Si el guard deniega una lectura completa, funciona: reintenta con offset/limit.
- Usa la skill `token-optimization` al cerrar una tarea grande (checkpoint: `/clear` o seguir) o para auditar el coste.
- Prefiere `/clear` + `docs/STATUS.md` antes que `/compact`.
- Subagentes por modelo en `.claude/agents/` (haiku/sonnet/opus/fable-worker) y skill `model-router`: delega lo mecánico a Haiku, lo normal a Sonnet, lo difícil a Opus y toda revisión de código/seguridad a Fable. Clasificador: `python3 .claude/skills/model-router/scripts/route.py "tarea" --files N`.
