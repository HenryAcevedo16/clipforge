# ClipForge ✂️ — tu propia app de clipping

Pegas un link de YouTube (o subes un video) y te genera N clips verticales **1080x1920** listos para
**TikTok, YouTube Shorts e Instagram Reels**, con subtítulos animados palabra por palabra.

## Qué hace
1. **Descarga** el video en la mejor calidad hasta 1080p (yt-dlp).
2. **Transcribe** con tiempos por palabra (Whisper, local y gratis; usa GPU NVIDIA si tienes).
3. **Elige los mejores momentos**:
   - Con **Claude** (si pones `ANTHROPIC_API_KEY`): elige los clips con más potencial viral y genera título, gancho, descripción y hashtags.
   - Sin API key: algoritmo local que mide ganchos, preguntas, energía del audio, ritmo y si la idea está completa.
4. **Reencuadra a vertical** siguiendo la cara del que habla (detecta cortes de cámara y suaviza el movimiento).
   Si no hay caras: video completo sobre fondo desenfocado.
5. **Subtítulos animados** (5 estilos): `viral` (amarillo con pop), `caja`, `karaoke`, `neon`, `minimal`, o ninguno,
   más un **titular gancho** arriba los primeros 3 segundos.
6. **Revisión con IA** (con API key): Claude mira 9 fotogramas de cada clip terminado + lo que se dice, y te dice
   si está listo para publicar, con nota 0–100, problemas (encuadre, subtítulos, gancho, cortes a mitad de frase) y sugerencias.
   Se desactiva con la casilla "Revisar clips con IA" o `--no-review`.
7. **Exporta** H.264 1080p alta calidad (CRF 18), audio normalizado a -14 LUFS (estándar de redes).

Cantidad de clips (1–30), duración mín/máx y formato (9:16, 4:5, 1:1, 16:9) configurables.

## Instalación (una sola vez)
Requisitos: **Python 3.10+** y **FFmpeg**.

- **Windows:** instala Python de python.org y `winget install Gyan.FFmpeg`. Doble clic en `iniciar_windows.bat`.
- **Mac:** `brew install ffmpeg python` → `./iniciar_mac_linux.sh`
- **Linux:** `sudo apt install ffmpeg python3-venv` → `./iniciar_mac_linux.sh`

Se abre en **http://localhost:8000**.

### IA de Claude (opcional, recomendado)
```bash
# Windows (PowerShell)
$env:ANTHROPIC_API_KEY="sk-ant-..."
# Mac/Linux
export ANTHROPIC_API_KEY="sk-ant-..."
```
Clave en https://console.anthropic.com.

## Línea de comandos
```bash
python clipforge.py "https://www.youtube.com/watch?v=XXXX" -n 8 --style viral
python clipforge.py mi_video.mp4 -n 5 --min 15 --max 45 --style karaoke --lang es
```
`python clipforge.py -h` muestra todas las opciones.

## Consejos
- Con GPU usa precisión "Máxima" (`large-v3`); en CPU "Equilibrada" (`small`) va bien.
- Fuentes: mete un .ttf en `fonts/` y escribe su nombre en "Fuente".
- Si YouTube da error "Sign in to confirm": `pip install -U yt-dlp` o usa `--cookies chrome`.
- La primera vez se descargan el modelo de Whisper (~500 MB en `small`) y el detector de caras YuNet (230 KB).
- Usa solo contenido tuyo o con permiso para reutilizar.

## Archivos
| Archivo | Para qué |
|---|---|
| `pipeline.py` | Motor: descarga, transcripción, selección, reencuadre, subtítulos y render |
| `app.py` | Servidor web (FastAPI) |
| `static/index.html` | Interfaz |
| `clipforge.py` | Versión de línea de comandos |
