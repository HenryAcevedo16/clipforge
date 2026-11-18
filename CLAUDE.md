@AGENTS.md

## Claude Code

- Lee los archivos grandes por rango: `grep -n '^def \|^class ' pipeline.py`, luego Read con offset/limit. Si el guard deniega una lectura completa, funciona: reintenta con offset/limit.
- Usa la skill `token-optimization` al cerrar una tarea grande (checkpoint: `/clear` o seguir) o para auditar el coste.
- Prefiere `/clear` + `docs/STATUS.md` antes que `/compact`.
