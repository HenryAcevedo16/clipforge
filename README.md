# NovoClip ✂️ — tu propia app de clipping

Pegas un link de YouTube (o subes un video) y te genera N clips verticales **1080x1920** listos para
**TikTok, YouTube Shorts e Instagram Reels**, con subtítulos animados palabra por palabra.

## Qué hace
1. **Descarga** el video en la mejor calidad hasta 1080p (yt-dlp).
2. **Transcribe** con tiempos por palabra (Whisper, local y gratis; usa GPU NVIDIA si tienes).
3. **Elige los mejores momentos**:
   - Con **Claude** (tu suscripción vía Claude Code, o `ANTHROPIC_API_KEY`): elige los clips con más potencial viral y genera título, gancho, descripción y hashtags.
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
Hay dos formas. La app detecta sola cuál tienes (se ve arriba a la derecha: "IA: ...").

**A) Con tu suscripción de Claude (Pro/Max) mediante Claude Code — sin pagar API**
```bash
npm install -g @anthropic-ai/claude-code
claude
```
En esa ventana elige iniciar sesión con tu cuenta de Claude; cuando entre, ciérrala (`/exit`).
Listo: la app usará `claude -p` para elegir los clips y revisarlos. Consume tus límites de uso de la suscripción.
La app usa **Sonnet con esfuerzo alto** por defecto. Cambiar: `setx NOVOCLIP_CLAUDE_MODEL opus` y `setx NOVOCLIP_CLAUDE_EFFORT medium`.

