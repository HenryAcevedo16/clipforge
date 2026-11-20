# NovoClip Studio — editor y criterios de calidad

## Flujo de edición

1. Abre un clip desde un proyecto y revisa el reproductor.
2. Usa la línea de tiempo para marcar IN y OUT. Cuando el archivo fuente está disponible, muestra una forma de onda real calculada del audio original; en trabajos antiguos o fuentes no disponibles, usa la actividad estimada a partir de la transcripción.
3. Ajusta los segundos con los controles de inicio y fin o selecciona palabras de la transcripción.
4. Cambia palabras de subtítulos, resalta términos, elige encuadre y configura subtítulos y efectos.
5. Escribe una instrucción editorial para pedir cambios a la IA. Ejemplos:
   - "Empieza cuando comienza la historia, sin el saludo."
   - "Conserva el final porque ahí termina el chiste."
   - "Haz el gancho más curioso, pero no inventes una frase pronunciada."
   - "Cambia el encuadre a gaming."
6. Revisa el resultado renderizado. Si la optimización no funciona, restaura la versión anterior.

Las instrucciones de IA trabajan sobre la última versión guardada del clip. Si hay cambios manuales pendientes en el editor, primero pulsa **Volver a generar**; el botón de instrucciones se mantiene desactivado para evitar sobrescribirlos.

## Reglas de fidelidad

- `hook_quote` es un extracto de palabras reales de la transcripción y se muestra separado del gancho de pantalla.
- El gancho, título y descripción pueden ser redacción editorial; no deben presentarse como citas literales.
- Las palabras clave para animar subtítulos deben existir en el clip.
- La selección IA exige autonomía, gancho y cierre mínimos. Si ningún candidato cumple, se usa el selector local en lugar de aceptar un candidato narrativamente débil.
- La puntuación es una estimación editorial del motor, no una promesa de visualizaciones o viralidad.

## Límites actuales

- La línea de tiempo calcula picos normalizados del audio original cuando el archivo está disponible; usa la transcripción como fallback.
- El editor procesa y renderiza en el equipo donde corre NovoClip.
- La edición en lenguaje natural usa el proveedor de IA configurado en Ajustes; requiere que ese proveedor esté disponible.
- Esta integración no conecta por sí sola la conversación web de ChatGPT con el servidor local. Para ese flujo se necesita una conexión remota autorizada; no se debe exponer el servidor local sin autenticación.

## Aplicar los cambios visuales

El servidor FastAPI sirve la carpeta compilada `web/`; editar `frontend/` no cambia por sí solo la interfaz que se abre en localhost.

- Windows: ejecuta `build_frontend.bat`.
- Mac/Linux: ejecuta `bash build_frontend.sh`.

Después reinicia NovoClip y recarga el navegador con Ctrl+F5. Estos scripts compilan el frontend estático con `NEXT_PUBLIC_USE_MOCK=false` (para que use FastAPI y no datos de demostración) y copian el resultado a `web/`.
