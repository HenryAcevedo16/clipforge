"""
ClipForge - motor de clipping.

Flujo:
  1. Descarga el video de YouTube en la mejor calidad <=1080p (yt-dlp)
  2. Transcribe con marcas de tiempo por palabra (faster-whisper)
  3. Elige los mejores momentos (Claude si hay ANTHROPIC_API_KEY, si no un algoritmo local)
  4. Reencuadra a vertical siguiendo la cara del que habla (OpenCV) o con fondo desenfocado
  5. Quema subtítulos animados palabra por palabra (ASS + libass) y exporta en 1080x1920
"""
from __future__ import annotations

import json
import math
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Callable, Optional
import warnings

# Avisos inofensivos de Hugging Face al bajar el modelo de Whisper en Windows
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
os.environ.setdefault("HF_HUB_VERBOSITY", "error")
warnings.filterwarnings("ignore", module="huggingface_hub")

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent
FONTS_DIR = ROOT / "fonts"
ProgressFn = Callable[[float, str], None]


def _noop(p: float, m: str) -> None:
    print(f"[{p:5.1f}%] {m}", flush=True)


# --------------------------------------------------------------------------- #
# Configuración
# --------------------------------------------------------------------------- #
ASPECTS = {"9:16": (1080, 1920), "1:1": (1080, 1080), "4:5": (1080, 1350), "16:9": (1920, 1080)}


@dataclass
class Options:
    num_clips: int = 5
    min_len: float = 20.0          # segundos
    max_len: float = 60.0
    aspect: str = "9:16"
    layout: str = "auto"            # auto | track | blur | gaming (webcam arriba + juego) | gamecenter (solo juego)
    caption_style: str = "viral"    # viral | caja | karaoke | neon | minimal | none
    words_per_line: int = 3
    font: str = "Arial Black"
    show_hook: bool = True          # titular arriba los primeros segundos
    language: Optional[str] = None  # None = autodetectar ("es", "en", ...)
    whisper_model: str = "small"    # tiny | base | small | medium | large-v3
    use_ai: bool = True             # usar Claude para elegir clips si hay API key
    ai_model: str = "claude-opus-5-5"
    crf: int = 18
    preset: str = "medium"
    fps: Optional[float] = None     # None = el del original (máx 60)
    loudnorm: bool = True
    review: bool = True             # Claude revisa cada clip terminado (necesita API key)
    cookies_from_browser: Optional[str] = None  # "chrome", "firefox"... por si YouTube lo pide


@dataclass
class Clip:
    index: int
    start: float
    end: float
    title: str
    hook: str = ""
    score: float = 0.0
    reason: str = ""
    caption: str = ""
    hashtags: list = field(default_factory=list)
    file: str = ""
    thumb: str = ""
    review: dict = field(default_factory=dict)

    @property
    def duration(self) -> float:
        return self.end - self.start


# --------------------------------------------------------------------------- #
# Utilidades
# --------------------------------------------------------------------------- #
def run(cmd: list, **kw) -> subprocess.CompletedProcess:
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode != 0:
        raise RuntimeError(f"Falló: {' '.join(map(str, cmd[:6]))}...\n{r.stderr[-2000:]}")
    return r


def probe(path: Path) -> dict:
    r = run(["ffprobe", "-v", "error", "-print_format", "json", "-show_streams", "-show_format", str(path)])
    info = json.loads(r.stdout)
    v = next(s for s in info["streams"] if s["codec_type"] == "video")
    num, den = (v.get("avg_frame_rate") or v.get("r_frame_rate") or "30/1").split("/")
    fps = float(num) / float(den) if float(den) else 30.0
    if not (1 < fps < 241):
        fps = 30.0
    return {
        "width": int(v["width"]), "height": int(v["height"]), "fps": fps,
        "duration": float(info["format"].get("duration", 0)),
        "has_audio": any(s["codec_type"] == "audio" for s in info["streams"]),
    }


def slug(text: str, n: int = 40) -> str:
    import unicodedata
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    s = re.sub(r"[^\w\s-]", "", text, flags=re.U).strip().lower()
    return re.sub(r"[\s_-]+", "-", s)[:n].strip("-") or "clip"


# --------------------------------------------------------------------------- #
# 1. Descarga
# --------------------------------------------------------------------------- #
def download(url: str, workdir: Path, opts: Options, progress: ProgressFn = _noop) -> tuple[Path, str]:
    import yt_dlp

    workdir.mkdir(parents=True, exist_ok=True)

    def hook(d):
        if d.get("status") == "downloading":
            tot = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            if tot:
                progress(2 + 8 * d.get("downloaded_bytes", 0) / tot, "Descargando video...")

    ydl_opts = {
        "format": "bv*[height<=1080][ext=mp4]+ba[ext=m4a]/bv*[height<=1080]+ba/b[height<=1080]/b",
        "merge_output_format": "mp4",
        "outtmpl": str(workdir / "source.%(ext)s"),
        "quiet": True, "no_warnings": True, "noplaylist": True,
        "progress_hooks": [hook],
    }
    if opts.cookies_from_browser:
        ydl_opts["cookiesfrombrowser"] = (opts.cookies_from_browser,)
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        title = info.get("title") or "video"
    done = [p for p in workdir.glob("source.*") if p.suffix not in (".part", ".ytdl") and ".f" not in p.stem]
    if not done:
        raise RuntimeError("La descarga no terminó. Revisa tu conexión o actualiza yt-dlp (pip install -U yt-dlp).")
    src = max(done, key=lambda p: p.stat().st_size)
    return src, title