**B) Con clave de API** (se paga aparte en https://console.anthropic.com)
```bash
setx ANTHROPIC_API_KEY "sk-ant-..."
```
Si hay clave de API se usa la API; si no, Claude Code; si no hay ninguno, el algoritmo local.

## Edición para redes (nuevo)
- **Encuadre automático inteligente:** Claude mira el video y decide si es una persona hablando, un podcast,
  un gameplay con webcam, un gameplay sin webcam o una grabación de pantalla. Solo divide la pantalla
  (webcam arriba + juego abajo) cuando de verdad es un recuadro de webcam sobre un juego. Sin IA, una
  detección estricta comprueba tamaño, posición, que el recuadro no se mueva y que el fondo sea un juego en movimiento.
- **Selección de clips de editor:** frases cortas en vez de bloques largos, energía de la voz, gancho en los
  primeros segundos, remate al final, sin intros ni "suscríbete", sin empezar con "y/bueno/entonces".
- **Quitar silencios** (jump cuts), **zoom dinámico** (cambio de plano en cada corte + golpe en palabras clave),
  **palabras clave resaltadas** en otro color, **barra de progreso**, **color más vivo** y **música de fondo**
  que baja sola cuando hay voz (pon tus canciones en `music/`).
Todo se activa o desactiva desde la app.

### Gemini (nuevo)
La app también puede usar **Gemini** de Google para elegir, afinar y revisar los clips.
1. Crea una clave gratis en https://aistudio.google.com/apikey
2. En la app, pégala en **"Clave de Gemini"** y pulsa **Guardar** (se guarda solo en tu PC, en `config.json`).
3. En **IA** elige *Gemini* (o deja *Automática*: usa Claude y, si no está, Gemini).
El modelo por defecto es `gemini-flash-latest`; puedes escribir otro (por ejemplo uno "pro") en el campo de al lado.

## 🎨 Nuevo diseño: NovoClip (frontend)
La página principal (`/`) ahora es el diseño **NovoClip** (carpeta `web/`, ya compilado: no hace falta instalar nada).
- Inicio en 4 pasos (video → personalizar → procesar → resultado), con todas las opciones: encuadre, silencios, zoom,
  directo, descarga rápida, resolución, estilo de subtítulos y revisión con IA.
- **Mis proyectos**: se guardan en disco y siguen ahí al reiniciar la app. Cada proyecto muestra su progreso en
  vivo, tiene botón para **cancelar / detener el directo** y los clips van apareciendo según se hacen.
- **Editor de cortes** en cada clip: corta con un clic en la transcripción, corrige palabras de los subtítulos,
  resalta palabras clave, cambia título, titular, encuadre y estilo, y vuelve a generar solo ese clip.
- **Ajustes**: IA incluida o clave propia (Gemini/Claude), licencia, y lo que la app lee de tu equipo.
- Kit de marca, Calendario y Cuentas de redes son una **vista previa**: guardan datos solo en el navegador y todavía
  no publican ni aplican logos (llevan un aviso en pantalla).
- El diseño anterior sigue disponible en `/classic`.

Para modificar el diseño (necesita Node 20+): `cd frontend && npm install && npm run build`, y copiar el contenido de
`frontend/out/` a la carpeta `web/`. Con `npm run dev` se ve con datos de prueba (sin backend).

## IA incluida o clave propia (nuevo)
Arriba de las opciones hay dos modos:
- **IA incluida:** la IA la pone NovoClip. Tiene dos formas de configurarse (las prepara el dueño de la app en
  `ia_incluida.json`, ver `ia_incluida.ejemplo.json`):
  - *Provisional:* `gemini_key` con la clave de Gemini del dueño. Fácil, pero la clave queda dentro del archivo:
    solo para repartir entre gente de confianza.
  - *Para vender:* `proxy_url` apuntando al servidor de `servidor_ia/`. La clave nunca sale del servidor y cada
    cliente usa su clave de licencia, con un límite de usos de IA al día.
- **Mi propia clave:** el usuario pega su clave de Gemini o de Claude y paga lo que use.
Para usar tu suscripción de Claude (Claude Code), elígela en Ajustes -> Mi suscripción de Claude.

## Ajuste automático según el equipo (nuevo)
La app lee el procesador, la RAM, la tarjeta gráfica y su memoria, y con "Automática" en Precisión y Velocidad
elige sola el mejor modelo de transcripción y dónde renderizar (GPU o procesador). Lo verás en el recuadro
"Tu equipo".

## ✏️ Editor de cortes (nuevo)
Cada clip tiene el botón **"Editar corte"**. Se abre un editor con el clip y la transcripción de alrededor
(30 segundos antes y después):
- **Clic en una palabra** marca dónde empieza el clip (verde) y el siguiente clic dónde termina (rojo).
  También hay botones de ±0,5 s.
- **Doble clic** en una palabra para corregirla si Whisper la escribió mal: así sale en los subtítulos.
- **Mayús + clic** para resaltar una palabra (o quitarle el resaltado).
- Cambia el título, el titular de arriba, la descripción, los hashtags, el encuadre y el estilo de subtítulos.
- **Volver a generar este clip** rehace solo ese clip (con descarga rápida baja de nuevo solo su trozo).
- **Eliminar clip** borra ese clip.
Los clips de los directos no se pueden editar.

## Modo instantáneo (nuevo)
Con un link de YouTube que tenga subtítulos (manuales o automáticos), la app **no descarga ni transcribe el video**:
lee los subtítulos de YouTube en segundos, la IA elige los clips, y solo entonces baja el trozo de cada clip y
transcribe ese trozo (unos segundos) para que los subtítulos animados y los cortes queden exactos.
Si el video no tiene subtítulos, usa la descarga rápida (solo el audio). Se desactiva desmarcando
"Modo instantáneo (subtítulos de YouTube)".

## Descarga rápida (nuevo)
Con un link de YouTube, la app ya no baja el video entero: baja **solo el audio** (pesa muy poco), transcribe y elige
los clips, y después baja en 1080p **solo los trozos elegidos**. Si la descarga por trozos falla, baja el video
completo como antes. Se puede desactivar desmarcando "Descarga rápida (solo los trozos)".

## 🔴 Modo en vivo (nuevo)
Marca **"Directo (clips en tiempo real)"**, pega el link de un directo de YouTube o Twitch que esté en vivo y pulsa
**Empezar a clipear el directo**. La app graba el directo en trozos temporales, cada pocos minutos (2, 3, 5 o 10)
analiza lo nuevo y los clips buenos van apareciendo en la página mientras el directo sigue.
- Solo saca clips que la IA puntúe con 70 o más (máximo 2 por tramo). Sin IA, saca el mejor de cada tramo.
- En Twitch lee también el chat: cuando el chat se dispara, se lo marca a la IA como posible buen momento.
- **Detener directo** para la grabación y conserva los clips ya hechos. Lo ya analizado se borra del disco.
- Línea de comandos: `python novoclip.py "https://twitch.tv/canal" --live`

## Mejor selección y cortes (nuevo)
- La IA puntúa con dureza y devuelve **menos clips si no hay tantos momentos buenos** (nada por debajo de 50).
- Se comprueba que cada clip empieza en las palabras exactas del gancho.
- Los cortes se mueven al **silencio real del audio**, para no cortar una respiración o media palabra.

## Conversaciones y podcasts (nuevo)
- **Enfoca a quien habla:** con dos o más personas en el plano, la app mira el movimiento de la boca de cada una
  mientras hay voz y corta al primer plano de la que está hablando. Si no está claro quién habla (risas, los dos a la
  vez, silencio largo) abre el plano para que salgan todos. Es el modo **Automático**.
- **Dividido:** una persona arriba y otra abajo, con los subtítulos en el centro.
- **Abierto:** el plano completo siempre.
- **La IA afina los cortes:** después de elegir los clips, una segunda pasada ajusta el inicio y el final palabra por
  palabra para empezar en el gancho y terminar en el remate.
- **Descargar todos (.zip):** todos los clips y un .txt con título, descripción y hashtags de cada uno.

## GPU o procesador (velocidad)
En la app elige **Procesar con**: *Automático* (usa la GPU si hay), *GPU* o *Procesador*, y la **Velocidad**
(*Rápido*, *Normal*, *Máxima calidad*). Arriba a la derecha se ve qué detectó tu equipo.
- **Video (render):** usa la GPU con NVIDIA NVENC, Intel Quick Sync o AMD AMF si tu FFmpeg y tus drivers lo
  permiten. Si no, usa x264 en el procesador.
- **Transcripción (Whisper):** solo con tarjetas NVIDIA. La primera vez ejecuta `activar_gpu_nvidia.bat`
  (instala CUDA 12 + cuDNN 9, ~1 GB). Si algo falla con la GPU, la app sigue sola con el procesador.
- **Transcripción con GPU AMD (o Intel):** ejecuta una vez `compilar_whisper_vulkan.bat`. Instala lo necesario
  (Git, CMake, Vulkan SDK, Visual Studio Build Tools) y compila whisper.cpp con Vulkan desde el código oficial
  (ggml-org/whisper.cpp v1.9.5). Después la app transcribe con tu tarjeta; si algo falla, vuelve al procesador.
- Con GPU puedes usar la precisión "Turbo" (large-v3-turbo): casi la calidad de la máxima, mucho más rápida.

## Línea de comandos
```bash
python novoclip.py "https://www.youtube.com/watch?v=XXXX" -n 8 --style viral
python novoclip.py mi_video.mp4 -n 5 --min 15 --max 45 --style karaoke --lang es
```
`python novoclip.py -h` muestra todas las opciones.

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
| `novoclip.py` | Versión de línea de comandos |

## 🎯 Encuadre automático: cuándo divide la pantalla
En modo **Auto** la pantalla solo se divide (webcam arriba, juego abajo) si de verdad es un stream: una cara pequeña y quieta en una esquina, sin más personas en el plano, y un fondo con movimiento (el juego). Podcasts, entrevistas, conversaciones y videollamadas nunca se dividen: se sigue a quien habla o se abre el plano para que salgan todos. Si quieres forzar la división, elige a mano "Streamer" o "Dividido".

## 🤖 Elegir la IA con un botón
En **Ajustes → Inteligencia artificial** eliges qué IA usar: **Automática**, **Mi suscripción de Claude** (Claude Code, con la cuenta iniciada en tu PC; solo para tus propios videos), **API de Claude** (con clave), **Gemini** (con clave) o **IA incluida** (licencia de NovoClip). Cada opción te dice si está lista. En el paso 2 también puedes cambiarla solo para ese video. Ya no hace falta un archivo `.bat` aparte.

## 🏷️ Kit de marca: tu logo como marca de agua
Sube tu logo en **Kit de marca**, elige esquina, tamaño y opacidad, y selecciona la plantilla al crear tus clips: el logo sale en todos. En el editor de cada clip puedes quitarlo ("Mostrar mi logo"). Se aplica el estilo de subtítulos y el logo; la tipografía y los colores propios aún no.

## 📡 Directos de Twitch, Kick y TikTok
Pega el enlace del canal (`twitch.tv/canal`, `kick.com/canal`, `tiktok.com/@usuario/live`) y la app lo reconoce: aparece una pastilla con el icono de la plataforma y "EN VIVO", y activa sola el modo directo. También funcionan videos, VODs y clips de esas plataformas y de YouTube.
- El canal tiene que estar en vivo en ese momento.
- El chat solo se usa para detectar momentos "calientes" en Twitch; en Kick y TikTok la app se guía por el audio y el video.
- Kick y TikTok a veces exigen que el descargador simule un navegador: por eso `requirements.txt` incluye `curl-cffi`. Si falla, ejecuta `.venv\\Scripts\\pip install -U "yt-dlp[default,curl-cffi]"`.

**Cada cuánto busca clips la IA en un directo:** al activar "Es un directo en vivo" eliges 1, 3, 5 o 10 minutos. Con 1 min salen los clips casi al instante (más llamadas a la IA); con 10 min se gasta menos IA. Recomendado: 3 min.

## 🗑️ Proyectos: borrado
Cada proyecto tiene un botón de papelera (pide confirmación). Además, los proyectos y sus clips se **borran solos a los 5 días** (`NOVOCLIP_RETENTION_DAYS` cambia el plazo; `0` lo desactiva). Los que siguen procesando no se tocan.

## 🎮 Streams de videojuegos
Con IA activa, si es un stream la app divide sola: streamer arriba (usa el recuadro de la webcam que ve la IA si el detector de caras no lo encuentra) y juego abajo. La IA reconoce además el personaje del jugador en cada clip y el recorte del juego lo sigue.

## ✏️ Todo se puede apagar y cada clip se puede editar
- **Antes de generar** (paso 2): puedes apagar subtítulos, resaltado de palabras clave, título arriba, quitar silencios, zoom, barra de progreso, color, música, igualar volumen, elegir momentos con IA, afinar inicio/fin y cortar en silencios. También hay "Sin plantilla".
- **Después de generar**: cada clip tiene el botón **Editar** (también mientras se generan los demás, y en Mis proyectos). Ahí cambias título, titular, descripción, hashtags, recortas con deslizadores o con la transcripción, corriges palabras y apagas efectos solo de ese clip. "Volver a generar este clip" rehace solo ese.

## 📤 Publicar (asistido, sin permisos ni pagos)
Cada clip tiene el botón **Publicar**. Eliges TikTok, YouTube Shorts, Instagram Reels, Facebook Reels o X: se abre en una ventana nueva su página de subir video, se descarga el clip y se copia el texto (descripción + hashtags). Solo arrastras el video y pegas. Funciona con varias cuentas: usa la sesión que tengas abierta en tu navegador.

## 🩺 Diagnóstico
En **Ajustes → Diagnóstico → Revisar mi equipo** la app comprueba FFmpeg, el codificador por GPU, yt-dlp, Deno, curl-cffi, la transcripción (incluida la de GPU AMD), OpenCV, la IA, el espacio en disco, la música y la conexión con YouTube, Twitch, Kick y TikTok. Si algo falla, te dice cómo arreglarlo.

## 👁️ Vista previa del encuadre
En el paso 2, junto a "Encuadre", pulsa **Probar el encuadre (10 s)**: la app saca una muestra corta del video (con el encuadre, zoom y efectos elegidos, sin subtítulos) para que veas cómo quedará antes de procesar todo. "Probar otro momento" prueba otra parte. No funciona con directos.

## 🎯 Clips que terminan la idea
Un clip no debe cortarse mientras quien habla sigue explicando. Ahora hay tres capas:
1. **El editor de IA** recibe la regla de que el final importa tanto como el gancho: incluye las frases siguientes si completan la idea ("porque...", "entonces...", "por eso...") y usa la duración que haga falta hasta el máximo.
2. **Revisión de finales con IA:** una pasada aparte le enseña a la IA lo que se dice *después* del corte y mueve el final (o empieza más tarde si no cabe) hasta que la idea queda cerrada.
3. **Red de seguridad sin IA:** si el corte cae a mitad de frase, el clip se alarga hasta el siguiente punto y, si la frase siguiente es una continuación, también la incluye, sin pasar del máximo.

Se puede apagar en el paso 2 con **"Terminar siempre la idea"**.

## ✏️ Editar cada clip después de generarlo
En **Mis proyectos → tu proyecto**, cada clip tiene:
- **Gancho:** botón "Cambiar gancho" junto al gancho: escribes el texto nuevo y "Aplicar al video" lo vuelve a pintar (unos segundos).
- **Título y hashtags:** edición rápida, se guarda al instante (no vuelve a generar el video).
- **Editar corte:** recortar con deslizadores, corregir palabras, resaltar, cambiar titular, encuadre y efectos, y "Volver a generar".
También se ven y se editan los clips que sí se generaron aunque el trabajo haya terminado con error.

## 📷 Calidad de la webcam del streamer
La webcam de un stream es pequeña y estirarla a 1080 px la dejaba borrosa. Ahora el encuadre de la webcam se aleja hasta que no se amplíe más de 2 veces (se ve más del recuadro y menos "la cara pegada a la cámara"). Ahora el panel de la webcam se limpia (reduce los bloques de compresión), se amplía con Lanczos y se afina. Si la webcam es tan pequeña que habría que ampliarla más de 3,2 veces, se muestra nítida y centrada sobre su propio fondo difuminado, en vez de estirarla de borde a borde. Para más nitidez, descarga el video con "La mejor" resolución (paso 2 → Origen del video).

## 🔎 Qué modelo de Gemini puede usar mi clave
En **Ajustes → Inteligencia artificial → Gemini**, pulsa **"Ver los modelos que puede usar mi clave"**: la app le pregunta a Google y lista los modelos de texto disponibles (Flash primero). Toca uno para usarlo.
