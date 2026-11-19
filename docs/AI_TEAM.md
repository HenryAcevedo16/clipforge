# Equipo de desarrollo IA de ClipForge

Este repositorio usa cuatro roles especializados. La asignación se hace por tarea y complejidad; no hay que llamar a los cuatro agentes para cada cambio de una línea.

## Roles

| Orden | Agente | Modelo | Misión |
|---|---|---|---|
| 1 | opus-worker | Opus | Arquitectura, alcance, decisiones y plan de aceptación |
| 2 | haiku-worker | Haiku | Investigación acotada: símbolos, contratos, logs, docs y pruebas relevantes |
| 3 | sonnet-worker | Sonnet | Implementación, pruebas dirigidas y correcciones |
| 4 | sonnet-reviewer | Sonnet | Revisión independiente del diff, pruebas y regresiones |

## Flujo para trabajo no trivial

1. **Arquitectura (Opus):** define problema, alcance, criterios de aceptación, riesgos y archivos/sistemas afectados. Para cambios simples o ya especificados, el coordinador puede omitir esta fase.
2. **Investigación (Haiku):** localiza código, interfaces, pruebas y documentación. Devuelve evidencia archivo:línea y no toma decisiones arquitectónicas.
3. **Implementación (Sonnet):** realiza el cambio de menor tamaño que cumple el plan y añade pruebas.
4. **Revisión (Sonnet):** inspecciona el diff de forma independiente; no modifica código. Devuelve hallazgos priorizados.
5. **Corrección (Sonnet):** resuelve los hallazgos confirmados y vuelve a ejecutar las pruebas afectadas.
6. **Cierre:** actualizar documentación/estado si corresponde, refrescar Graphify y reportar qué se verificó.

## Reglas de delegación y coste

- No usar un subagente si la llamada cuesta más que leer una salida pequeña directamente.
- Haiku solo para trabajo mecánico, acotado y fácil de verificar.
- Sonnet es el implementador predeterminado.
- Opus se reserva para decisiones ambiguas, cambios multi-sistema, debugging de causa raíz o alto impacto.
- Sonnet Reviewer revisa cambios normales; Opus puede hacer una revisión adicional si el riesgo es alto o hay implicaciones de arquitectura/seguridad.
- Limitar respuestas de subagentes a hallazgos, rutas/lineas, decisiones y próximos pasos. No copiar archivos completos al contexto principal.
- No delegar dos agentes para editar el mismo archivo simultáneamente.

## Skills del proyecto

| Skill | Activar cuando |
|---|---|
| model-router | Elegir modelo/rol o delegar trabajo |
| token-optimization | Inicio/cierre de sesión, checkpoint o auditoría de consumo |
| clipforge-media-pipeline | Descarga, Whisper, selección, timestamps, encuadre, audio, FFmpeg, GPU o directos |
| clipforge-frontend | Next.js, React, TypeScript, editor, proyectos, UI, accesibilidad o rendimiento |

Graphify sigue siendo el mapa de relaciones del código. Antes de explorar fuentes, usa las instrucciones vigentes de CLAUDE.md.