# --------------------------------------------------------------------------- #
# 2. Transcripción
# --------------------------------------------------------------------------- #
def transcribe(src: Path, workdir: Path, opts: Options, progress: ProgressFn = _noop) -> dict:
    cache = workdir / "transcript.json"
    if cache.exists():
        return json.loads(cache.read_text(encoding="utf-8"))

    from faster_whisper import WhisperModel

    progress(12, f"Cargando modelo Whisper '{opts.whisper_model}'...")
    device, compute = "cpu", "int8"
    try:
        import ctranslate2
        if ctranslate2.get_cuda_device_count() > 0:
            device, compute = "cuda", "float16"
    except Exception:
        pass
    model = WhisperModel(opts.whisper_model, device=device, compute_type=compute)
    segs, info = model.transcribe(
        str(src), language=opts.language, word_timestamps=True, vad_filter=True, beam_size=5
    )
    total = info.duration or 1
    out = {"language": info.language, "segments": []}
    for s in segs:
        words = [{"w": w.word.strip(), "s": round(w.start, 3), "e": round(w.end, 3)}
                 for w in (s.words or []) if w.word.strip()]
        out["segments"].append({"s": round(s.start, 3), "e": round(s.end, 3), "text": s.text.strip(), "words": words})
        progress(12 + 28 * min(1, s.end / total), f"Transcribiendo... {int(s.end)}s / {int(total)}s")
    cache.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    return out


# --------------------------------------------------------------------------- #
# 3. Selección de clips
# --------------------------------------------------------------------------- #
HOOK_WORDS = {
    # español
    "nunca", "siempre", "secreto", "error", "errores", "dinero", "increíble", "verdad", "nadie",
    "mejor", "peor", "cómo", "como", "por qué", "porque", "imagina", "atención", "importante",
    "millones", "gratis", "problema", "cambió", "mentira", "truco", "clave", "jamás", "loco",
    "escucha", "mira", "historia", "real", "miedo", "éxito", "fracaso", "rico", "pobre",
    # inglés
    "never", "always", "secret", "mistake", "money", "crazy", "truth", "nobody", "best", "worst",
    "how", "why", "imagine", "important", "million", "free", "problem", "changed", "lie",
    "trick", "key", "listen", "look", "story", "insane", "fear", "success", "fail", "rich",
}


