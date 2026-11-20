# NovoClip — clipping narrativo e hooks verificables

Estado: diseño inicial para `feat/narrative-clipping-hooks`.

## Objetivo del producto

Generar menos clips, pero que cada uno se entienda sin haber visto el directo original. El criterio de aceptación principal es la coherencia narrativa; la viralidad ordena los clips que ya superaron ese criterio, no compensa una historia incomprensible.

## Principios no negociables

1. **Sentido antes que viralidad.** Cada clip necesita contexto suficiente, desarrollo y cierre. No se acepta una respuesta aislada si falta la pregunta, un chiste cuyo referente quedó fuera ni una idea cortada a mitad.
2. **Hooks auténticos.** El hook hablado debe ser una cita literal, contigua y verificable en la transcripción del video. No se atribuyen al creador palabras inventadas por el modelo.
3. **Hook sincronizado.** El hook seleccionado debe apuntar a un intervalo real del video. Si el momento se reordena al inicio, la imagen y el audio deben proceder de ese intervalo, no solo cambiar el texto superpuesto.
4. **Edición bajo control del usuario.** El usuario puede elegir entre candidatos, ajustar entrada/salida, editar el texto editorial y previsualizar antes de renderizar. Se distingue la cita original del texto de portada.
5. **Sin IA también debe funcionar.** La selección local usa transcripción, límites de frases, pausas, energía de audio y cambios de escena; presenta puntuaciones y motivos. No debe fingir comprensión semántica equivalente a un LLM.
6. **Proveedores intercambiables.** La lógica de selección y el motor de render no dependen de un proveedor. Cada adaptador declara capacidades, autenticación, disponibilidad y límites.
7. **No destructivo.** Las decisiones de edición son datos del proyecto; el original no se altera y los cambios se pueden deshacer.

## Estado de la base existente

La aplicación ya contiene:
- selección IA y selección local;
- puntuaciones parciales de gancho, emoción, valor, autonomía y remate;
- refinamiento de límites y comprobación de finales completos;
- opción `complete_ideas`;
- editor de cortes con transcripción, corrección de palabras y campo de titular/gancho;
- proveedores actuales: Claude Code CLI en modo desarrollador, API de Claude, Gemini e IA incluida.

Por tanto, esta iniciativa debe extender esos flujos, no duplicarlos ni reemplazar FFmpeg/Whisper.

## Flujo propuesto de selección

1. Ingerir y transcribir usando el camino rápido actual cuando aplique.
2. Construir unidades de contexto (frases/turnos), preservando hablante, tiempos por palabra y pausas.
3. Generar candidatos por señales locales y/o modelo.
4. Evaluar cada candidato en dos fases:
   - **Puerta de coherencia:** contexto suficiente, referente identificable, idea completa y cierre verificable. Los candidatos que fallen se descartan o se amplían.
   - **Ranking:** fuerza del hook, emoción, novedad, valor, ritmo, autonomía y señales de audiencia.
5. Verificar con palabras reales los límites y la cita del hook.
6. Mostrar candidatos, motivos, puntuaciones y posibles problemas para que el usuario elija.
7. Renderizar y guardar los metadatos para poder editar/revertir.

La puntuación de autonomía y cierre debe funcionar como umbral de aceptación, no solo como pesos dentro de una media.

## Modelo de hook

Cada candidato de hook debe conservar, como mínimo:
- `quote`: texto literal pronunciado;
- `source_start` y `source_end`: segundos absolutos del video fuente;
- `word_start` y `word_end`: índices de palabras de la transcripción usada para verificar la cita;
- `display_text`: texto opcional de portada, claramente diferenciado de la cita;
- `kind`: `spoken_quote` o `editorial_title`.

La interfaz debe permitir seleccionar un hook detectado, escuchar/ver ese fragmento, cambiar sus límites y modificar `display_text`. Si se elige un hook que está más adelante en el video, la composición debe insertar el fragmento audiovisual correspondiente al principio y mantener después la historia que lo contextualiza. Debe evitar repetirlo de forma confusa y conservar una transición comprensible.

Para versiones antiguas de proyectos, los campos nuevos serán opcionales y se derivarán de forma segura cuando sea posible.

## Selección sin IA

Debe seguir siendo útil y honesta:
- detectar pausas, silencios, energía, risas y cambios de escena;
- proponer ventanas que respeten frases completas;
- evitar solapamientos y segmentos sin voz;
- puntuar ritmo/energía y estructura observable;
- explicar que la autonomía semántica no puede garantizarse sin un modelo de lenguaje.

## Arquitectura de proveedores

Un contrato común de proveedor debe exponer capacidades (texto, visión, video, herramientas), estado de disponibilidad y un método de salida estructurada. Adaptadores previstos:
- Claude Code CLI autenticado oficialmente por el usuario;
- API de Claude;
- ChatGPT/OpenAI API;
- conexión MCP compatible cuando el cliente y el plan permitan las operaciones requeridas;
- Ollama local;
- Gemini y otros proveedores compatibles.

No se extraerán cookies, tokens ni sesiones privadas de las aplicaciones oficiales. No se simulará el login de ChatGPT/Claude ni se presentará una suscripción web como API. Cuando una vía sin API no esté oficialmente disponible para una cuenta/cliente, NovoClip debe mostrar esa limitación y ofrecer el flujo alternativo permitido.

## Criterios de aceptación

- Un clip no se aprueba solo por tener puntuación viral alta si no se entiende por sí mismo.
- La cita de hook se verifica como secuencia contigua de palabras reales con timestamps; si no coincide, se rechaza o se sustituye por una cita válida.
- Cambiar el hook actualiza su referencia temporal y la previsualización; no puede quedar texto sincronizado con audio distinto.
- Un hook encontrado más tarde puede abrir el clip sin perder el contexto necesario para comprenderlo.
- El usuario puede seleccionar, recortar, editar el texto de portada, previsualizar, guardar y deshacer.
- La selección local funciona con los proveedores IA desconectados.
- Las rutas antiguas, modo instantáneo, directos, cancelación, tiempos absolutos/relativos y render actual siguen funcionando.

## Secuencia de implementación

1. **M1 — Contrato narrativo y hooks verificables:** modelo de datos, validación literal de citas, pruebas de límites y compatibilidad con proyectos antiguos.
2. **M2 — Selector de hooks en el editor:** lista de candidatos, reproductor/preview sincronizado, ajuste de rango y texto editorial separado.
3. **M3 — Reordenamiento audiovisual:** insertar el fragmento de hook al inicio con transición y continuidad, sin desalinear subtítulos.
4. **M4 — Evaluación local mejorada:** ranking heurístico y explicación de límites sin IA.
5. **M5 — Proveedores modulares:** Ollama y proveedores API/MCP según capacidades oficiales disponibles.
6. **M6 — Revisión de calidad:** fixtures sintéticos, pruebas de timestamps, exportación y revisión manual de clips reales.

## Riesgos técnicos a vigilar

- Los tiempos de subtítulos de YouTube pueden ser aproximados; al descargar el fragmento hay que alinear con Whisper antes de sincronizar.
- Quitar silencios modifica el mapeo temporal del hook; el intervalo fuente debe convertirse al tiempo final usando el mismo mapa de intervalos.
- El hook insertado al principio puede revelar el remate antes de contexto; hay que medir si conviene teaser corto, hook completo o empezar cronológicamente.
- En podcasts/directos puede haber varios hablantes simultáneos; no se debe atribuir una frase a quien no la dijo.
- No cambiar la selección/ranking actual hasta tener pruebas de regresión que demuestren una mejora.
