# Equipo de desarrollo IA de ClipForge

Usa cuatro agentes con responsabilidades claras. No invoques a todos para una tarea trivial: la delegación debe ahorrar más contexto del que añade.

## Roles

| Orden | Agente | Modelo | Responsabilidad |
|---|---|---|---|
| 1 | `opus-worker` | Opus | Arquitectura, criterios de aceptación, riesgos y coordinación |
| 2 | `haiku-worker` | Haiku | Investigación acotada, contratos, logs y pruebas relevantes |
| 3 | `sonnet-worker` | Sonnet | Implementación, pruebas dirigidas y correcciones |
| 4 | `sonnet-reviewer` | Sonnet | Revisión independiente del diff; no implementa |

## Flujo recomendado

Para cambios no triviales: Opus define el plan → Haiku recopila evidencia → Sonnet implementa → Sonnet Reviewer revisa → Sonnet corrige hallazgos → verificación y cierre.

Para una tarea pequeña, Sonnet puede ejecutarla directamente; usa Haiku para búsquedas mecánicas y Opus solo cuando la ambigüedad o el impacto lo justifiquen.

## Política de modelos

- **Opus:** requisitos ambiguos, arquitectura multi-módulo, causa raíz compleja, cambios irreversibles o decisiones de alto impacto.
- **Haiku:** localizar símbolos, revisar contratos conocidos, resumir logs, consultar docs concretas, contar/clasificar y otras tareas mecánicas verificables.
- **Sonnet Developer:** implementación habitual, pruebas, refactors acotados e integración.
- **Sonnet Reviewer:** revisión independiente de cambios normales y seguridad de código rutinaria. Para un cambio de seguridad/arquitectura de alto riesgo, pedir además revisión de Opus.
- La revisión es una fase distinta de la implementación. El revisor no edita; devuelve hallazgos con archivo:línea.
- Limita respuestas de agentes a 30–40 líneas, sin bloques de código ni lecturas completas innecesarias.
- Nunca delegues dos agentes para editar el mismo archivo simultáneamente.

## Skills del proyecto

| Skill | Activar cuando |
|---|---|
| `model-router` | Elegir agente/modelo y delegar |
| `token-optimization` | Reducir lecturas/contexto, checkpoints y auditoría de coste |
| `clipforge-media-pipeline` | yt-dlp, Whisper, selección de clips, timestamps, encuadre, audio, FFmpeg, GPU, directos |
| `clipforge-frontend` | Next.js, React, TypeScript, editor, proyectos, UI, accesibilidad y rendimiento |

## Skills externas opcionales para frontend

Desde la raíz del repo, se pueden instalar las guías oficiales de Vercel en el ámbito del proyecto:

```bash
npx skills add vercel-labs/agent-skills --skill react-best-practices -a claude-code
npx skills add vercel-labs/agent-skills --skill web-design-guidelines -a claude-code
npx skills add vercel-labs/agent-skills --skill composition-patterns -a claude-code
```

Son complementarias a `clipforge-frontend`; no reemplazan las reglas específicas de Next.js 16, HeroUI 3 ni el contrato del backend. Instálalas solo cuando vayas a trabajar el frontend.

Graphify sigue siendo el mapa de relaciones del código. Antes de explorar fuentes, usa las instrucciones vigentes de `CLAUDE.md`.