def _loudness_curve(src: Path, hop: float = 0.5) -> np.ndarray:
    sr = 8000
    try:
        r = subprocess.run(["ffmpeg", "-v", "error", "-i", str(src), "-ac", "1", "-ar", str(sr), "-f", "s16le", "-"],
                           capture_output=True)
        a = np.frombuffer(r.stdout, dtype=np.int16).astype(np.float32) / 32768.0
    except Exception:
        return np.zeros(1)
    n = int(sr * hop)
    if len(a) < n:
        return np.zeros(1)
    a = a[: len(a) // n * n].reshape(-1, n)
    return 20 * np.log10(np.sqrt((a ** 2).mean(axis=1)) + 1e-6)


def _candidates(segs: list, min_len: float, max_len: float) -> list[tuple[int, int]]:
    out = []
    for i in range(len(segs)):
        for j in range(i, len(segs)):
            d = segs[j]["e"] - segs[i]["s"]
            if d > max_len:
                break
            if d >= min_len:
                out.append((i, j))
    return out


def _heuristic_score(segs, i, j, loud, loud_mu, loud_sd, rate_mu) -> tuple[float, str]:
    text = " ".join(s["text"] for s in segs[i : j + 1])
    low = text.lower()
    first = segs[i]["text"].lower()
    dur = segs[j]["e"] - segs[i]["s"]
    nwords = sum(len(s["words"]) or len(s["text"].split()) for s in segs[i : j + 1])
    reasons = []

    hook = sum(1 for w in HOOK_WORDS if re.search(rf"\b{re.escape(w)}\b", first))
    hook += 2 if "?" in first else 0
    hook += 1 if re.search(r"\d", first) else 0
    kw = sum(1 for w in HOOK_WORDS if re.search(rf"\b{re.escape(w)}\b", low))
    punct = low.count("?") + low.count("!")
    nums = len(re.findall(r"\d+", low))
    rate = nwords / max(dur, 1)
    complete = 1.0 if re.search(r"[.!?…]$", segs[j]["text"].strip()) else 0.0

    a, b = int(segs[i]["s"] / 0.5), max(int(segs[j]["e"] / 0.5), int(segs[i]["s"] / 0.5) + 1)
    lz = 0.0
    if len(loud) > 1 and a < len(loud):
        w = loud[a:b]
        lz = (float(np.mean(w)) - loud_mu) / (loud_sd + 1e-6) + 0.5 * float(np.std(w)) / (loud_sd + 1e-6)

    score = (
        14 * min(hook, 3)
        + 3 * min(kw, 8)
        + 3 * min(punct, 5)
        + 2 * min(nums, 4)
        + 10 * max(-1, min(2, lz))
        + 8 * max(-1, min(1.5, (rate - rate_mu) / (rate_mu * 0.25 + 1e-6)))
        + 10 * complete
    )
    if hook:
        reasons.append("arranca con gancho")
    if lz > 0.5:
        reasons.append("momento de alta energía")
    if punct >= 2:
        reasons.append("preguntas/exclamaciones")
    if rate > rate_mu * 1.1:
        reasons.append("ritmo rápido")
    if complete:
        reasons.append("idea completa")
    return score, ", ".join(reasons) or "segmento coherente"


def _overlaps(a, b, gap=1.0) -> bool:
    return not (a[1] + gap <= b[0] or b[1] + gap <= a[0])


def select_heuristic(src: Path, tr: dict, opts: Options) -> list[Clip]:
    segs = tr["segments"]
    if not segs:
        return []
    loud = _loudness_curve(src)
    voiced = loud[loud > -60] if len(loud) > 1 else loud
    mu, sd = (float(np.mean(voiced)), float(np.std(voiced))) if len(voiced) else (0.0, 1.0)
    tot_words = sum(len(s["words"]) or len(s["text"].split()) for s in segs)
    rate_mu = tot_words / max(1, sum(s["e"] - s["s"] for s in segs))

    cands = _candidates(segs, opts.min_len, opts.max_len)
    if not cands:  # video corto: usar todo
        cands = [(0, len(segs) - 1)]
    scored = []
    for i, j in cands:
        sc, why = _heuristic_score(segs, i, j, loud, mu, sd, rate_mu)
        scored.append((sc, i, j, why))
    scored.sort(reverse=True)

    picked: list = []
    for sc, i, j, why in scored:
        rng = (segs[i]["s"], segs[j]["e"])
        if any(_overlaps(rng, (p[1], p[2])) for p in picked):
            continue
        picked.append((sc, *rng, i, why))
        if len(picked) >= opts.num_clips:
            break

    if not picked:
        return []
    hi, lo = max(p[0] for p in picked), min(p[0] for p in picked)
    clips = []
    for k, (sc, s, e, i, why) in enumerate(sorted(picked, key=lambda p: -p[0])):
        first = segs[i]["text"]
        title = " ".join(first.split()[:9]).rstrip(",.;:")
        norm = 70 + 25 * ((sc - lo) / (hi - lo) if hi > lo else 1)
        clips.append(Clip(index=k + 1, start=max(0, s - 0.15), end=e + 0.35, title=title,
                          hook=" ".join(first.split()[:6]).upper(), score=round(norm),
                          reason=why, caption=title, hashtags=["#shorts", "#viral", "#fyp"]))
    return clips


def select_ai(tr: dict, opts: Options, video_title: str = "") -> list[Clip]:
    """Usa Claude para escoger los momentos con más potencial viral."""
    import anthropic
    from pydantic import BaseModel, Field

    class AIClip(BaseModel):
        start_line: int = Field(description="índice de la primera línea del clip")
        end_line: int = Field(description="índice de la última línea del clip (incluida)")
        title: str
        hook: str = Field(description="texto corto (máx 7 palabras) que se muestra arriba al inicio")
        virality_score: int = Field(description="0-100")
        reason: str
        caption: str = Field(description="descripción para publicar en TikTok/Reels/Shorts")
        hashtags: list[str]

    class AIResult(BaseModel):
        clips: list[AIClip]

    segs = tr["segments"]
    lines = "\n".join(f"{k} [{s['s']:.1f}-{s['e']:.1f}] {s['text']}" for k, s in enumerate(segs))
    prompt = f"""Eres un editor experto en contenido viral para TikTok, YouTube Shorts e Instagram Reels.

Video: "{video_title}"
Transcripción (índice [inicio-fin en segundos] texto):
{lines}

Elige los {opts.num_clips} mejores clips para generar tráfico e interacción. Reglas:
- Cada clip debe durar entre {opts.min_len:.0f} y {opts.max_len:.0f} segundos (fin de end_line menos inicio de start_line).
- Debe enganchar en los primeros 2 segundos (pregunta, afirmación polémica, dato sorprendente, emoción).
- Debe entenderse solo, sin contexto previo, y terminar en una idea completa o un remate.
- Los clips no se pueden solapar.
- Ordénalos de mayor a menor virality_score.
- Escribe title, hook, caption y hashtags en el mismo idioma del video."""

    client = anthropic.Anthropic()
    resp = client.messages.parse(
        model=opts.ai_model,
        max_tokens=16000,
        output_config={"effort": "medium"},
        messages=[{"role": "user", "content": prompt}],
        output_format=AIResult,
    )
    if resp.stop_reason == "refusal" or resp.parsed_output is None:
        raise RuntimeError("La IA no devolvió clips")

    clips: list[Clip] = []
    used: list = []
    for c in resp.parsed_output.clips:
        i = max(0, min(c.start_line, len(segs) - 1))
        j = max(i, min(c.end_line, len(segs) - 1))
        # Ajustar a la duración pedida
        while j > i and segs[j]["e"] - segs[i]["s"] > opts.max_len * 1.15:
            j -= 1
        while j < len(segs) - 1 and segs[j]["e"] - segs[i]["s"] < opts.min_len * 0.85:
            j += 1
        rng = (segs[i]["s"], segs[j]["e"])
        if any(_overlaps(rng, u, gap=0) for u in used):
            continue
        used.append(rng)
        clips.append(Clip(index=len(clips) + 1, start=max(0, rng[0] - 0.15), end=rng[1] + 0.35,
                          title=c.title, hook=c.hook, score=c.virality_score, reason=c.reason,
                          caption=c.caption, hashtags=[h if h.startswith("#") else "#" + h for h in c.hashtags]))
        if len(clips) >= opts.num_clips:
            break
    return clips


def select_clips(src: Path, tr: dict, opts: Options, title: str, progress: ProgressFn = _noop) -> list[Clip]:
    if opts.use_ai and os.environ.get("ANTHROPIC_API_KEY"):
        try:
            progress(42, "La IA está eligiendo los mejores momentos...")
            clips = select_ai(tr, opts, title)
            if clips:
                return clips
        except Exception as e:  # cae al algoritmo local
            progress(42, f"IA no disponible ({str(e)[:80]}), usando algoritmo local...")
    progress(43, "Analizando energía, ganchos y ritmo...")
    return select_heuristic(src, tr, opts)


# --------------------------------------------------------------------------- #
# 4. Reencuadre (seguimiento de caras)
# --------------------------------------------------------------------------- #
_CASCADES = None
_YUNET = None
YUNET_URL = ("https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/"
             "face_detection_yunet_2023mar.onnx")
YUNET_PATH = ROOT / "models" / "face_detection_yunet_2023mar.onnx"


def _yunet():
    """Detector de caras moderno (YuNet). Se descarga solo la primera vez (~230 KB)."""
    global _YUNET
    if _YUNET is None:
        _YUNET = False
        try:
            if not YUNET_PATH.exists():
                import urllib.request
                YUNET_PATH.parent.mkdir(exist_ok=True)
                urllib.request.urlretrieve(YUNET_URL, YUNET_PATH)
            _YUNET = cv2.FaceDetectorYN.create(str(YUNET_PATH), "", (320, 320), 0.75, 0.3, 50)
        except Exception:
            YUNET_PATH.unlink(missing_ok=True)
            _YUNET = False
    return _YUNET


def _detectors():
    global _CASCADES
    if _CASCADES is None:
        base = Path(cv2.data.haarcascades)
        _CASCADES = (cv2.CascadeClassifier(str(base / "haarcascade_frontalface_default.xml")),
                     cv2.CascadeClassifier(str(base / "haarcascade_profileface.xml")))
    return _CASCADES


def _detect_faces(frame: np.ndarray) -> list[tuple[float, float, float]]:
    """Todas las caras del fotograma como (centro_x, centro_y, alto), en píxeles del original."""
    h, w = frame.shape[:2]
    sc = 640.0 / w
    resized = cv2.resize(frame, (640, int(h * sc)))
    yn = _yunet()
    if yn:
        yn.setInputSize((resized.shape[1], resized.shape[0]))
        _, faces = yn.detect(resized)
        faces = [] if faces is None else [tuple(f[:4]) for f in faces]
    else:
        small = cv2.equalizeHist(cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY))
        mins = int(small.shape[0] * 0.05)
        front, prof = _detectors()
        faces = list(front.detectMultiScale(small, 1.1, 6, minSize=(mins, mins)))
        if not faces:
            faces = list(prof.detectMultiScale(small, 1.1, 6, minSize=(mins, mins)))
            if not faces:
                flipped = cv2.flip(small, 1)
                faces = [(small.shape[1] - x - fw, y, fw, fh) for x, y, fw, fh in
                         prof.detectMultiScale(flipped, 1.1, 6, minSize=(mins, mins))]
    return [((x + fw / 2) / sc, (y + fh / 2) / sc, fh / sc) for x, y, fw, fh in faces]


