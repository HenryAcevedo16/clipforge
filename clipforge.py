"""ClipForge por línea de comandos.

Ejemplos:
  python clipforge.py "https://www.youtube.com/watch?v=XXXX" -n 8
  python clipforge.py video.mp4 -n 5 --style caja --min 15 --max 45 --aspect 9:16
"""
import argparse
import re
from pathlib import Path

import pipeline
from pipeline import Options


def main() -> None:
    ap = argparse.ArgumentParser(description="Convierte un video largo en clips virales verticales 1080p.")
    ap.add_argument("source", help="URL de YouTube o ruta de un video local")
    ap.add_argument("-n", "--num", type=int, default=5, help="número de clips")
    ap.add_argument("--min", type=float, default=20, help="duración mínima (s)")
    ap.add_argument("--max", type=float, default=60, help="duración máxima (s)")
    ap.add_argument("--aspect", default="9:16", choices=list(pipeline.ASPECTS))
    ap.add_argument("--layout", default="auto", choices=["auto", "track", "blur", "gaming", "gamecenter"])
    ap.add_argument("--style", default="viral", choices=list(pipeline.STYLES) + ["none"])
    ap.add_argument("--words", type=int, default=3, help="palabras por línea de subtítulo")
    ap.add_argument("--font", default="Arial Black")
    ap.add_argument("--no-hook", action="store_true", help="no mostrar titular arriba")
    ap.add_argument("--lang", default=None, help="idioma (es, en...). Por defecto autodetecta")
    ap.add_argument("--whisper", default="small", help="tiny|base|small|medium|large-v3")
    ap.add_argument("--no-ai", action="store_true", help="no usar Claude para elegir clips")
    ap.add_argument("--no-review", action="store_true", help="no pedir a Claude que revise los clips terminados")
    ap.add_argument("--crf", type=int, default=18, help="calidad (menor = mejor; 16-23)")
    ap.add_argument("--cookies", default=None, help="navegador para cookies de YouTube (chrome, firefox...)")
    ap.add_argument("-o", "--out", default="salida", help="carpeta de salida")
    a = ap.parse_args()

    opts = Options(num_clips=a.num, min_len=a.min, max_len=a.max, aspect=a.aspect, layout=a.layout,
                   caption_style=a.style, words_per_line=a.words, font=a.font, show_hook=not a.no_hook,
                   language=a.lang, whisper_model=a.whisper, use_ai=not a.no_ai, crf=a.crf,
                   cookies_from_browser=a.cookies, review=not a.no_review)
    name = re.sub(r"\W+", "_", a.source)[-40:].strip("_") or "video"
    res = pipeline.process(a.source, Path(a.out) / name, opts)
    print("\nClips generados en", Path(a.out) / name / "clips")
    for c in res["clips"]:
        print(f"  [{c['score']:>3}] {c['duration']:5.1f}s  {c['file']}  -  {c['title']}")
        rv = c.get("review") or {}
        if rv.get("error"):
            print(f"        Revisión IA: no disponible ({rv['error']})")
        elif rv:
            estado = "LISTO PARA PUBLICAR" if rv["aprobado"] else "REVISAR"
            print(f"        Revisión IA: {estado} · nota {rv['nota']}/100 · {rv['resumen']}")
            for p in rv["problemas"]:
                seg = f" (s{p['segundo']:.0f})" if p.get("segundo") is not None else ""
                print(f"          - [{p['gravedad']}] {p['tipo']}{seg}: {p['detalle']}")
            for s in rv["sugerencias"]:
                print(f"          > {s}")


if __name__ == "__main__":
    main()
