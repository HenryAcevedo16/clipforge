# Procedencia de los archivos de ejemplo

`public/mock/clips/{a,b,c,d}.{mp4,jpg}` son **marcadores de posición**, no videos reales ni material de nadie.

- Generados el 2026-11-16 con FFmpeg 6.1 (fuente sintética `gradients`, 540×960, 8 s, 24 fps, sin audio, H.264 CRF 30).
- Las miniaturas `.jpg` son el fotograma del segundo 2 de cada video.
- Se usan solo con `NEXT_PUBLIC_USE_MOCK=true`. En modo real los clips salen de `GET /files/{job_id}/{name}`.
- Si algún navegador no reproduce H.264 (por ejemplo, Chromium de código abierto), los videos de ejemplo no se verán; no pasa con los clips reales del backend.

Comando base: `ffmpeg -f lavfi -i "gradients=s=540x960:d=8:r=24:speed=0.03:c0=…:c1=…:c2=…:nb_colors=3" … -c:v libx264 -crf 30 -an a.mp4`