def _facecam_cells(dets: list, src_w: int, src_h: int) -> set:
    """Detecta la webcam del streamer: una cara pequeña, quieta y en una esquina durante buena parte del clip."""
    n = max(1, sum(1 for d in dets if d is not None))
    counts: dict = {}
    for faces in dets:
        for cell in {(int(cx / src_w * 8), int(cy / src_h * 8)) for cx, cy, fh in (faces or [])
                     if fh < src_h * 0.22}:
            counts[cell] = counts.get(cell, 0) + 1
    cam = set()
    for (gx, gy), c in counts.items():
        corner = (gx <= 2 or gx >= 5) and (gy <= 2 or gy >= 5)
        if corner and c >= 0.3 * n:
            cam.add((gx, gy))
    return cam


def _hist(frame):
    small = cv2.resize(frame, (64, 36))
    hsv = cv2.cvtColor(small, cv2.COLOR_BGR2HSV)
    hst = cv2.calcHist([hsv], [0, 1], None, [16, 8], [0, 180, 0, 256])
    return cv2.normalize(hst, hst).flatten()


SPLIT_TOP = 0.38   # fracción de la altura para la webcam en el modo stream


def _facecam_box(faces: list, src_w: int, src_h: int) -> tuple[float, float, float]:
    """Cara media de la webcam del streamer: (centro_x, centro_y, alto) en píxeles del original."""
    arr = np.array(faces, dtype=float)
    return tuple(float(v) for v in np.median(arr, axis=0))


def analyze_framing(path: Path, crop_w: int, src_w: int, src_h: int, fps: float):
    """Devuelve la x central del recorte para cada frame, la fracción de frames con cara
    (sin contar la webcam del streamer) y la cara de la webcam (cx, cy, alto) o None si no hay."""
    cap = cv2.VideoCapture(str(path))
    step = max(1, int(round(fps / 6)))  # ~6 detecciones/seg
    dets, cuts, prev_h, n = [], [0], None, 0
    while True:
        ok = cap.grab()
        if not ok:
            break
        if n % step == 0:
            ok, fr = cap.retrieve()
            if not ok:
                break
            hst = _hist(fr)
            if prev_h is not None and cv2.compareHist(prev_h, hst, cv2.HISTCMP_CORREL) < 0.55:
                cuts.append(len(dets))
            prev_h = hst
            dets.append(_detect_faces(fr))
        n += 1
    cap.release()
    total = n
    if not dets:
        return np.full(max(total, 1), src_w / 2), 0.0, None, None
    cam = _facecam_cells(dets, src_w, src_h)
    cam_box, cam_on = None, None
    if cam:
        in_cam = lambda f: (int(f[0] / src_w * 8), int(f[1] / src_h * 8)) in cam  # noqa: E731
        cam_faces = [f for faces in dets for f in faces if in_cam(f)]
        cam_box = _facecam_box(cam_faces, src_w, src_h)
        # ¿la webcam está visible en cada momento? (el streamer a veces la oculta)
        on = np.array([any(in_cam(f) for f in faces) for faces in dets], dtype=float)
        win = 9  # ~1.5 s: ignora fallos sueltos del detector
        pad = np.pad(on, (win // 2, win // 2), mode="edge")
        on = np.array([np.median(pad[k:k + win]) for k in range(len(on))]) >= 0.5
        cam_on = np.repeat(on, step)[:total]
        if len(cam_on) < total:
            cam_on = np.pad(cam_on, (0, total - len(cam_on)), mode="edge")
    xs = []
    for faces in dets:
        real = [f for f in faces if (int(f[0] / src_w * 8), int(f[1] / src_h * 8)) not in cam]
        xs.append(max(real, key=lambda f: f[2])[0] if real else None)
    found = sum(x is not None for x in xs) / len(xs)

    arr = np.array([np.nan if x is None else x for x in xs], dtype=float)
    cuts = sorted(set(cuts + [len(arr)]))
    smooth = np.empty_like(arr)
    half = crop_w / 2
    for a, b in zip(cuts[:-1], cuts[1:]):
        seg = arr[a:b]
        valid = seg[~np.isnan(seg)]
        if len(valid) == 0:
            smooth[a:b] = np.nan
            continue
        # quitar falsos positivos: mediana robusta
        med = np.median(valid)
        if np.std(valid) < crop_w * 0.12:      # persona quieta: encuadre fijo
            smooth[a:b] = med
            continue
        filled = seg.copy()
        last = med
        for k in range(len(filled)):
            if np.isnan(filled[k]):
                filled[k] = last
            last = filled[k]
        # Cámara "de editor": encuadre quieto; si la persona se mueve de verdad
        # (lejos y durante ~0.7 s) se salta de golpe a la nueva posición, sin paneos lentos.
        win = 5
        pad = np.pad(filled, (win // 2, win // 2), mode="edge")
        target = np.array([np.median(pad[k:k + win]) for k in range(len(filled))])
        cur = float(np.median(target[: min(len(target), 6)]))
        away = 0
        for k in range(len(target)):
            if abs(target[k] - cur) > crop_w * 0.2:
                away += 1
                if away >= 4:
                    cur, away = float(target[k]), 0
            else:
                away = 0
            smooth[a + k] = cur
    # segmentos sin cara: centro, o heredar el vecino
    if np.all(np.isnan(smooth)):
        smooth[:] = src_w / 2
    else:
        idx = np.arange(len(smooth))
        good = ~np.isnan(smooth)
        smooth = np.interp(idx, idx[good], smooth[good])
    smooth = np.clip(smooth, half, src_w - half)
    per_frame = np.repeat(smooth, step)[:total]
    if len(per_frame) < total:
        per_frame = np.pad(per_frame, (0, total - len(per_frame)), mode="edge")
    return per_frame, found, cam_box, cam_on


# --------------------------------------------------------------------------- #
# 5. Subtítulos animados (ASS)
# --------------------------------------------------------------------------- #
def _ass_color(rgb: str, alpha: int = 0) -> str:
    rgb = rgb.lstrip("#")
    r, g, b = rgb[0:2], rgb[2:4], rgb[4:6]
    return f"&H{alpha:02X}{b}{g}{r}".upper()


STYLES = {
    #            texto      activo     borde      tamaño mayúsc  borde  sombra  caja
    "viral":   ("FFFFFF", "FFE600", "000000", 92, True, 7, 3, False),
    "caja":    ("FFFFFF", "00E676", "000000", 84, True, 0, 0, True),
    "karaoke": ("FFFFFF", "FF3DD8", "000000", 86, True, 6, 2, False),
    "neon":    ("FFFFFF", "00F0FF", "0A0A40", 88, True, 5, 0, False),
    "minimal": ("FFFFFF", "FFFFFF", "000000", 70, False, 3, 2, False),
}


def _fmt_t(t: float) -> str:
    t = max(0.0, t)
    h, rem = divmod(t, 3600)
    m, s = divmod(rem, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def _clean_word(w: str, upper: bool) -> str:
    w = w.replace("{", "(").replace("}", ")").replace("\\", "")
    if upper:
        w = w.upper().strip(",.;:")
    return w


def build_ass(words: list, clip: Clip, opts: Options, out_w: int, out_h: int, layout: str, path: Path) -> None:
    style = opts.caption_style if opts.caption_style in STYLES else "viral"
    txt, act, out, size, upper, bord, shad, box = STYLES[style]
    size = int(size * out_w / 1080)
    margin_v = int(out_h * (0.22 if layout == "track" else 0.24))
    if out_h <= out_w:
        margin_v = int(out_h * 0.10)
    hook_mv = int(out_h * 0.11)
    if layout == "gaming":   # gancho sobre la línea entre webcam y juego, sin tapar la cara
        hook_mv = int(out_h * SPLIT_TOP) - int(size * 0.72 * 0.75)
    bstyle = 3 if box else 1
    back = _ass_color("000000", 0x40) if box else _ass_color("000000", 0x80)

    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {out_w}
PlayResY: {out_h}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Main,{opts.font},{size},{_ass_color(txt)},{_ass_color(act)},{_ass_color(out)},{back},-1,0,0,0,100,100,1,0,{bstyle},{bord if not box else 14},{shad},2,60,60,{margin_v},1
Style: Hook,{opts.font},{int(size*0.72)},{_ass_color('111111')},{_ass_color('111111')},{_ass_color('FFFFFF')},{_ass_color('FFFFFF')},-1,0,0,0,100,100,0,0,3,18,0,8,80,80,{hook_mv},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    ev = []
    if opts.show_hook and clip.hook:
        hook = _clean_word(clip.hook, True)
        ev.append(f"Dialogue: 1,{_fmt_t(0)},{_fmt_t(min(3.2, clip.duration))},Hook,,0,0,0,,"
                  f"{{\\fad(150,250)\\fscx80\\fscy80\\t(0,180,\\fscx100\\fscy100)}}{hook}")

    if style != "none" and opts.caption_style != "none":
        # agrupar palabras en líneas cortas
        groups, cur = [], []
        for w in words:
            gap = w["s"] - cur[-1]["e"] if cur else 0
            if cur and (len(cur) >= opts.words_per_line or gap > 0.6 or re.search(r"[.!?]$", cur[-1]["w"])):
                groups.append(cur)
                cur = []
            cur.append(w)
        if cur:
            groups.append(cur)

        act_c = _ass_color(act)
        for gi, g in enumerate(groups):
            g_end = g[-1]["e"] + 0.25
            if gi + 1 < len(groups):
                g_end = min(g_end, groups[gi + 1][0]["s"])
            toks = [_clean_word(w["w"], upper) for w in g]
            if style == "karaoke":
                parts = []
                for k, w in enumerate(g):
                    nxt = g[k + 1]["s"] if k + 1 < len(g) else w["e"]
                    parts.append(f"{{\\kf{max(1, int((nxt - w['s']) * 100))}}}{toks[k]}")
                # en karaoke: Primary = color ya cantado, Secondary = antes
                ev.append(f"Dialogue: 0,{_fmt_t(g[0]['s'])},{_fmt_t(g_end)},Main,,0,0,0,,"
                          f"{{\\1c{act_c}\\2c{_ass_color(txt)}\\fad(60,0)}}" + " ".join(parts))
                continue
            if style == "minimal":
                ev.append(f"Dialogue: 0,{_fmt_t(g[0]['s'])},{_fmt_t(g_end)},Main,,0,0,0,,"
                          f"{{\\fad(80,80)}}" + " ".join(toks))
                continue
            for k, w in enumerate(g):
                s = w["s"]
                e = g[k + 1]["s"] if k + 1 < len(g) else g_end
                if e <= s:
                    continue
                pieces = []
                for m, t in enumerate(toks):
                    if m == k:
                        glow = "\\blur4" if style == "neon" else ""
                        pieces.append(f"{{\\1c{act_c}{glow}\\fscx88\\fscy88\\t(0,90,\\fscx112\\fscy112)"
                                      f"\\t(90,170,\\fscx106\\fscy106)}}{t}{{\\r}}")
                    else:
                        pieces.append(t)
                intro = "\\fscx70\\fscy70\\t(0,100,\\fscx100\\fscy100)" if k == 0 else ""
                ev.append(f"Dialogue: 0,{_fmt_t(s)},{_fmt_t(e)},Main,,0,0,0,,{{{intro}}}" + " ".join(pieces))

    path.write_text(head + "\n".join(ev) + "\n", encoding="utf-8")


def _filter_path(p: Path) -> str:
    s = str(p.resolve()).replace("\\", "/")
    return s.replace(":", "\\:").replace("'", "\\'")


# --------------------------------------------------------------------------- #
# 6. Render
# --------------------------------------------------------------------------- #
def _blur_bg(frame: np.ndarray, out_w: int, out_h: int) -> np.ndarray:
    h, w = frame.shape[:2]
    sc = max(out_w / w, out_h / h)
    small = cv2.resize(frame, (max(1, int(w * sc / 8)), max(1, int(h * sc / 8))), interpolation=cv2.INTER_AREA)
    small = cv2.GaussianBlur(small, (0, 0), 6)
    big = cv2.resize(small, (int(w * sc) + 2, int(h * sc) + 2), interpolation=cv2.INTER_LINEAR)
    y0, x0 = (big.shape[0] - out_h) // 2, (big.shape[1] - out_w) // 2
    bg = big[y0 : y0 + out_h, x0 : x0 + out_w]
    return (bg * 0.55).astype(np.uint8)


def render_clip(src: Path, clip: Clip, tr: dict, opts: Options, outdir: Path, meta: dict,
                progress: ProgressFn = _noop, p0: float = 0, p1: float = 100) -> Clip:
    out_w, out_h = ASPECTS.get(opts.aspect, ASPECTS["9:16"])
    fps = min(opts.fps or meta["fps"], 60)
    name = f"{clip.index:02d}_{slug(clip.title)}"
    tmp = outdir / f".{name}_cut.mp4"
    final = outdir / f"{name}.mp4"
    ass = outdir / f".{name}.ass"

    # 6.1 corte preciso (intermedio casi sin pérdida)
    progress(p0, f"Clip {clip.index}: cortando...")
    run(["ffmpeg", "-y", "-v", "error", "-ss", f"{clip.start:.3f}", "-i", str(src), "-t", f"{clip.duration:.3f}",
         "-map", "0:v:0", "-map", "0:a:0?", "-r", f"{fps:.3f}",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "10", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "256k",
         str(tmp)])
    m = probe(tmp)
    sw, sh = m["width"], m["height"]

    # 6.2 encuadre
    target_ratio = out_w / out_h
    crop_w = min(sw, int(round(sh * target_ratio / 2) * 2))
    crop_h = sh if crop_w < sw else min(sh, int(round(sw / target_ratio / 2) * 2))
    layout = opts.layout
    xs, cam, cam_on = None, None, None
    if crop_w < sw and layout in ("auto", "track", "gaming"):
        progress(p0 + (p1 - p0) * 0.15, f"Clip {clip.index}: analizando el encuadre...")
        xs, found, cam, cam_on = analyze_framing(tmp, crop_w, sw, sh, fps)
        if layout == "auto":
            if cam:              # stream de videojuego: webcam arriba + juego abajo
                layout = "gaming"
            else:
                layout = "track" if found >= 0.35 else "blur"
        if layout == "gaming":
            xs = None            # el juego va con recorte fijo al centro (personaje en 3ª persona)
            if cam:
                progress(p0 + (p1 - p0) * 0.25, f"Clip {clip.index}: webcam detectada -> streamer arriba, juego abajo")
            else:
                layout = "gamecenter"
    elif layout == "auto":
        layout = "track"  # mismo aspect o más estrecho: recorte centrado

    # geometría del modo stream: panel de webcam arriba y juego abajo
    if layout == "gaming":
        top_h = int(out_h * SPLIT_TOP) // 2 * 2
        bot_h = out_h - top_h
        fcx, fcy, fhh = cam
        # la webcam está en una esquina: correr un poco el centro hacia ese lado para no meter juego
        fcx += -0.15 * fhh if fcx < sw / 2 else 0.15 * fhh
        cw = min(sw, 2.1 * fhh)
        ch = min(sh, cw * top_h / out_w)
        cw = ch * out_w / top_h
        cx0 = int(np.clip(fcx - cw / 2, 0, sw - cw))
        cy0 = int(np.clip(fcy - ch * 0.45, 0, sh - ch))
        cam_rect = (cx0, cy0, int(cx0 + cw), int(cy0 + ch))
        gw = min(sw, int(round(sh * out_w / bot_h / 2) * 2))
        gh = sh if gw < sw else min(sh, int(round(sw * bot_h / out_w / 2) * 2))
        game_rect = ((sw - gw) // 2, (sh - gh) // 2, (sw - gw) // 2 + gw, (sh - gh) // 2 + gh)

    # 6.3 subtítulos
    words = [dict(w, s=w["s"] - clip.start, e=w["e"] - clip.start)
             for s in tr["segments"] for w in s["words"]
             if w["s"] >= clip.start - 0.05 and w["e"] <= clip.end + 0.05]
    build_ass(words, clip, opts, out_w, out_h, layout, ass)

    # 6.4 render final: frames reencuadrados por pipe -> ffmpeg (+ subtítulos + audio normalizado)
    vf = f"ass='{_filter_path(ass)}'"
    if FONTS_DIR.exists() and any(FONTS_DIR.iterdir()):
        vf = f"ass='{_filter_path(ass)}':fontsdir='{_filter_path(FONTS_DIR)}'"
    vf += ",format=yuv420p"
    cmd = ["ffmpeg", "-y", "-v", "error",
           "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{out_w}x{out_h}", "-r", f"{fps:.3f}", "-i", "-",
           "-i", str(tmp), "-map", "0:v", "-map", "1:a?", "-vf", vf,
           "-c:v", "libx264", "-preset", opts.preset, "-crf", str(opts.crf), "-profile:v", "high",
           "-c:a", "aac", "-b:a", "192k", "-ar", "48000"]
    if opts.loudnorm and m["has_audio"]:
        cmd += ["-af", "loudnorm=I=-14:TP=-1.5:LRA=11"]
    cmd += ["-movflags", "+faststart", "-shortest", str(final)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)

    cap = cv2.VideoCapture(str(tmp))
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 1
    k = 0
    try:
        while True:
            ok, fr = cap.read()
            if not ok:
                break
            if layout == "blur" and crop_w < sw:
                canvas = _blur_bg(fr, out_w, out_h)
                fh = int(sh * out_w / sw) // 2 * 2
                fg = cv2.resize(fr, (out_w, fh), interpolation=cv2.INTER_LANCZOS4)
                y0 = (out_h - fh) // 2 - int(out_h * 0.04)
                canvas[y0 : y0 + fh] = fg
                outf = canvas
            elif layout == "gaming" and cam_on[min(k, len(cam_on) - 1)]:
                x0, y0, x1, y1 = cam_rect
                top = cv2.resize(fr[y0:y1, x0:x1], (out_w, top_h), interpolation=cv2.INTER_LANCZOS4)
                x0, y0, x1, y1 = game_rect
                bot = cv2.resize(fr[y0:y1, x0:x1], (out_w, bot_h), interpolation=cv2.INTER_LANCZOS4)
                outf = np.vstack([top, bot])
                outf[top_h - 3 : top_h + 3] = 0   # línea separadora
            else:
                cx = xs[min(k, len(xs) - 1)] if xs is not None else sw / 2
                x0 = int(np.clip(cx - crop_w / 2, 0, sw - crop_w))
                y0 = (sh - crop_h) // 2
                crop = fr[y0 : y0 + crop_h, x0 : x0 + crop_w]
                outf = cv2.resize(crop, (out_w, out_h), interpolation=cv2.INTER_LANCZOS4)
            proc.stdin.write(outf.tobytes())
            k += 1
            if k % 30 == 0:
                progress(p0 + (p1 - p0) * (0.3 + 0.68 * k / total), f"Clip {clip.index}: renderizando {k}/{total} frames")
    finally:
        cap.release()
        proc.stdin.close()
        err = proc.stderr.read().decode(errors="ignore")
        proc.wait()
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg falló en el clip {clip.index}: {err[-1500:]}")

    thumb = outdir / f"{name}.jpg"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{min(1.5, clip.duration / 2):.2f}", "-i", str(final),
                    "-frames:v", "1", "-q:v", "3", str(thumb)])
    for f in (tmp, ass):
        f.unlink(missing_ok=True)
    clip.file, clip.thumb = final.name, thumb.name if thumb.exists() else ""
    return clip


# --------------------------------------------------------------------------- #
# 7. Revisión de calidad con Claude
# --------------------------------------------------------------------------- #
REVIEW_FRAMES = 9


def _frames_b64(video: Path, duration: float, n: int = REVIEW_FRAMES) -> list[tuple[float, str]]:
    """Saca n fotogramas repartidos por el clip (el primero a 0.5s para ver el gancho)."""
    import base64
    out = []
    times = [min(0.5, duration / 4)] + [duration * (k + 0.5) / (n - 1) for k in range(n - 1)]
    for t in times:
        r = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", str(video), "-frames:v", "1",
                            "-vf", "scale=540:-2", "-q:v", "4", "-f", "image2pipe", "-vcodec", "mjpeg", "-"],
                           capture_output=True)
        if r.returncode == 0 and r.stdout:
            out.append((t, base64.standard_b64encode(r.stdout).decode()))
    return out


def review_clip(clip: Clip, video: Path, tr: dict, opts: Options) -> dict:
    """Claude mira fotogramas + transcripción del clip y dice si está listo para publicar."""
    import anthropic
    from pydantic import BaseModel, Field

    class Problema(BaseModel):
        tipo: str = Field(description="encuadre | subtitulos | gancho | inicio | final | contenido | tecnico")
        gravedad: str = Field(description="alta | media | baja")
        detalle: str
        segundo: Optional[float] = Field(default=None, description="segundo del clip donde se ve, si aplica")

    class Revision(BaseModel):
        aprobado: bool = Field(description="true si se puede publicar tal cual")
        nota: int = Field(description="calidad general 0-100")
        resumen: str = Field(description="una frase con el veredicto")
        problemas: list[Problema]
        sugerencias: list[str] = Field(description="cambios concretos para mejorarlo")

    segs = tr["segments"]
    inside = [s for s in segs if s["e"] > clip.start + 0.2 and s["s"] < clip.end - 0.2]
    before = [s for s in segs if s["e"] <= clip.start + 0.2][-1:]
    after = [s for s in segs if s["s"] >= clip.end - 0.2][:1]
    texto = " ".join(s["text"] for s in inside)

    content: list = [{"type": "text", "text": f"""Eres el editor jefe de un canal de TikTok/Shorts/Reels. Revisa este clip antes de publicarlo.

Título: {clip.title}
Gancho (texto arriba los primeros 3 s): {clip.hook or "(ninguno)"}
Duración: {clip.duration:.1f} s · Formato {opts.aspect} · Estilo de subtítulos: {opts.caption_style}

Lo que se dice en el clip:
"{texto}"

Frase justo ANTES del clip en el video original: "{before[0]['text'] if before else '(es el inicio del video)'}"
Frase justo DESPUÉS del clip: "{after[0]['text'] if after else '(es el final del video)'}"

Abajo tienes {REVIEW_FRAMES} fotogramas del clip ya editado. Revisa:
1. Encuadre: ¿la persona/sujeto principal está bien centrado o aparece cortado/fuera de cuadro? ¿hay barras negras o fotogramas vacíos?
2. Subtítulos: ¿se leen bien, tapan la cara u otro texto del video, están bien escritos?
3. Gancho: ¿los primeros segundos enganchan? ¿el titular de arriba se lee y tiene sentido?
4. Inicio y final: ¿empieza o termina a mitad de frase/idea? Usa las frases de antes y después para juzgarlo.
5. Contenido: ¿se entiende solo, sin contexto previo? ¿tiene potencial para retener al espectador?

Sé exigente pero justo: aprueba solo si se puede publicar tal cual. Responde en español."""}]
    for t, b64 in _frames_b64(video, clip.duration):
        content.append({"type": "text", "text": f"Fotograma a los {t:.1f} s:"})
        content.append({"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": b64}})

    resp = anthropic.Anthropic().messages.parse(
        model=opts.ai_model,
        max_tokens=16000,
        output_config={"effort": "medium"},
        messages=[{"role": "user", "content": content}],
        output_format=Revision,
    )
    if resp.stop_reason == "refusal" or resp.parsed_output is None:
        raise RuntimeError("la IA no devolvió revisión")
    return resp.parsed_output.model_dump()


# --------------------------------------------------------------------------- #
# Orquestador
# --------------------------------------------------------------------------- #
def process(source: str, workdir: Path, opts: Options, progress: ProgressFn = _noop) -> dict:
    workdir.mkdir(parents=True, exist_ok=True)
    if re.match(r"^https?://", source):
        progress(1, "Descargando video de YouTube...")
        src, title = download(source, workdir, opts, progress)
    else:
        src = Path(source)
        title = src.stem
    meta = probe(src)
    progress(11, f"Video: {meta['width']}x{meta['height']} @ {meta['fps']:.0f}fps, {meta['duration']:.0f}s")

    tr = transcribe(src, workdir, opts, progress)
    clips = select_clips(src, tr, opts, title, progress)
    if not clips:
        raise RuntimeError("No se encontraron segmentos con voz para recortar.")

    outdir = workdir / "clips"
    outdir.mkdir(exist_ok=True)
    span = 55 / len(clips)
    reviewing = opts.review and bool(os.environ.get("ANTHROPIC_API_KEY"))
    done = []
    for n, c in enumerate(clips):
        p0 = 45 + n * span
        p_end = p0 + span * (0.85 if reviewing else 1)
        c = render_clip(src, c, tr, opts, outdir, meta, progress, p0, p_end)
        if reviewing:
            progress(p_end, f"Clip {c.index}: la IA está revisando el resultado...")
            try:
                c.review = review_clip(c, outdir / c.file, tr, opts)
            except Exception as e:
                c.review = {"error": str(e)[:200]}
        done.append(c)
    result = {"title": title, "language": tr.get("language"), "source": meta,
              "clips": [dict(asdict(c), duration=round(c.duration, 2)) for c in done]}
    (workdir / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    progress(100, f"¡Listo! {len(done)} clips generados.")
    return result
