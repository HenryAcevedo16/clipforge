"""
NovoClip - motor de clipping.

Flujo:
  1. Descarga el video de YouTube en la mejor calidad <=1080p (yt-dlp)
  2. Transcribe con marcas de tiempo por palabra (faster-whisper)
  3. Elige los mejores momentos (Claude si hay ANTHROPIC_API_KEY, si no un algoritmo local)
  4. Reencuadra a vertical siguiendo la cara del que habla (OpenCV) o con fondo desenfocado
  5. Quema subtítulos animados palabra por palabra (ASS + libass) y exporta en 1080x1920
"""

from __future__ import annotations

# Compatibilidad: las variables CLIPFORGE_* antiguas siguen funcionando como NOVOCLIP_*
import os as _os
for _k, _v in list(_os.environ.items()):
    if _k.startswith("CLIPFORGE_"):
        _os.environ.setdefault("NOVOCLIP_" + _k[len("CLIPFORGE_"):], _v)


import json
import math
import os
import re
import shutil
import time
import subprocess
import sys
from dataclasses import dataclass, asdict, field, replace
from pathlib import Path
from typing import Callable, Optional
import warnings

# Avisos inofensivos de Hugging Face al bajar el modelo de Whisper en Windows
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
os.environ.setdefault("HF_HUB_VERBOSITY", "error")
warnings.filterwarnings("ignore", module="huggingface_hub")

import cv2
import numpy as np
from novoclip_signals import audience_bonus, replay_intervals

ROOT = Path(__file__).resolve().parent
FONTS_DIR = ROOT / "fonts"
MUSIC_DIR = ROOT / "music"
ProgressFn = Callable[[float, str], None]


# --------------------------------------------------------------------------- #
# Cancelación: cada trabajo corre en su hilo; se puede detener al instante
# --------------------------------------------------------------------------- #
import threading


class Cancelled(BaseException):  # BaseException: ningún "except Exception" la oculta
    """El usuario canceló la generación."""


_CANCEL: dict = {}   # id del hilo -> threading.Event
_ACTIVE: dict = {}   # id del hilo -> procesos externos en marcha (ffmpeg, claude...)
_REG_LOCK = threading.Lock()


def begin_job() -> int:
    ident = threading.get_ident()
    with _REG_LOCK:
        _CANCEL[ident] = threading.Event()
        _ACTIVE[ident] = set()
    return ident


def end_job() -> None:
    global _AI_PROVIDER
    ident = threading.get_ident()
    with _REG_LOCK:
        _CANCEL.pop(ident, None)
        _ACTIVE.pop(ident, None)
        if not _CANCEL:             # la IA elegida para un trabajo no se queda pegada (salvo que haya otro trabajo en marcha)
            _AI_PROVIDER = "auto"


def check_cancel() -> None:
    ev = _CANCEL.get(threading.get_ident())
    if ev is not None and ev.is_set():
        raise Cancelled("Generación cancelada")


def _kill_tree(proc: subprocess.Popen) -> None:
    try:
        if os.name == "nt":  # mata también los procesos hijos (p. ej. claude.cmd -> node)
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], capture_output=True)
        else:
            proc.kill()
    except Exception:
        pass


def cancel_thread(ident: int) -> None:
    """Pide cancelar el trabajo del hilo `ident` y mata sus procesos externos."""
    with _REG_LOCK:
        ev = _CANCEL.get(ident)
        procs = list(_ACTIVE.get(ident, ()))
    if ev is not None:
        ev.set()
    for pr in procs:
        _kill_tree(pr)


def _register(proc: subprocess.Popen) -> None:
    with _REG_LOCK:
        s = _ACTIVE.get(threading.get_ident())
        if s is not None:
            s.add(proc)


def _unregister(proc: subprocess.Popen) -> None:
    with _REG_LOCK:
        s = _ACTIVE.get(threading.get_ident())
        if s is not None:
            s.discard(proc)


def _sp_popen(cmd, **kw) -> subprocess.Popen:
    check_cancel()
    proc = subprocess.Popen(cmd, **kw)
    _register(proc)
    return proc


def _sp_run(cmd, input=None, capture_output=False, timeout=None, **kw) -> subprocess.CompletedProcess:
    """Como subprocess.run, pero se puede cancelar desde la app."""
    check_cancel()
    if capture_output:
        kw.setdefault("stdout", subprocess.PIPE)
        kw.setdefault("stderr", subprocess.PIPE)
    if input is not None:
        kw["stdin"] = subprocess.PIPE
    proc = subprocess.Popen(cmd, **kw)
    _register(proc)
    try:
        out, err = proc.communicate(input, timeout=timeout)
    except subprocess.TimeoutExpired:
        _kill_tree(proc)
        proc.communicate()
        raise
    finally:
        _unregister(proc)
    check_cancel()
    return subprocess.CompletedProcess(cmd, proc.returncode, out, err)



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
    layout: str = "auto"            # auto | speaker (quien habla) | wide (abierto) | split (dividido) | track | blur | gaming (webcam arriba + juego) | gamecenter (solo juego)
    caption_style: str = "viral"    # viral | caja | karaoke | neon | minimal | none
    words_per_line: int = 3
    font: str = "Arial Black"
    show_hook: bool = True          # titular arriba los primeros segundos
    language: Optional[str] = None  # None = autodetectar ("es", "en", ...)
    whisper_model: str = "auto"     # auto (según tu equipo) | tiny | base | small | medium | large-v3 | large-v3-turbo
    use_ai: bool = False            # elegir clips con IA (gasta tokens). Por defecto se eligen gratis en local; la IA entra al pulsar «Optimizar con IA»
    ai_model: str = "claude-sonnet-5-5"
    use_captions: bool = True       # YouTube: elegir los clips con los subtítulos del video (sin bajar nada)
    smart_download: bool = True     # YouTube: bajar solo el audio y luego solo los trozos elegidos
    ai_provider: str = "auto"       # auto (Claude y, si no hay, Gemini) | claude | gemini
    crf: int = 16                   # calidad final (menor = mejor): 14 original · 16 máxima · 18 alta
    source_quality: str = "max"     # max: la mejor resolución de YouTube (hasta 4K en trozos, 1440p completo) | 1080
    preset: str = "medium"
    fps: Optional[float] = None     # None = el del original (máx 60)
    loudnorm: bool = True
    review: bool = False            # la IA revisa cada clip al terminarlo (gasta tokens; «Optimizar con IA» siempre revisa)
    manual_ranges: list = field(default_factory=list)   # [[inicio, fin], ...] en segundos: el usuario elige los cortes (sin selección de la IA)
    video_ai: bool = False          # con Gemini: la IA VE el video del clip (imagen + audio) al revisarlo, no solo fotogramas sueltos
    cookies_from_browser: Optional[str] = None  # "chrome", "firefox"... por si YouTube lo pide
    # --- edición para retener al espectador ---
    jumpcuts: bool = True           # quitar silencios y pausas largas
    zoom: bool = True               # zoom dinámico: cambio de plano en cada corte + golpe en palabras clave
    progress_bar: bool = True       # barra de progreso arriba
    color_pop: bool = True          # más contraste, color y nitidez
    music: bool = True              # música de fondo (si hay archivos en la carpeta music/) que baja con la voz
    music_volume: float = 0.18
    highlight_keywords: bool = True  # resaltar en color las palabras clave de los subtítulos
    # --- Kit de marca: logo como marca de agua ---
    logo_path: str = ""             # imagen del logo (png/jpg/webp); vacío = sin logo
    logo_on: bool = True            # interruptor (también por clip en el editor)
    logo_pos: str = "br"            # tl | tr | bl | br | center
    logo_size: float = 16.0         # % del ancho del video
    logo_opacity: float = 80.0      # % de opacidad
    # --- velocidad ---
    # --- modo en vivo ---
    live_window: int = 180          # cada cuántos segundos se analiza lo nuevo del directo
    live_segment: int = 20          # tamaño de los trozos de grabación
    live_clips_per_window: int = 2  # máximo de clips por tramo
    live_min_score: int = 60        # nota mínima de la IA para sacar un clip del directo (baja sola si pasan tramos sin clips)
    live_chat: bool = True          # usar los picos del chat de Twitch como señal
    snap_silence: bool = True       # cortar en el silencio real del audio
    refine: bool = True             # segunda pasada de la IA: afinar inicio y final palabra por palabra
    complete_ideas: bool = True     # que ningún clip termine antes de cerrar la idea de quien habla
    device: str = "auto"            # auto (GPU si hay) | gpu | cpu
    speed: str = "auto"             # auto (según tu equipo) | rapido | normal | calidad


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
    keywords: list = field(default_factory=list)   # palabras a resaltar (color + zoom)
    layout: str = ""
    out_duration: float = 0.0                       # duración final (tras quitar silencios)

    @property
    def duration(self) -> float:
        return self.end - self.start


# --------------------------------------------------------------------------- #
# Utilidades
# --------------------------------------------------------------------------- #
def run(cmd: list, **kw) -> subprocess.CompletedProcess:
    r = _sp_run(cmd, capture_output=True, text=True, **kw)
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
# Hardware: GPU o procesador
# --------------------------------------------------------------------------- #
_HW: Optional[dict] = None
GPU_ENCODERS = ("h264_nvenc", "h264_qsv", "h264_amf")   # NVIDIA, Intel, AMD
ENCODER_NAMES = {"h264_nvenc": "NVIDIA NVENC", "h264_qsv": "Intel Quick Sync", "h264_amf": "AMD AMF"}


def _add_nvidia_dll_dirs() -> None:
    """En Windows, faster-whisper necesita cuBLAS/cuDNN. Si están instalados con pip
    (nvidia-cublas-cu12, nvidia-cudnn-cu12), se añaden al buscador de DLLs."""
    try:
        import importlib.util
        for pkg in ("nvidia.cublas", "nvidia.cudnn", "nvidia.cuda_runtime", "nvidia.cuda_nvrtc"):
            spec = importlib.util.find_spec(pkg)
            if not spec or not spec.submodule_search_locations:
                continue
            for base in spec.submodule_search_locations:
                for sub in ("bin", "lib"):
                    d = Path(base) / sub
                    if d.is_dir():
                        os.environ["PATH"] = str(d) + os.pathsep + os.environ.get("PATH", "")
                        if hasattr(os, "add_dll_directory"):
                            try:
                                os.add_dll_directory(str(d))
                            except OSError:
                                pass
    except Exception:
        pass


def _encoder_test(enc: str) -> tuple[Optional[str], str]:
    """Prueba de verdad el codificador con un video corto. Devuelve (pix_fmt que funcionó, error)."""
    err = ""
    for fmt in (("nv12", "yuv420p") if enc != "h264_nvenc" else ("yuv420p", "nv12")):
        try:
            r = _sp_run(["ffmpeg", "-hide_banner", "-v", "error", "-f", "lavfi",
                                "-i", "testsrc2=s=1280x720:r=30:d=0.5", "-pix_fmt", fmt, "-c:v", enc,
                                "-f", "null", "-"], capture_output=True, text=True, timeout=45)
            if r.returncode == 0:
                return fmt, ""
            lines = [l for l in r.stderr.strip().splitlines()
                     if l.strip() and "Nothing was written" not in l and "Conversion failed" not in l]
            err = (" | ".join(lines[-3:]) or "error desconocido")[:400]
        except Exception as e:
            err = str(e)[:300]
    return None, err


def _windows_gpus() -> list[str]:
    """Nombres de las tarjetas gráficas del equipo (Windows)."""
    if os.name != "nt":
        return []
    try:
        r = _sp_run(["powershell", "-NoProfile", "-Command",
                            "Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty Name"],
                           capture_output=True, text=True, timeout=20)
        return [l.strip() for l in r.stdout.splitlines() if l.strip()]
    except Exception:
        return []


def hw_info(refresh: bool = False) -> dict:
    """Detecta (una sola vez) qué puede acelerar la GPU de este equipo."""
    global _HW
    if _HW is not None and not refresh:
        return _HW
    _add_nvidia_dll_dirs()
    info = {"gpu_name": None, "gpus": _windows_gpus(), "whisper_cuda": False, "encoder": None,
            "encoder_name": None, "encoder_pix": None, "ffmpeg_gpu_encoders": [], "errors": {},
            "ffmpeg": shutil.which("ffmpeg"), "cpu_threads": os.cpu_count() or 4,
            "whispercpp": None}
    try:
        r = _sp_run(["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
                           capture_output=True, text=True, timeout=10)
        if r.returncode == 0 and r.stdout.strip():
            info["gpu_name"] = r.stdout.strip().splitlines()[0]
    except Exception:
        pass
    if not info["gpu_name"] and info["gpus"]:
        # preferir la tarjeta dedicada (RX, RTX, Arc...) sobre los gráficos integrados del procesador
        def rank(g: str) -> int:
            if re.search(r"\bRX\b|RTX|GTX|GeForce|Arc\b|Radeon Pro|FirePro", g, re.I):
                return 0
            if re.search(r"Radeon\(TM\) Graphics|Radeon Graphics|UHD|Iris|HD Graphics|Vega \d+ Graphics", g, re.I):
                return 2
            return 1
        info["gpu_name"] = sorted(info["gpus"], key=rank)[0]
    try:
        import ctranslate2
        info["whisper_cuda"] = ctranslate2.get_cuda_device_count() > 0
    except Exception:
        pass
    try:
        listed = _sp_run(["ffmpeg", "-hide_banner", "-encoders"], capture_output=True, text=True).stdout
    except Exception:
        listed = ""
    info["ffmpeg_gpu_encoders"] = [e for e in GPU_ENCODERS if e in listed]

    # probar primero el codificador del fabricante de tu tarjeta
    names = " ".join(info["gpus"] + [info["gpu_name"] or ""]).lower()
    order = list(GPU_ENCODERS)
    if re.search(r"radeon|amd", names):
        order = ["h264_amf", "h264_qsv", "h264_nvenc"]
    elif re.search(r"intel|arc|iris|uhd", names) and not re.search(r"nvidia|geforce|rtx", names):
        order = ["h264_qsv", "h264_amf", "h264_nvenc"]
    for enc in order:
        if enc not in listed:
            info["errors"][enc] = "tu FFmpeg no incluye este codificador"
            continue
        pix, err = _encoder_test(enc)
        if pix:
            info["encoder"], info["encoder_name"], info["encoder_pix"] = enc, ENCODER_NAMES[enc], pix
            break
        info["errors"][enc] = err
    try:
        info["whispercpp"] = whispercpp_exe()
    except NameError:
        pass
    _HW = info
    return info


# --------------------------------------------------------------------------- #
# Perfil del equipo: se leen los componentes y se elige la configuración óptima
# --------------------------------------------------------------------------- #
_PROFILE: Optional[dict] = None


def _ps(cmd: str) -> str:
    try:
        r = subprocess.run(["powershell", "-NoProfile", "-Command", cmd], capture_output=True, text=True, timeout=25)
        return r.stdout.strip()
    except Exception:
        return ""


def _ram_gb() -> Optional[float]:
    try:
        if os.name == "nt":
            import ctypes

            class MS(ctypes.Structure):
                _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                            ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                            ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                            ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                            ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
            m = MS()
            m.dwLength = ctypes.sizeof(MS)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
            return round(m.ullTotalPhys / 2 ** 30, 1)
        if Path("/proc/meminfo").exists():
            kb = int(re.search(r"MemTotal:\s+(\d+)", Path("/proc/meminfo").read_text()).group(1))
            return round(kb / 2 ** 20, 1)
        r = subprocess.run(["sysctl", "-n", "hw.memsize"], capture_output=True, text=True)
        return round(int(r.stdout.strip()) / 2 ** 30, 1)
    except Exception:
        return None


def _cpu_name() -> str:
    try:
        if os.name == "nt":
            n = _ps("(Get-CimInstance Win32_Processor | Select-Object -First 1 -ExpandProperty Name)")
            if n:
                return re.sub(r"\s+", " ", n)
        if Path("/proc/cpuinfo").exists():
            m = re.search(r"model name\s*:\s*(.+)", Path("/proc/cpuinfo").read_text())
            if m:
                return m.group(1).strip()
        import platform
        return platform.processor() or "procesador"
    except Exception:
        return "procesador"


def _vram_gb(gpu_name: Optional[str]) -> Optional[float]:
    """Memoria de la tarjeta gráfica (NVIDIA con nvidia-smi; AMD/Intel en Windows por el registro)."""
    try:
        r = subprocess.run(["nvidia-smi", "--query-gpu=memory.total", "--format=csv,noheader,nounits"],
                           capture_output=True, text=True, timeout=10)
        if r.returncode == 0 and r.stdout.strip():
            return round(int(r.stdout.strip().splitlines()[0]) / 1024, 1)
    except Exception:
        pass
    if os.name == "nt":
        out = _ps("Get-ItemProperty 'HKLM:\\SYSTEM\\ControlSet001\\Control\\Class\\{4d36e968-e325-11ce-bfc1-08002be10318}\\0*' "
                  "-ErrorAction SilentlyContinue | ForEach-Object { \"$($_.DriverDesc)|$($_.'HardwareInformation.qwMemorySize')\" }")
        best = None
        for line in out.splitlines():
            name, _, mem = line.partition("|")
            if mem.strip().isdigit():
                gb = int(mem) / 2 ** 30
                if gpu_name and name.strip().lower() == gpu_name.lower():
                    return round(gb, 1)
                best = max(best or 0, gb)
        return round(best, 1) if best else None
    return None


def system_profile(refresh: bool = False) -> dict:
    """Lee los componentes del equipo y decide la mejor configuración para él."""
    global _PROFILE
    if _PROFILE is not None and not refresh:
        return _PROFILE
    hw = hw_info(refresh)
    threads = hw.get("cpu_threads") or os.cpu_count() or 4
    ram = _ram_gb()
    gpu = hw.get("gpu_name")
    vram = _vram_gb(gpu) if gpu else None
    if hw.get("whisper_cuda"):
        engine = "cuda"
    elif hw.get("whispercpp"):
        engine = "vulkan"
    else:
        engine = "cpu"
    v = vram or 0
    if engine == "cuda":
        model = "large-v3-turbo" if v >= 6 else "small"
    elif engine == "vulkan":
        model = "large-v3-turbo" if v >= 8 else ("small" if v >= 4 else "base")
    else:
        model = "small" if threads >= 12 and (ram or 0) >= 12 else ("base" if threads >= 6 else "tiny")
    fast_render = bool(hw.get("encoder"))
    speed = "normal" if (fast_render or threads >= 8) else "rapido"
    gpu_accel = engine != "cpu" or fast_render
    if gpu_accel and (ram or 0) >= 16 and (engine != "cpu" or threads >= 12):
        tier = "potente"
    elif gpu_accel or threads >= 8:
        tier = "medio"
    else:
        tier = "básico"
    tname = {"cuda": "GPU NVIDIA (CUDA)", "vulkan": "GPU (Vulkan)", "cpu": f"procesador ({threads} hilos)"}[engine]
    rname = f"GPU ({hw['encoder_name']})" if fast_render else "procesador (x264)"
    _PROFILE = {
        "cpu": _cpu_name(), "threads": threads, "ram_gb": ram, "gpu": gpu, "vram_gb": vram,
        "transcribe_on": tname, "render_on": rname, "tier": tier,
        "recommended": {"whisper_model": model, "speed": speed, "device": "auto"},
        "summary": " · ".join(x for x in [
            _cpu_name(), f"{ram:.0f} GB RAM" if ram else "",
            f"{gpu}" + (f" {vram:.0f} GB" if vram else "") if gpu else "sin GPU dedicada"] if x),
    }
    return _PROFILE


def resolve_auto(opts: Options) -> Options:
    """Sustituye los valores "auto" por los recomendados para este equipo."""
    rec = system_profile()["recommended"]
    changes = {}
    if opts.whisper_model in ("auto", "", None):
        changes["whisper_model"] = rec["whisper_model"]
    if opts.speed in ("auto", "", None):
        changes["speed"] = rec["speed"]
    return replace(opts, **changes) if changes else opts


def use_gpu(opts: Options) -> bool:
    return opts.device != "cpu"


def video_encoder(opts: Options, intermediate: bool = False) -> list:
    """Argumentos de codificación H.264: GPU si se puede (mucho más rápido), si no x264 en el procesador."""
    hw = hw_info() if use_gpu(opts) else {}
    enc = hw.get("encoder")
    speed = opts.speed if opts.speed in ("rapido", "normal", "calidad") else "normal"
    if intermediate:   # paso intermedio: casi sin pérdida y muy rápido (siempre x264 para no perder calidad)
        return ["-c:v", "libx264", "-preset", "ultrafast", "-crf", "8", "-pix_fmt", "yuv420p"]
    if enc == "h264_nvenc":
        pre = {"rapido": "p4", "normal": "p6", "calidad": "p7"}[speed]
        return ["-c:v", "h264_nvenc", "-preset", pre, "-tune", "hq", "-rc", "vbr", "-cq", str(max(10, opts.crf - 1)),
                "-b:v", "0", "-maxrate", "20M", "-bufsize", "40M", "-profile:v", "high", "-pix_fmt", "yuv420p"]
    if enc == "h264_qsv":
        q = max(10, opts.crf)
        pre = {"rapido": "medium", "normal": "slower", "calidad": "veryslow"}[speed]
        return ["-c:v", "h264_qsv", "-preset", pre, "-global_quality", str(q), "-pix_fmt", hw.get("encoder_pix") or "nv12"]
    if enc == "h264_amf":
        q = max(10, opts.crf - 2)
        qual = {"rapido": "balanced", "normal": "quality", "calidad": "quality"}[speed]
        return ["-c:v", "h264_amf", "-quality", qual, "-rc", "cqp", "-qp_i", str(q), "-qp_p", str(q + 2),
                "-qp_b", str(q + 2), "-pix_fmt", hw.get("encoder_pix") or "nv12"]
    pre = {"rapido": "veryfast", "normal": opts.preset or "medium", "calidad": "slow"}[speed]
    return ["-c:v", "libx264", "-preset", pre, "-crf", str(opts.crf), "-profile:v", "high", "-pix_fmt", "yuv420p"]


def describe_device(opts: Options) -> str:
    hw = hw_info() if use_gpu(opts) else {}
    parts = []
    if use_gpu(opts) and hw.get("whisper_cuda"):
        parts.append("transcripción en GPU (CUDA)")
    elif use_gpu(opts) and whispercpp_exe():
        parts.append("transcripción en GPU (Vulkan)")
    else:
        parts.append("transcripción en CPU")
    parts.append(f"video con {hw['encoder_name']}" if hw.get("encoder") else "video con CPU (x264)")
    return " · ".join(parts)


# --------------------------------------------------------------------------- #
# 1. Descarga
# --------------------------------------------------------------------------- #
# --------------------------------------------------------------------------- #
# Cookies de YouTube: "Sign in to confirm you're not a bot"
# --------------------------------------------------------------------------- #
COOKIES_FILE = ROOT / "cookies.txt"          # exportado del navegador (formato Netscape); opcional


def _find_cookies_file() -> Optional[Path]:
    """cookies.txt en la carpeta; si no, el que deja la extensión (www.youtube.com_cookies.txt) aquí o en Descargas."""
    if COOKIES_FILE.is_file():
        return COOKIES_FILE
    found = []
    for d in (ROOT, Path.home() / "Downloads", Path.home() / "Descargas"):
        try:
            found += [p for p in d.glob("*cookies*.txt")
                      if p.is_file() and (d == ROOT or "youtube" in p.name.lower())]
        except OSError:
            pass
    return max(found, key=lambda p: p.stat().st_mtime) if found else None


COOKIE_BROWSERS = ("firefox", "edge", "chrome", "brave", "opera", "vivaldi")
YT_CLIENTS = ("tv", "web_safari", "mweb", "android_vr", "tv_simply")   # otras "puertas" de YouTube que a veces no piden iniciar sesión


def _is_bot_check(err: BaseException) -> bool:
    t = str(err).lower()
    return "confirm you" in t and "bot" in t or "sign in to confirm" in t or "--cookies-from-browser" in t


def _cookie_opts(method: Optional[str]) -> dict:
    """Opciones de yt-dlp para un método: 'file' (cookies.txt), un navegador, o None (sin cookies)."""
    if not method:
        return {}
    if method == "file":
        f = _find_cookies_file()
        if not f:
            return {}
        # yt-dlp reescribe el archivo al cerrar y borra lo que YouTube invalida: trabaja con una copia
        import tempfile
        tmp = Path(tempfile.gettempdir()) / "novoclip_cookies.txt"
        shutil.copyfile(f, tmp)
        return {"cookiefile": str(tmp)}
    if method.startswith("client:"):
        return {"extractor_args": {"youtube": {"player_client": [method.split(":", 1)[1]]}}}
    return {"cookiesfrombrowser": (method,)}


def _cookie_methods(opts: Options) -> list:
    """Orden de intentos: el que ya funcionó, el que eligió el usuario, sin cookies, cookies.txt y navegadores."""
    first = [opts.cookies_from_browser] if opts.cookies_from_browser else []
    remembered = load_config().get("yt_cookies")
    if remembered:
        first.insert(0, remembered)
    rest = ([None] + (["file"] if _find_cookies_file() else []) + ["client:" + c for c in YT_CLIENTS]
            + list(COOKIE_BROWSERS))
    out: list = []
    for m in first + rest:
        if m not in out:
            out.append(m)
    return out


def _cookie_opts_now(opts: Options) -> dict:
    """Para llamadas sueltas: usa solo el método que ya se sabe que funciona (o el elegido)."""
    m = opts.cookies_from_browser or load_config().get("yt_cookies")
    return _cookie_opts(m)


def yt_run(ydl_opts: dict, opts: Options, fn: Callable, progress: ProgressFn = _noop):
    """Ejecuta fn(ydl). Si YouTube pide confirmar que no eres un robot, repite el intento con tus cookies
    (cookies.txt o la sesión de Firefox/Edge/Chrome...) y recuerda el método que funcionó."""
    import yt_dlp
    methods = _cookie_methods(opts)
    first_err: Optional[BaseException] = None
    base = dict(ydl_opts)
    # YouTube exige un motor de JavaScript (Deno o Node) para resolver su desafío; sin él casi todo da "no eres un robot"
    rt = "deno" if shutil.which("deno") else "node" if shutil.which("node") else None
    if rt and "js_runtimes" not in base:
        base["js_runtimes"] = {rt: {}}
    base.setdefault("remote_components", ["ejs:github"])   # baja el resolutor del desafío si no viene instalado
    for k, m in enumerate(methods):
        o = dict(base, **_cookie_opts(m))
        try:
            with yt_dlp.YoutubeDL(o) as ydl:
                res = fn(ydl)
            if m and load_config().get("yt_cookies") != m:
                try:
                    save_config(yt_cookies=m)
                except Exception:
                    pass
            return res
        except Cancelled:
            raise
        except Exception as e:
            if first_err is None:
                first_err = e
            if not _is_bot_check(first_err):
                raise
            if k + 1 < len(methods):
                nm = methods[k + 1]
                if nm:
                    how = ("cookies.txt" if nm == "file" else f"otro modo de acceso ({nm[7:]})" if nm.startswith("client:")
                           else f"tu sesión de {nm}")
                    progress(2, f"YouTube pide verificar que no eres un robot; pruebo con {how}...")
    raise RuntimeError(
        "YouTube pide iniciar sesión para confirmar que no eres un robot y no se pudo usar ninguna sesión.\n"
        "Solución (elige una):\n"
        f"  1) LO MÁS SEGURO: exporta tus cookies con la extensión «Get cookies.txt LOCALLY» estando en youtube.com con tu sesión iniciada "
        f"y guarda el archivo como  {COOKIES_FILE.name}  dentro de la carpeta de NovoClip (Chrome/Edge en Windows no dejan leer sus cookies solos).\n"
        "  2) O descarga el video por otro medio y súbelo a NovoClip como archivo.\n"
        + ("" if rt else "  *) FALTA el motor de JavaScript que YouTube exige: instala Deno con  winget install DenoLand.Deno  y reinicia la app.\n")
        + "  3) Actualiza el descargador:  .venv\\Scripts\\pip install -U \"yt-dlp[default]\"") from first_err


def download(url: str, workdir: Path, opts: Options, progress: ProgressFn = _noop,
             audio_only: bool = False, section: Optional[tuple] = None, stem: str = "source",
             label: str = "Descargando video...") -> tuple[Path, str]:
    """Descarga de YouTube. Por defecto el video completo (<=1080p).
    audio_only: solo el audio (pesa muy poco). section=(inicio, fin): solo ese trozo del video, con corte exacto."""
    import yt_dlp

    workdir.mkdir(parents=True, exist_ok=True)

    def hook(d):
        check_cancel()
        if d.get("status") == "downloading":
            tot = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            if tot:
                progress(2 + 8 * d.get("downloaded_bytes", 0) / tot, label)

    ydl_opts = {
        "format": "bv*[height<=1080][ext=mp4]+ba[ext=m4a]/bv*[height<=1080]+ba/b[height<=1080]/b",
        "merge_output_format": "mp4",
        "format_sort": ["res", "fps", "br"],
        "outtmpl": str(workdir / f"{stem}.%(ext)s"),
        "quiet": True, "no_warnings": True, "noplaylist": True,
        "progress_hooks": [hook],
    }
    if opts.source_quality == "max" and not audio_only:
        # Mejor resolución disponible: al recortar en vertical se reduce en vez de ampliar (= sin perder nitidez).
        # Los trozos pesan poco, así que admiten 4K; el video completo se limita a 1440p por tamaño.
        h = 2160 if section else 1440
        ydl_opts["format"] = f"bv*[height<={h}]+ba[ext=m4a]/bv*[height<={h}]+ba/b[height<={h}]/b"
        ydl_opts["merge_output_format"] = "mkv"     # admite VP9/AV1 de YouTube (necesarios para 1440p y 4K)
    if audio_only:
        ydl_opts["format"] = "ba[ext=m4a]/ba/b[height<=480]/b"
        ydl_opts.pop("merge_output_format", None)
    if section:
        from yt_dlp.utils import download_range_func
        ydl_opts["download_ranges"] = download_range_func(None, [(float(section[0]), float(section[1]))])
        ydl_opts["force_keyframes_at_cuts"] = True     # corte exacto: el trozo empieza justo en `inicio`
        # al cortar exacto, yt-dlp vuelve a comprimir el trozo; sin esto usa la calidad por defecto (baja)
        ydl_opts["external_downloader_args"] = {"ffmpeg_o": ["-c:v", "libx264", "-preset", "veryfast", "-crf", "8",
                                                             "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "320k"]}
        ydl_opts["merge_output_format"] = "mkv"
    for old in workdir.glob(f"{stem}.*"):
        old.unlink(missing_ok=True)
    info = yt_run(ydl_opts, opts, lambda y: y.extract_info(url, download=True), progress)
    title = info.get("title") or "video"
    done = [p for p in workdir.glob(f"{stem}.*") if p.suffix not in (".part", ".ytdl") and ".f" not in p.stem]
    if not done:
        raise RuntimeError("La descarga no terminó. Revisa tu conexión o actualiza yt-dlp (pip install -U yt-dlp).")
    src = max(done, key=lambda p: p.stat().st_size)
    if audio_only or stem == "source":
        heatmap = []
        for point in info.get("heatmap") or []:
            try:
                heatmap.append({
                    "start_time": float(point["start_time"]),
                    "end_time": float(point["end_time"]),
                    "value": float(point["value"]),
                })
            except (KeyError, TypeError, ValueError):
                continue
        (workdir / "audience.json").write_text(
            json.dumps({"youtube_heatmap": heatmap}, ensure_ascii=False), encoding="utf-8"
        )
    return src, title


# --------------------------------------------------------------------------- #
# 2. Transcripción
# --------------------------------------------------------------------------- #
# --------------------------------------------------------------------------- #
# Transcripción con whisper.cpp + Vulkan (GPU AMD / Intel / NVIDIA sin CUDA)
# --------------------------------------------------------------------------- #
WHISPER_CPP_DIR = ROOT / "bin" / "whisper-vulkan"
GGML_MODELS = {"tiny": "ggml-tiny.bin", "base": "ggml-base.bin", "small": "ggml-small.bin",
               "medium": "ggml-medium.bin", "large-v3": "ggml-large-v3.bin",
               "large-v3-turbo": "ggml-large-v3-turbo.bin", "turbo": "ggml-large-v3-turbo.bin"}
GGML_URL = "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/{}"


def whispercpp_exe() -> Optional[str]:
    """whisper-cli compilado con Vulkan (lo crea compilar_whisper_vulkan.bat)."""
    env = os.environ.get("NOVOCLIP_WHISPER_CPP")
    if env and Path(env).is_file():
        return env
    for name in ("whisper-cli.exe", "whisper-cli"):
        p = WHISPER_CPP_DIR / name
        if p.is_file():
            return str(p)
    return None


def _ggml_model(size: str, progress: ProgressFn) -> Path:
    """Descarga (una vez) el modelo de whisper.cpp desde el repositorio oficial en Hugging Face."""
    import urllib.request
    fname = GGML_MODELS.get(size, "ggml-small.bin")
    dest = ROOT / "models" / fname
    if dest.exists() and dest.stat().st_size > 10_000_000:
        return dest
    dest.parent.mkdir(exist_ok=True)
    part = dest.with_suffix(".part")
    with urllib.request.urlopen(GGML_URL.format(fname), timeout=60) as r, part.open("wb") as f:
        total = int(r.headers.get("Content-Length") or 0)
        done = 0
        while True:
            check_cancel()
            chunk = r.read(1 << 20)
            if not chunk:
                break
            f.write(chunk)
            done += len(chunk)
            if total:
                progress(12, f"Descargando modelo {fname} ({done >> 20} / {total >> 20} MB)...")
    part.replace(dest)
    return dest


def _group_words(words: list) -> list:
    segs, cur = [], []
    for k, w in enumerate(words):
        cur.append(w)
        nxt = words[k + 1] if k + 1 < len(words) else None
        if (re.search(r"[.!?…]$", w["w"]) or nxt is None or nxt["s"] - w["e"] > 0.8 or len(cur) >= 30):
            segs.append({"s": cur[0]["s"], "e": cur[-1]["e"], "text": " ".join(x["w"] for x in cur), "words": cur})
            cur = []
    return segs


def transcribe_whispercpp(src: Path, workdir: Path, opts: Options, progress: ProgressFn) -> dict:
    exe = whispercpp_exe()
    if not exe:
        raise RuntimeError("whisper.cpp con Vulkan no está instalado (ejecuta compilar_whisper_vulkan.bat)")
    model = _ggml_model(opts.whisper_model, progress)
    wav = workdir / "audio16k.wav"
    progress(12, "Preparando audio para la GPU...")
    run(["ffmpeg", "-y", "-v", "error", "-i", str(src), "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", str(wav)])
    out_base = workdir / "whispercpp"
    threads = max(2, min(8, (os.cpu_count() or 4) // 2))
    cmd = [exe, "-m", str(model), "-f", str(wav), "-l", opts.language or "auto", "-oj", "-of", str(out_base),
           "-ml", "1", "-sow", "-pp", "-t", str(threads), "-bs", "1" if opts.speed == "rapido" else "5"]
    proc = _sp_popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True,
                     encoding="utf-8", errors="replace")
    tail: list = []
    gpu_line = ""
    try:
        for line in proc.stderr:
            line = line.rstrip()
            if not line:
                continue
            tail = (tail + [line])[-25:]
            low = line.lower()
            if "ggml_vulkan:" in low and ("=" in line or "found" in low) and not gpu_line:
                gpu_line = line.split(":", 1)[-1].strip()[:90]
            m = re.search(r"progress\s*=\s*(\d+)%", line)
            if m:
                pct = int(m.group(1))
                progress(12 + 28 * pct / 100, f"Transcribiendo con la GPU (Vulkan)... {pct}%")
        proc.wait()
    finally:
        _unregister(proc)
    check_cancel()
    if proc.returncode != 0:
        raise RuntimeError("whisper.cpp falló: " + " | ".join(tail[-4:])[:400])
    if not any("vulkan" in t.lower() for t in tail) and not gpu_line:
        progress(40, "Aviso: whisper.cpp no informó de una GPU Vulkan; puede que haya usado el procesador.")
    data = json.loads((workdir / "whispercpp.json").read_text(encoding="utf-8", errors="replace"))
    words = []
    for it in data.get("transcription", []):
        txt = (it.get("text") or "").strip()
        if not txt or re.fullmatch(r"\[.*\]|\(.*\)", txt) and "risa" not in txt.lower() and "laugh" not in txt.lower():
            continue
        s, e = it["offsets"]["from"] / 1000, it["offsets"]["to"] / 1000
        parts = txt.split()
        step = (e - s) / max(1, len(parts))
        for k, pw in enumerate(parts):
            words.append({"w": pw, "s": round(s + k * step, 3), "e": round(s + (k + 1) * step, 3)})
    wav.unlink(missing_ok=True)
    return {"language": (data.get("result") or {}).get("language") or opts.language or "es",
            "segments": _group_words(words), "engine": "whisper.cpp-vulkan"}


_WHISPER_CACHE: dict = {}


def transcribe(src: Path, workdir: Path, opts: Options, progress: ProgressFn = _noop) -> dict:
    cache = workdir / "transcript.json"
    if cache.exists():
        return json.loads(cache.read_text(encoding="utf-8"))

    from faster_whisper import WhisperModel

    hw = hw_info() if use_gpu(opts) else {"cpu_threads": os.cpu_count() or 4}
    want_gpu = use_gpu(opts) and hw.get("whisper_cuda")
    if opts.device == "gpu" and not want_gpu and not whispercpp_exe():
        progress(12, "No se encontró una GPU NVIDIA compatible para la transcripción: se usa el procesador.")

    def _run(device: str) -> dict:
        compute = "float16" if device == "cuda" else "int8"
        where = "GPU" if device == "cuda" else f"procesador ({hw.get('cpu_threads')} hilos)"
        progress(12, f"Cargando modelo Whisper '{opts.whisper_model}' en {where}...")
        key = (opts.whisper_model, device)
        if key not in _WHISPER_CACHE:          # el modelo se carga una vez y se reutiliza entre trozos
            _WHISPER_CACHE.clear()
            _WHISPER_CACHE[key] = WhisperModel(opts.whisper_model, device=device, compute_type=compute,
                                               cpu_threads=hw.get("cpu_threads") or 0)
        model = _WHISPER_CACHE[key]
        segs, info = model.transcribe(
            str(src), language=opts.language, word_timestamps=True, vad_filter=True,
            beam_size=5 if device == "cuda" or opts.speed != "rapido" else 1,
        )
        total = info.duration or 1
        res = {"language": info.language, "segments": []}
        for s in segs:
            words = [{"w": w.word.strip(), "s": round(w.start, 3), "e": round(w.end, 3)}
                     for w in (s.words or []) if w.word.strip()]
            res["segments"].append({"s": round(s.start, 3), "e": round(s.end, 3), "text": s.text.strip(), "words": words})
            progress(12 + 28 * min(1, s.end / total), f"Transcribiendo en {where}... {int(s.end)}s / {int(total)}s")
        return res

    vk = use_gpu(opts) and not want_gpu and whispercpp_exe()
    if vk:
        try:
            out = transcribe_whispercpp(src, workdir, opts, progress)
        except Cancelled:
            raise
        except Exception as e:
            progress(12, f"La GPU (Vulkan) falló ({str(e)[:120]}); sigo con el procesador...")
            out = _run("cpu")
    elif want_gpu:
        try:
            out = _run("cuda")
        except Exception as e:  # faltan DLLs de CUDA/cuDNN, poca memoria de video, etc.
            progress(12, f"La GPU falló ({str(e)[:90]}); sigo con el procesador...")
            out = _run("cpu")
    else:
        out = _run("cpu")
    cache.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    return out


# --------------------------------------------------------------------------- #
# 3. Selección de clips
# --------------------------------------------------------------------------- #
HOOK_WORDS = {
    # español
    "nunca", "siempre", "secreto", "error", "errores", "dinero", "increíble", "verdad", "nadie",
    "mejor", "peor", "cómo", "por qué", "imagina", "atención", "importante", "millones", "gratis",
    "problema", "cambió", "mentira", "truco", "clave", "jamás", "loco", "locura", "escucha", "mira",
    "historia", "real", "miedo", "éxito", "fracaso", "rico", "pobre", "brutal", "impresionante",
    "nadie", "todos", "única", "único", "peligro", "prohibido", "odio", "amo", "muerte", "matar",
    "dios", "wow", "qué", "neta", "literal", "obvio", "polémica", "polémico", "confesar", "confieso",
    # inglés
    "never", "always", "secret", "mistake", "money", "crazy", "truth", "nobody", "best", "worst",
    "how", "why", "imagine", "important", "million", "free", "problem", "changed", "lie", "insane",
    "trick", "key", "listen", "look", "story", "fear", "success", "fail", "rich", "broke", "wild",
}
# Arranques flojos: un clip no debería empezar con un conector que depende de lo anterior
FILLER_START = {"y", "e", "pero", "entonces", "bueno", "o", "sea", "eh", "em", "este", "pues", "osea",
                "ah", "mmm", "and", "so", "but", "um", "uh", "like", "well", "okay", "ok", "also",
                "también", "además", "porque", "eso", "esto", "ahí", "aja", "ajá", "sí", "no"}
CTA_MARKERS = ("suscríb", "suscrib", "dale like", "campanita", "patrocin", "link en la descripción",
               "enlace en la descripción", "bienvenidos", "bienvenidas", "bienvenido a", "nos vemos en el próximo",
               "subscribe", "sponsor", "link in the description", "welcome back", "hit the bell", "código de descuento")
LAUGH_RE = re.compile(r"\b(ja){2,}|\(risas?\)|\[risas?\]|\bjeje|\bhaha|\(laughs?\)|\[laughter\]", re.I)


def _norm(w: str) -> str:
    return re.sub(r"[^\w]", "", w.lower(), flags=re.U)


def sentence_lines(tr: dict) -> list[dict]:
    """Parte la transcripción en frases cortas (por puntuación o pausas) con tiempos por palabra.
    Así la IA y el algoritmo pueden cortar con mucha más precisión que con los segmentos de Whisper."""
    words = [w for s in tr["segments"] for w in s.get("words", [])]
    if not words:
        return [dict(s, words=[]) for s in tr["segments"]]
    lines, cur = [], []
    for k, w in enumerate(words):
        cur.append(w)
        nxt = words[k + 1] if k + 1 < len(words) else None
        end = (re.search(r"[.!?…]$", w["w"]) or nxt is None or (nxt["s"] - w["e"]) > 0.7
               or len(cur) >= 28 or (len(cur) >= 14 and w["w"].endswith(",")))
        if end:
            lines.append({"s": cur[0]["s"], "e": cur[-1]["e"], "text": " ".join(x["w"] for x in cur), "words": cur})
            cur = []
    return lines


def _loudness_curve(src: Path, hop: float = 0.5) -> np.ndarray:
    sr = 8000
    try:
        r = _sp_run(["ffmpeg", "-v", "error", "-i", str(src), "-ac", "1", "-ar", str(sr), "-f", "s16le", "-"],
                           capture_output=True)
        a = np.frombuffer(r.stdout, dtype=np.int16).astype(np.float32) / 32768.0
    except Exception:
        return np.zeros(1)
    n = int(sr * hop)
    if len(a) < n:
        return np.zeros(1)
    a = a[: len(a) // n * n].reshape(-1, n)
    return 20 * np.log10(np.sqrt((a ** 2).mean(axis=1)) + 1e-6)


def _line_energy(lines: list, loud: np.ndarray, hop: float = 0.5) -> list[float]:
    """Energía de cada frase (z-score del volumen respecto al resto del video)."""
    if len(loud) < 2:
        return [0.0] * len(lines)
    voiced = loud[loud > -60]
    mu, sd = (float(np.mean(voiced)), float(np.std(voiced)) + 1e-6) if len(voiced) else (0.0, 1.0)
    out = []
    for ln in lines:
        a, b = int(ln["s"] / hop), max(int(ln["e"] / hop), int(ln["s"] / hop) + 1)
        w = loud[a:b] if a < len(loud) else loud[-1:]
        out.append((float(np.max(w)) * 0.5 + float(np.mean(w)) * 0.5 - mu) / sd)
    return out


def _line_features(lines: list, energy: list) -> list[dict]:
    feats = []
    for ln, en in zip(lines, energy):
        low = ln["text"].lower()
        toks = [_norm(w) for w in ln["text"].split()]
        n = len(toks) or 1
        feats.append({
            "hook": sum(1 for w in HOOK_WORDS if re.search(rf"\b{re.escape(w)}\b", low))
                    + (2 if "?" in low else 0) + (1 if re.search(r"\d", low) else 0),
            "kw": sum(1 for t in toks if t in HOOK_WORDS),
            "punct": low.count("?") + low.count("!"),
            "nums": len(re.findall(r"\d+", low)),
            "laugh": 1 if LAUGH_RE.search(low) else 0,
            "cta": 1 if any(c in low for c in CTA_MARKERS) else 0,
            "weak_start": 1 if toks and toks[0] in FILLER_START else 0,
            "complete": 1 if re.search(r"[.!?…]$", ln["text"].strip()) else 0,
            "words": n, "energy": en,
        })
    return feats


def _window_score(lines, feats, i, j, rate_mu, target) -> tuple[float, str]:
    F = feats[i : j + 1]
    dur = max(lines[j]["e"] - lines[i]["s"], 1)
    first = feats[i]
    first2 = feats[i : min(j + 1, i + 2)]
    rate = sum(f["words"] for f in F) / dur
    energy_peak = max(f["energy"] for f in F)
    energy_mean = sum(f["energy"] for f in F) / len(F)
    opening_energy = max(f["energy"] for f in first2)
    reasons = []
    score = (
        12 * min(sum(f["hook"] for f in first2), 3)                  # gancho en los primeros segundos
        + 4 * max(-1, min(2, opening_energy))                          # arranca con fuerza
        + 2.5 * min(sum(f["kw"] for f in F), 10)
        + 2.5 * min(sum(f["punct"] for f in F), 6)
        + 1.5 * min(sum(f["nums"] for f in F), 4)
        + 8 * min(sum(f["laugh"] for f in F), 2)                       # risas = momento emocional
        + 7 * max(-1, min(2, energy_mean)) + 5 * max(0, min(3, energy_peak))
        + 7 * max(-1, min(1.5, (rate - rate_mu) / (rate_mu * 0.25 + 1e-6)))
        + 10 * feats[j]["complete"]                                    # termina en idea completa
        - 14 * first["weak_start"]                                     # empieza con "y/pero/entonces..."
        - 30 * min(sum(f["cta"] for f in F), 1)                        # intros, patrocinios, "suscríbete"
        + 6 * (1 - min(1, abs(dur - target) / target))                 # duración cómoda
    )
    if sum(f["hook"] for f in first2):
        reasons.append("arranca con gancho")
    if opening_energy > 0.8:
        reasons.append("empieza con energía")
    if energy_peak > 1.5:
        reasons.append("pico emocional")
    if sum(f["laugh"] for f in F):
        reasons.append("momento gracioso")
    if sum(f["punct"] for f in F) >= 2:
        reasons.append("preguntas/exclamaciones")
    if rate > rate_mu * 1.1:
        reasons.append("ritmo rápido")
    if feats[j]["complete"]:
        reasons.append("idea completa")
    return score, ", ".join(reasons) or "segmento coherente"


HOOK_TAIL = {"de", "que", "y", "o", "a", "en", "con", "por", "para", "la", "el", "los", "las", "un", "una", "del", "al",
             "se", "me", "te", "lo", "su", "mi", "pero", "como", "si", "and", "the", "to", "of", "in", "is", "but"}


def _best_hook(lines: list, feats: list, i: int, j: int, max_words: int = 7) -> str:
    """Frase corta con sentido para el gancho: la línea con más fuerza (pregunta, número, palabra clave, risa)
    de los primeros ~25 s del clip, sin conectores al inicio ni al final, cortada en un límite natural."""
    t0, best, best_sc = lines[i]["s"], None, -1e9
    for k in range(i, j + 1):
        if lines[k]["s"] - t0 > 25:
            break
        f = feats[k]
        sc = 6 * f["hook"] + 3 * f["kw"] + 3 * f["punct"] + 2 * f["nums"] + 3 * f["laugh"] + 4 * f["complete"] \
            - 8 * f["weak_start"] - 1.5 * (k - i) - 30 * f["cta"]
        if sc > best_sc:
            best, best_sc = k, sc
    words = lines[best]["text"].split() if best is not None else lines[i]["text"].split()
    while len(words) > 1 and _norm(words[0]) in FILLER_START:        # "pues, entonces..." al inicio
        words = words[1:]
    q = [k for k, w in enumerate(words[:max_words]) if w.endswith(("?", "!"))]   # corta en la primera pregunta/exclamación
    words = words[: q[0] + 1] if q else words[:max_words]
    while len(words) > 1 and _norm(words[-1]) in HOOK_TAIL:           # no terminar en "de", "que", "y"...
        words = words[:-1]
    text = " ".join(words).strip(" ,;:.-")
    for opening, closing in (("¿", "?"), ("¡", "!")):                 # sin signos de apertura huérfanos
        if opening in text and closing not in text:
            text = text.replace(opening, "")
    return text


def _overlaps(a, b, gap=1.0) -> bool:
    return not (a[1] + gap <= b[0] or b[1] + gap <= a[0])


def _trim_start(line: dict) -> float:
    """Empieza en la primera palabra con contenido (salta 'eh', 'bueno', 'y'... al inicio)."""
    ws = line.get("words") or []
    k = 0
    while k < min(2, len(ws) - 1) and _norm(ws[k]["w"]) in FILLER_START:
        k += 1
    return ws[k]["s"] if ws else line["s"]


def _auto_keywords(text: str, n: int = 6) -> list[str]:
    out = []
    for w in text.split():
        t = _norm(w)
        if t and (t in HOOK_WORDS or re.fullmatch(r"\d+", t)) and t not in out:
            out.append(t)
    return out[:n]


def _attach_replay_signals(tr: dict, workdir: Path, captions: Optional[dict] = None) -> None:
    """Attach YouTube replay intervals when yt-dlp supplied a usable heatmap."""
    heatmap = (captions or {}).get("heatmap") or []
    if not heatmap:
        path = workdir / "audience.json"
        try:
            heatmap = json.loads(path.read_text(encoding="utf-8")).get("youtube_heatmap") or []
        except (OSError, ValueError, AttributeError):
            heatmap = []
    intervals = replay_intervals(heatmap)
    if intervals:
        tr["replay"] = intervals


def select_heuristic(src: Path, tr: dict, opts: Options) -> list[Clip]:
    lines = sentence_lines(tr)
    if not lines:
        return []
    energy = _line_energy(lines, _loudness_curve(src)) if src else [0.0] * len(lines)
    feats = _line_features(lines, energy)
    rate_mu = sum(f["words"] for f in feats) / max(1, sum(l["e"] - l["s"] for l in lines))
    target = (opts.min_len + opts.max_len) / 2

    scored = []
    for i in range(len(lines)):
        if feats[i]["cta"]:
            continue
        for j in range(i, len(lines)):
            d = lines[j]["e"] - lines[i]["s"]
            if d > opts.max_len:
                break
            if d >= opts.min_len:
                sc, why = _window_score(lines, feats, i, j, rate_mu, target)
                audience, audience_reasons = audience_bonus(
                    lines[i]["s"], lines[j]["e"], tr.get("hot") or [], tr.get("replay") or []
                )
                sc += audience
                if audience_reasons:
                    why = ", ".join(([why] if why else []) + audience_reasons)
                scored.append((sc, i, j, why))
    if not scored:  # video corto: usar todo
        scored = [(0.0, 0, len(lines) - 1, "video completo")]
    scored.sort(key=lambda x: -x[0])

    picked: list = []
    for sc, i, j, why in scored:
        rng = (lines[i]["s"], lines[j]["e"])
        if any(_overlaps(rng, (p[1], p[2]), gap=2.0) for p in picked):
            continue
        picked.append((sc, *rng, i, j, why))
        if len(picked) >= opts.num_clips:
            break

    clips = []
    for k, (sc, s, e, i, j, why) in enumerate(sorted(picked, key=lambda p: -p[0])):
        hook = _best_hook(lines, feats, i, j) or " ".join(lines[i]["text"].split()[:6])
        title = hook[:1].upper() + hook[1:]
        text = " ".join(l["text"] for l in lines[i : j + 1])
        norm = max(0, min(100, 25 + 0.9 * sc))    # nota absoluta: un video flojo da notas bajas, uno muy bueno notas altas
        clips.append(Clip(index=k + 1, start=max(0, _trim_start(lines[i]) - 0.1), end=e + 0.35, title=title,
                          hook=hook.upper(), score=round(norm),
                          reason=why, caption=title, hashtags=["#shorts", "#viral", "#fyp"],
                          keywords=_auto_keywords(text)))
    return clips


# --------------------------------------------------------------------------- #
# Conexión con Claude: API (ANTHROPIC_API_KEY) o Claude Code con tu suscripción
# --------------------------------------------------------------------------- #
def _claude_cli() -> Optional[str]:
    """Ruta del comando `claude` (Claude Code), si está instalado."""
    exe = os.environ.get("NOVOCLIP_CLAUDE_CLI") or shutil.which("claude")
    if not exe:
        for cand in (Path.home() / ".local" / "bin" / "claude.exe", Path.home() / ".local" / "bin" / "claude",
                     Path(os.environ.get("APPDATA", "")) / "npm" / "claude.cmd"):
            if cand.is_file():
                return str(cand)
    return exe


CONFIG_PATH = ROOT / "config.json"
GEMINI_DEFAULT_MODEL = "gemini-4-hydrogen"   # Gemini 4 rápido y barato (según la lista de modelos de aistudio.google.com/docs/models)
# Orden de preferencia para este programa (elegir momentos y mirar imágenes con salida JSON): rápidos y baratos primero.
GEMINI_PREFERRED = ("gemini-4-hydrogen", "gemini-4-argon", "gemini-3.8-flash", "gemini-3.5-flash-lite", "gemini-3.6-flash",
                    "gemini-3.1-flash-lite", "gemini-3-flash-preview", "gemini-3.1-pro-preview")
GEMINI_SKIP = ("embedding", "image", "tts", "audio", "live", "robotics", "computer-use", "aqa", "thinking-exp",
               "omni", "transcribe", "translate", "banana", "veo", "imagen")


def gemini_rank(name: str):
    """Orden para elegir modelo: los preferidos primero; después Flash, Flash-Lite y Pro; Carbon (el más caro) al final."""
    if name in GEMINI_PREFERRED:
        return (0, GEMINI_PREFERRED.index(name), name)
    n = name.lower()
    tier = 1 if ("flash" in n and "lite" not in n) else 2 if "lite" in n else 4 if "carbon" in n else 3
    return (tier, 0 if "latest" in n else 1, name)
_AI_PROVIDER = "auto"     # IA elegida para este trabajo ("auto" = la de Ajustes); ver AI_SOURCES
AI_SOURCES = ("auto", "cli", "claude_api", "gemini", "incluida")


def norm_provider(p) -> str:
    """Valida la IA elegida (los valores antiguos 'claude' pasan a 'auto')."""
    return p if p in AI_SOURCES else "auto"


def load_config() -> dict:
    try:
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_config(**changes) -> dict:
    cfg = load_config()
    for k, v in changes.items():
        if v is None or v == "":
            cfg.pop(k, None)
        else:
            cfg[k] = v
    CONFIG_PATH.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    return cfg


def gemini_key() -> Optional[str]:
    """Clave de Gemini: variable de entorno GEMINI_API_KEY / GOOGLE_API_KEY o la guardada desde la app."""
    return (os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
            or load_config().get("gemini_key") or None)


def gemini_model() -> str:
    return os.environ.get("NOVOCLIP_GEMINI_MODEL") or load_config().get("gemini_model") or GEMINI_DEFAULT_MODEL


# --------------------------------------------------------------------------- #
# IA incluida (servicio de NovoClip) o IA propia (clave del usuario)
# --------------------------------------------------------------------------- #
INCLUDED_FILE = ROOT / "ia_incluida.json"   # lo prepara el dueño de la app antes de repartirla


def _included_cfg() -> dict:
    try:
        return json.loads(INCLUDED_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def included_source() -> Optional[str]:
    """'proxy' (servidor de NovoClip con licencia), 'key' (clave de Gemini incluida, provisional) o None."""
    inc = _included_cfg()
    if (os.environ.get("NOVOCLIP_PROXY_URL") or inc.get("proxy_url")):
        return "proxy"
    if os.environ.get("NOVOCLIP_INCLUDED_GEMINI_KEY") or inc.get("gemini_key"):
        return "key"
    if dev_mode() and os.environ.get("NOVOCLIP_NO_CLI") != "1" and _claude_cli():
        return "claude"      # modo dueño: la "IA incluida" es tu propia suscripción de Claude (Claude Code)
    return None


def ai_mode() -> str:
    m = os.environ.get("NOVOCLIP_AI_MODE") or load_config().get("ai_mode")
    if m in ("incluida", "propia"):
        return m
    return "incluida" if included_source() else "propia"


def license_key() -> Optional[str]:
    return load_config().get("license_key") or os.environ.get("NOVOCLIP_LICENSE") or None


def _proxy_url() -> str:
    return (os.environ.get("NOVOCLIP_PROXY_URL") or _included_cfg().get("proxy_url") or "").rstrip("/")


def _ask_proxy(prompt: str, schema, images: Optional[list] = None):
    """Pide la respuesta al servidor de NovoClip (IA incluida en la suscripción)."""
    import base64
    import urllib.error
    import urllib.request
    lic = license_key()
    if not lic:
        raise RuntimeError("Falta tu clave de licencia de NovoClip (pégala en la app, en 'IA incluida').")
    body = json.dumps({"license": lic, "prompt": prompt, "schema": schema.model_json_schema(),
                       "images": [{"label": l, "data": base64.b64encode(d).decode()} for l, d in (images or [])]})
    req = urllib.request.Request(_proxy_url() + "/v1/ai", data=body.encode(), method="POST",
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            data = json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        msg = e.read().decode(errors="replace")[:300]
        if e.code == 401:
            raise RuntimeError("Tu licencia de NovoClip no es válida o está vencida.") from e
        if e.code == 429:
            raise RuntimeError("Llegaste al límite de uso de IA de tu plan por hoy. Vuelve mañana o usa tu propia clave.") from e
        raise RuntimeError(f"El servidor de IA respondió {e.code}: {msg}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"No se pudo conectar con el servidor de IA de NovoClip ({e.reason}).") from e
    return schema.model_validate_json(_extract_json(data.get("text") or ""))


def included_status() -> dict:
    """Estado de la IA incluida para mostrarlo en la app."""
    src = included_source()
    if src == "key":
        return {"ok": True, "source": "key", "text": "IA incluida activa (Gemini)."}
    if src == "claude":
        return {"ok": True, "source": "claude", "text": "IA incluida activa: tu suscripción de Claude (Claude Code, modo dueño)."}
    if src != "proxy":
        return {"ok": False, "source": None, "text": "Esta copia de la app no trae IA incluida. Usa tu propia clave."}
    lic = license_key()
    if not lic:
        return {"ok": False, "source": "proxy", "text": "Pega tu clave de licencia para activar la IA incluida."}
    import urllib.request
    try:
        with urllib.request.urlopen(_proxy_url() + "/v1/license/" + urllib.request.quote(lic), timeout=15) as r:
            d = json.loads(r.read().decode())
        if not d.get("active"):
            return {"ok": False, "source": "proxy", "text": "Licencia no válida o vencida."}
        return {"ok": True, "source": "proxy", "text": f"Licencia activa ({d.get('plan', 'plan')}). "
                f"Te quedan {d.get('remaining', '?')} usos de IA hoy."}
    except Exception as e:
        return {"ok": False, "source": "proxy", "text": f"No se pudo comprobar la licencia ({str(e)[:80]})."}


def anthropic_key() -> Optional[str]:
    return os.environ.get("ANTHROPIC_API_KEY") or load_config().get("anthropic_key") or None


def dev_mode() -> bool:
    """Modo desarrollador (solo el dueño): permite usar Claude Code con su suscripción personal."""
    return os.environ.get("NOVOCLIP_DEV") == "1" or bool(load_config().get("dev_mode"))


def claude_backend() -> Optional[str]:
    if anthropic_key():
        return "api"
    if dev_mode() and os.environ.get("NOVOCLIP_NO_CLI") != "1" and _claude_cli():
        return "cli"
    return None


def ai_source() -> str:
    """Qué IA quiere el usuario: auto | cli (su suscripción de Claude) | claude_api | gemini | incluida.
    Manda lo elegido para el trabajo; si no, lo guardado en Ajustes."""
    if _AI_PROVIDER != "auto":
        return _AI_PROVIDER
    s = os.environ.get("NOVOCLIP_AI_SOURCE") or load_config().get("ai_source")
    if s in AI_SOURCES:
        return s
    return "incluida" if ai_mode() == "incluida" else "auto"


def cli_available() -> bool:
    return os.environ.get("NOVOCLIP_NO_CLI") != "1" and bool(_claude_cli())


def ai_backend() -> Optional[str]:
    """Qué IA se usa: 'cli' (tu suscripción, Claude Code), 'api' (clave de Claude), 'gemini', 'proxy'/'gemini_inc'
    (IA incluida) o None. Lo que el usuario elige se respeta; con "auto" se prefiere Claude y, si no, Gemini."""
    src = ai_source()
    if src == "incluida":
        return {"proxy": "proxy", "key": "gemini_inc", "claude": "cli"}.get(included_source() or "")
    if src == "cli":
        return "cli" if cli_available() else None
    if src == "claude_api":
        return "api" if anthropic_key() else None
    if src == "gemini":
        return "gemini" if gemini_key() else None
    return claude_backend() or ("gemini" if gemini_key() else None)


def ai_sources_status() -> dict:
    """Disponibilidad de cada opción para los botones de Ajustes."""
    inc = included_status()
    return {"auto": {"ok": bool(claude_backend() or gemini_key()), "text": "La app elige: Claude si hay, y si no Gemini."},
            "cli": {"ok": cli_available(), "text": "Usa tu suscripción de Claude por Claude Code." if cli_available()
                    else "Claude Code no está instalado o no se encuentra en este equipo."},
            "claude_api": {"ok": bool(anthropic_key()), "text": "Clave de la API de Claude guardada." if anthropic_key() else "Falta la clave de la API de Claude."},
            "gemini": {"ok": bool(gemini_key()), "text": "Clave de Gemini guardada." if gemini_key() else "Falta la clave de Gemini."},
            "incluida": {"ok": bool(inc.get("ok")), "text": inc.get("text", "")}}


def backend_name(b: Optional[str]) -> str:
    return {"cli": "Claude Code", "api": "la API de Claude", "gemini": f"Gemini · {gemini_model()}",
            "gemini_inc": "IA incluida · Gemini", "proxy": "IA incluida de NovoClip"}.get(b or "", "ninguna")


_AI_NOTIFY: Callable[[float, str], None] = _noop     # lo fija select_clips: así los avisos de la IA llegan a la pantalla de progreso
_AI_NOTIFY_PCT = 42.0


def _ai_note(msg: str) -> None:
    print(f"  [IA] {msg}")
    try:
        _AI_NOTIFY(_AI_NOTIFY_PCT, msg)
    except Exception:   # noqa: BLE001
        pass


GEMINI_TIMEOUT_S = 100   # sin límite, una llamada colgada dejaba el progreso parado para siempre


def _ask_gemini(prompt: str, schema, images: Optional[list] = None, key: Optional[str] = None,
                model: Optional[str] = None, videos: Optional[list] = None):
    """Respuesta estructurada de Gemini (SDK google-genai) con la forma de `schema`."""
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        raise RuntimeError("Falta la librería de Gemini: ejecuta  .venv\\Scripts\\pip install google-genai")
    client = genai.Client(api_key=key or gemini_key(), http_options=types.HttpOptions(timeout=GEMINI_TIMEOUT_S * 1000))
    contents: list = [prompt]
    for label, data in images or []:
        contents += [label, types.Part.from_bytes(data=data, mime_type="image/jpeg")]
    for label, data in videos or []:       # video con audio (Gemini lo analiza fotograma a fotograma y escucha la pista)
        contents += [label, types.Part.from_bytes(data=data, mime_type="video/mp4")]
    cfg = types.GenerateContentConfig(response_mime_type="application/json", response_schema=schema)
    models, last = [], None
    for m in (model or gemini_model(), GEMINI_DEFAULT_MODEL):
        if m not in models:
            models.append(m)
    quota_hit, discovered, queue, tried = False, False, list(models), []

    def discover() -> list:
        """Google retira modelos con el tiempo (404 "no longer available"): se le pregunta qué modelos tiene hoy esta clave."""
        try:
            names = []
            for mm in client.models.list():
                acts = getattr(mm, "supported_actions", None) or []
                nm = (getattr(mm, "name", "") or "").replace("models/", "")
                if "generateContent" in acts and nm.startswith("gemini") and not any(x in nm for x in GEMINI_SKIP):
                    names.append(nm)
            return sorted(names, key=gemini_rank)[:5]
        except Exception:   # noqa: BLE001
            return []

    while queue:
        m = queue.pop(0)
        tried.append(m)
        check_cancel()
        _ai_note(f"Gemini: consultando {m} (máx. {GEMINI_TIMEOUT_S} s)...")
        try:
            resp = client.models.generate_content(model=m, contents=contents, config=cfg)
        except Exception as e:
            last = e
            msg = str(e).lower()
            short = str(e).replace("\n", " ")[:110]
            if "not found" in msg or "404" in msg or "not supported" in msg:
                _ai_note(f"Gemini: el modelo {m} ya no está disponible para tu clave; pruebo otro...")
                if not discovered:
                    discovered = True
                    _ai_note("Gemini: consulto a Google qué modelos tiene disponibles tu clave hoy...")
                    queue += [x for x in discover() if x not in tried and x not in queue]
                continue          # ese nombre de modelo no existe en esta cuenta: probar el siguiente
            if "api key" in msg or "api_key" in msg or "401" in msg or "403" in msg or "permission" in msg:
                raise RuntimeError("La clave de Gemini no es válida. Crea una en https://aistudio.google.com/apikey "
                                   "y pégala en la app.") from e
            if "429" in msg or "quota" in msg or "resource_exhausted" in msg:
                quota_hit = True
                _ai_note(f"Gemini: {m} sin cupo ahora ({short}); pruebo otro modelo...")
                continue
            if any(x in msg for x in ("timeout", "timed out", "deadline", "503", "500", "overloaded", "unavailable", "connection")):
                _ai_note(f"Gemini: {m} tardó demasiado o está saturado; pruebo otro modelo...")
                continue
            raise
        if key is None and m != (model or gemini_model()):      # este modelo sí funciona: se recuerda para la próxima vez
            try:
                save_config(gemini_model=m)
                _ai_note(f"Gemini: uso {m} (queda guardado como tu modelo).")
            except Exception:   # noqa: BLE001
                pass
        parsed = getattr(resp, "parsed", None)
        if isinstance(parsed, schema):
            return parsed
        text = getattr(resp, "text", None) or ""
        if not text:
            raise RuntimeError("Gemini no devolvió respuesta (posible filtro de contenido).")
        return schema.model_validate_json(_extract_json(text))
    if quota_hit:
        raise RuntimeError("Gemini: se agotó la cuota gratuita por ahora en todos los modelos probados. Espera un rato, "
                           "elige otro modelo en Ajustes o usa Claude.")
    raise RuntimeError(f"Gemini: ningún modelo respondió ({', '.join(tried)}): {str(last)[:200]}")


def _extract_json(text: str) -> str:
    m = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.S)
    if m:
        return m.group(1)
    a, b = text.find("{"), text.rfind("}")
    if a == -1 or b <= a:
        raise RuntimeError("Claude no devolvió JSON")
    return text[a : b + 1]


# Reparto de la carga entre modelos: Opus manda y verifica, Sonnet hace lo técnico, Haiku escribe los textos.
# Se pueden cambiar con NOVOCLIP_MODEL_TECH / _COPY / _VERIFY. Sin rol se usa el modelo de siempre.
_ROLE_MODELS = {"tech": ("sonnet", "claude-sonnet-5-5"), "copy": ("haiku", "claude-haiku-5-5"),
                "verify": ("opus", "claude-opus-5-5")}
_MODEL_ERR = re.compile(r"model|limit|quota|overload|capacity", re.I)


def _role_models(role: Optional[str], backend: str, opts: Options) -> list:
    """Modelos a probar para un rol, en orden; el último es el modelo de respaldo (el de siempre)."""
    default = (os.environ.get("NOVOCLIP_CLAUDE_MODEL") or "sonnet") if backend == "cli" else opts.ai_model
    if role not in _ROLE_MODELS:
        return [default]
    want = os.environ.get(f"NOVOCLIP_MODEL_{role.upper()}") or _ROLE_MODELS[role][0 if backend == "cli" else 1]
    return [want] if want == default else [want, default]


def ask_claude(prompt: str, schema, opts: Options, images: Optional[list] = None, videos: Optional[list] = None,
               role: Optional[str] = None):
    """Pide a Claude una respuesta con la forma de `schema` (modelo pydantic).
    role: "tech" (Sonnet) | "copy" (Haiku) | "verify" (Opus). Con Gemini el rol se ignora.

    images: lista de (etiqueta, bytes_jpeg). Con la API van en el mensaje; con Claude Code
    se guardan en una carpeta temporal y Claude las abre con su herramienta de lectura.
    """
    backend = ai_backend()
    if backend == "gemini":
        return _ask_gemini(prompt, schema, images, videos=videos)
    if backend == "gemini_inc":
        inc = _included_cfg()
        return _ask_gemini(prompt, schema, images, key=os.environ.get("NOVOCLIP_INCLUDED_GEMINI_KEY") or inc.get("gemini_key"),
                           model=inc.get("gemini_model"), videos=videos)
    if backend == "proxy":
        return _ask_proxy(prompt, schema, images)
    if backend == "api":
        import anthropic

        content: list = [{"type": "text", "text": prompt}]
        if images:
            import base64
            for label, data in images:
                content.append({"type": "text", "text": label})
                content.append({"type": "image", "source": {"type": "base64", "media_type": "image/jpeg",
                                                            "data": base64.b64encode(data).decode()}})
        client = anthropic.Anthropic(api_key=anthropic_key())
        models = _role_models(role, "api", opts)
        for k, m in enumerate(models):
            kw = {} if role == "copy" else {"output_config": {"effort": os.environ.get("NOVOCLIP_CLAUDE_EFFORT") or "high"}}
            try:
                resp = client.messages.parse(model=m, max_tokens=16000, messages=[{"role": "user", "content": content}],
                                             output_format=schema, **kw)
                break
            except anthropic.NotFoundError:        # el modelo del rol no existe: se usa el de siempre
                if k + 1 >= len(models):
                    raise
        if resp.stop_reason == "refusal" or resp.parsed_output is None:
            raise RuntimeError("la IA no devolvió respuesta")
        return resp.parsed_output

    if backend != "cli":
        raise RuntimeError("no hay API key ni Claude Code instalado")

    import tempfile
    exe = _claude_cli()
    with tempfile.TemporaryDirectory(prefix="novoclip_") as tmp:
        full = prompt
        if images:
            names = []
            for k, (label, data) in enumerate(images):
                p = Path(tmp) / f"frame_{k:02d}.jpg"
                p.write_bytes(data)
                names.append(f"- {p.name}: {label}")
            full += ("\n\nLos fotogramas están en la carpeta actual. Ábrelos TODOS con la herramienta Read "
                     "antes de responder:\n" + "\n".join(names))
        full += ("\n\nResponde ÚNICAMENTE con un objeto JSON válido (sin texto antes ni después) "
                 "que cumpla este JSON Schema:\n" + json.dumps(schema.model_json_schema(), ensure_ascii=False))

        cmd = [exe, "-p", "--output-format", "json"]
        if images:
            cmd += ["--allowedTools", "Read"]
        else:
            cmd += ["--disallowedTools", "Bash", "Edit", "Write", "WebFetch", "WebSearch", "Read", "Glob", "Grep"]
        # Sin rol: NOVOCLIP_CLAUDE_MODEL o Sonnet. Con rol: el modelo del rol y, si falla por modelo/límite, el de siempre.
        env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}

        last_err = ""
        for model in _role_models(role, "cli", opts):
            mcmd = cmd + ["--model", model]
            if role != "copy":      # --effort con Haiku no está comprobado: se omite para ese rol
                mcmd += ["--effort", os.environ.get("NOVOCLIP_CLAUDE_EFFORT") or "high"]
            for _ in range(2):
                r = _sp_run(mcmd, input=full, capture_output=True, text=True, encoding="utf-8",
                            errors="replace", cwd=tmp, env=env, timeout=900)
                out = r.stdout.strip()
                try:
                    data = json.loads(out)
                    if data.get("is_error"):
                        msg = str(data.get("result") or data.get("subtype"))[:300]
                        if role and _MODEL_ERR.search(msg):
                            last_err = msg
                            break           # siguiente modelo
                        raise RuntimeError(msg)
                    text = data.get("result") or ""
                except json.JSONDecodeError:
                    text = out
                if r.returncode != 0 and not text:
                    last_err = (r.stderr or out)[-300:]
                    if "login" in last_err.lower() or "auth" in last_err.lower():
                        raise RuntimeError("Claude Code no tiene sesión iniciada: abre una terminal, escribe "
                                           "`claude` y entra con tu cuenta.")
                    if role and _MODEL_ERR.search(last_err):
                        break               # siguiente modelo
                    continue
                try:
                    return schema.model_validate_json(_extract_json(text))
                except Exception as e:
                    last_err = f"respuesta no válida: {str(e)[:200]}"
        raise RuntimeError(f"Claude Code falló: {last_err}")


def select_ai(tr: dict, opts: Options, video_title: str = "", src: Optional[Path] = None) -> list[Clip]:
    """Usa Claude como editor: elige los momentos con más potencial viral con criterio de retención."""
    from pydantic import BaseModel, Field

    class AIClip(BaseModel):
        start_line: int = Field(description="índice de la primera frase del clip (la del gancho)")
        end_line: int = Field(description="índice de la última frase del clip (incluida), donde está el remate")
        title: str = Field(description="título para la publicación, máx 60 caracteres")
        hook: str = Field(description="texto en pantalla los primeros 3 s, máx 7 palabras, que genere curiosidad")
        opening_words: str = Field(description="las primeras 4-6 palabras que se DICEN en el clip, copiadas "
                                               "literalmente de la transcripción (sirve para verificar el corte)")
        gancho: int = Field(description="0-10: ¿los primeros 3 segundos detienen el scroll?")
        emocion: int = Field(description="0-10: humor, sorpresa, polémica, tensión, inspiración")
        valor: int = Field(description="0-10: dato útil, historia o idea que vale la pena compartir")
        autonomia: int = Field(description="0-10: se entiende sin contexto previo")
        remate: int = Field(description="0-10: termina con un cierre, punchline o frase memorable")
        virality_score: int = Field(description="0-100, nota global")
        reason: str = Field(description="por qué funcionará en redes, una frase")
        caption: str = Field(description="descripción para TikTok/Reels/Shorts con una pregunta que invite a comentar")
        hashtags: list[str] = Field(description="3-6 hashtags relevantes")
        keywords: list[str] = Field(description="3-8 palabras EXACTAS dichas en el clip que conviene resaltar "
                                                "(cifras, palabras fuertes, nombres)")

    class AIResult(BaseModel):
        clips: list[AIClip]

    lines = sentence_lines(tr)
    energy = _line_energy(lines, _loudness_curve(src)) if src else [0.0] * len(lines)
    hot = tr.get("hot") or []
    replay = tr.get("replay") or []

    def tag(e, l=None):
        fire = " 🔥" if l is not None and any(a <= l["e"] and l["s"] <= b for a, b in hot) else ""
        repeat = " ↻" if l is not None and any(a <= l["e"] and l["s"] <= b for a, b in replay) else ""
        return (" ⚡" if e > 1.2 else "") + fire + repeat
    listing = "\n".join(f"{k} [{l['s']:.1f}-{l['e']:.1f}]{tag(e, l)} {l['text']}"
                        for k, (l, e) in enumerate(zip(lines, energy)))
    if hot:
        listing += "\n(🔥 = en ese momento el chat del directo se disparó: suele ser un momento que gustó al público)"
    if replay:
        listing += "\n(↻ = este tramo aparece entre los más repetidos por la audiencia en YouTube)"
    want = opts.num_clips
    ask_n = min(max(want * 2, want + 3), 24)    # se piden más candidatos y se queda con los mejores: elegir entre más da mejores clips
    prompt = f"""Eres el mejor editor de clips virales de TikTok, YouTube Shorts e Instagram Reels.
Tu trabajo: encontrar en este video largo los momentos que harían que alguien deje de hacer scroll,
vea hasta el final, comente y comparta.

Video: "{video_title}"
Transcripción en frases (índice [inicio-fin en segundos] texto). ⚡ = la voz sube de energía (gritos, risas, emoción):
{listing}

Elige los MEJORES clips: devuelve entre {want} y {ask_n} candidatos (los mejores primero). Cómo piensa un buen editor:
1. GANCHO: la primera frase del clip tiene que atrapar sola: una pregunta intrigante, una afirmación fuerte o
   polémica, una cifra sorprendente, el inicio de una historia ("El día que...") o un momento de emoción.
   Si el gancho está en medio de una idea, empieza AHÍ, no antes. Nunca empieces con relleno ("bueno", "y", "entonces",
   saludos, "como les decía").
2. AUTONOMÍA (lo más importante para que el clip TENGA SENTIDO): alguien que nunca vio el video lo tiene que entender de
   principio a fin. Descarta fragmentos de conversación sueltos, respuestas sin su pregunta, chistes que dependen de algo
   dicho antes ("eso que dije", "lo de antes") y partes donde se habla de algo que no se explica en el propio clip.
3. ARCO: gancho → desarrollo → remate. EL FINAL IMPORTA TANTO COMO EL GANCHO: el clip termina cuando la idea,
   la historia o el argumento YA QUEDÓ CERRADO (conclusión, punchline, frase memorable o cambio claro de tema).
   NUNCA termines mientras la persona sigue explicando: si la frase siguiente continúa o completa lo anterior
   (empieza con "porque", "entonces", "por eso", "pero", "así que", "y", "es decir", "o sea"...) o la frase actual
   acaba en coma o queda abierta, INCLUYE las siguientes frases hasta el cierre. Usa la duración que haga falta
   (hasta el máximo): es preferible un clip largo y completo a uno corto que se corta a mitad de idea.
   Si la idea no cabe completa en el máximo, empieza más tarde (en otro gancho) en vez de cortar el final.
4. EMOCIÓN Y VALOR: humor, sorpresa, polémica, confesiones, consejos concretos, historias personales, datos.
   Las frases con ⚡ suelen ser buenos momentos. Prioriza con prudencia los tramos con 🔥 (reacción del chat)
   o ↻ (repeticiones de YouTube): son señales de interés, no una garantía de que el fragmento tenga sentido.
5. DESCARTA: intro, despedidas, patrocinios, "suscríbete", partes técnicas aburridas, silencios, repeticiones.
6. VARIEDAD: cada clip sobre un tema o momento distinto.

Puntuación (virality_score 0-100). La nota es RELATIVA a ESTE video: el mejor momento que haya merece una nota alta si de
verdad funciona como clip; no lo castigues por no ser un viral perfecto. Usa todo el rango para poder ordenar:
- 85-100: funcionaría de verdad. Gancho fuerte, arco completo y una frase que la gente repetiría.
- 70-84: sólido. Se entiende solo y tiene remate; el gancho podría ser mejor.
- 50-69: se deja ver pero no destaca.
- Menos de 50 o que NO se entienda solo: NO lo devuelvas.
Las notas parciales (gancho, emoción, valor, autonomía, remate) son de 0 a 10 y tienen que ser coherentes con la global.
Devuelve hasta {ask_n} candidatos, pero MENOS si no hay tantos momentos buenos: es mejor 2 clips excelentes que
{want} de relleno. No alargues un clip para llegar a una duración ni juntes dos momentos sin relación.

Reglas:
- Duración de cada clip: entre {opts.min_len:.0f} y {opts.max_len:.0f} segundos (fin de end_line menos inicio de start_line).
- Los clips no se pueden solapar.
- Ordénalos de mayor a menor virality_score.
- opening_words: copia literal de las primeras palabras dichas en el clip.
- title, hook, caption, hashtags y keywords en el mismo idioma del video. keywords deben ser palabras que aparecen
  textualmente en esas frases."""

    result = ask_claude(prompt, AIResult, opts)

    clips: list[Clip] = []
    used: list = []

    def blend(c) -> int:
        """Nota final: la global de la IA mezclada con sus notas parciales (así una nota global inflada no manda sola)."""
        q = 0.30 * c.gancho + 0.20 * c.emocion + 0.15 * c.valor + 0.20 * c.autonomia + 0.15 * c.remate
        return int(round(0.5 * c.virality_score + 5.0 * q))

    ranked = sorted(result.clips, key=lambda x: -blend(x))
    # un clip "sin sentido" casi siempre tiene poca autonomía, no cierra o no engancha: se descartan primero
    strict = [c for c in ranked if c.autonomia >= 6 and c.remate >= 5 and c.gancho >= 5]
    pool = strict if strict else ranked
    for c in pool:
        i = max(0, min(c.start_line, len(lines) - 1))
        j = max(i, min(c.end_line, len(lines) - 1))
        # Ajustar a la duración pedida
        while j > i and lines[j]["e"] - lines[i]["s"] > opts.max_len * 1.1:
            j -= 1
        while j < len(lines) - 1 and lines[j]["e"] - lines[i]["s"] < opts.min_len * 0.9:
            j += 1
        rng = (lines[i]["s"], lines[j]["e"])
        if blend(c) < 50 or any(_overlaps(rng, u, gap=0.5) for u in used):
            continue
        used.append(rng)
        kws = [_norm(k) for kw in c.keywords for k in kw.split() if _norm(k)]
        # Verificar el gancho: buscar las palabras de apertura cerca del inicio y empezar justo ahí
        start_t = _trim_start(lines[i])
        q = [_norm(x) for x in c.opening_words.split() if _norm(x)][:4]
        if len(q) >= 2:
            cand = [w for l in lines[max(0, i - 2): min(len(lines), i + 3)] for w in l.get("words", [])]
            for k in range(len(cand) - len(q) + 1):
                if [_norm(w["w"]) for w in cand[k:k + len(q)]] == q:
                    if opts.min_len * 0.85 <= rng[1] - cand[k]["s"] <= opts.max_len * 1.15:
                        start_t = cand[k]["s"]
                    break
        clips.append(Clip(index=len(clips) + 1, start=max(0, start_t - 0.1), end=rng[1] + 0.35,
                          title=c.title, hook=c.hook, score=blend(c), reason=c.reason,
                          caption=c.caption, hashtags=[h if h.startswith("#") else "#" + h for h in c.hashtags],
                          keywords=kws[:10]))
        if len(clips) >= want:
            break
    return clips


def refine_boundaries(clips: list, tr: dict, opts: Options) -> list:
    """Segunda pasada de la IA: ajusta el inicio y el final de cada clip palabra por palabra,
    para empezar justo en el gancho y terminar justo después del remate."""
    from pydantic import BaseModel, Field

    class Ajuste(BaseModel):
        clip: int = Field(description="número del clip")
        start_word: int = Field(description="índice de la primera palabra del clip")
        end_word: int = Field(description="índice de la última palabra del clip (incluida)")

    class Ajustes(BaseModel):
        ajustes: list[Ajuste]

    words = [w for s in tr["segments"] for w in s.get("words", [])]
    if not words or not clips:
        return clips
    blocks = []
    for c in clips:
        idx = [k for k, w in enumerate(words) if c.start - 8 <= w["s"] <= c.end + 8]
        if not idx:
            continue
        cur_a = next((k for k in idx if words[k]["s"] >= c.start - 0.05), idx[0])
        cur_b = max((k for k in idx if words[k]["e"] <= c.end + 0.05), default=idx[-1])
        txt = " ".join(("»" if k == cur_a else "") + f"[{k}|{words[k]['s']:.1f}]{words[k]['w']}" + ("«" if k == cur_b else "")
                       for k in idx)
        blocks.append(f"CLIP {c.index} — \"{c.title}\" (ahora: palabras {cur_a} a {cur_b})\n{txt}")
    prompt = f"""Eres editor de clips virales. Ya elegimos estos clips; ahora afina dónde empieza y dónde termina cada uno.
Cada palabra aparece como [índice|segundo]palabra. » marca el inicio actual y « el final actual. Hay unos segundos
de contexto antes y después por si conviene mover los cortes.

{chr(10).join(blocks)}

Para cada clip devuelve start_word y end_word:
- Empieza EXACTAMENTE en la primera palabra del gancho: sin muletillas, saludos ni conectores ("y", "bueno", "entonces",
  "o sea"), y sin cortar una frase a la mitad.
- Termina justo después del remate o de la idea completa, al final de una frase. No dejes relleno ni el inicio de otra idea,
  pero NUNCA cortes antes de que quien habla cierre la idea (si la frase siguiente la completa, inclúyela).
- Duración (segundo de la última palabra menos segundo de la primera): entre {opts.min_len:.0f} y {opts.max_len:.0f} s.
- Si el corte actual ya es el mejor, devuelve los mismos índices."""
    res = ask_claude(prompt, Ajustes, opts)
    by = {a.clip: a for a in res.ajustes}
    for c in clips:
        a = by.get(c.index)
        if not a or not (0 <= a.start_word < a.end_word < len(words)):
            continue
        ns, ne = max(0.0, words[a.start_word]["s"] - 0.1), words[a.end_word]["e"] + 0.35
        if not (opts.min_len * 0.9 <= ne - ns <= opts.max_len * 1.1):
            continue
        if abs(ns - c.start) > 12 or abs(ne - c.end) > 12:
            continue
        if any(o is not c and _overlaps((ns, ne), (o.start, o.end), gap=0.3) for o in clips):
            continue
        c.start, c.end = ns, ne
    return clips


_END_RE = re.compile(r"[.!?…][\"')\]»”]*$")
_CONNECT = {"porque", "pero", "entonces", "así", "asi", "por", "es", "o", "pues", "aunque", "sino", "y", "e", "que",
            "because", "but", "so", "then", "and", "which", "meaning", "cause"}


def extend_to_sentence_end(clips: list, tr: dict, opts: Options) -> list:
    """Red de seguridad sin IA: si un clip termina a mitad de frase (o la frase siguiente es la continuación:
    "porque...", "pero...", "entonces..."), lo alarga hasta cerrar la idea, sin pasar de la duración máxima."""
    words = [w for s in tr["segments"] for w in s.get("words", [])]
    if len(words) < 20:
        return clips
    punct = sum(1 for w in words if _END_RE.search(w["w"])) / len(words)
    if punct < 0.015:      # transcripción sin puntuación (p. ej. subtítulos automáticos): no se puede saber dónde acaba una frase
        return clips
    for c in clips:
        b = max((k for k, w in enumerate(words) if w["e"] <= c.end + 0.05), default=None)
        if b is None or words[b]["s"] < c.start:
            continue
        limit = c.start + opts.max_len * 1.05
        k, moved = b, False
        steps = 0
        while k + 1 < len(words) and not _END_RE.search(words[k]["w"]) and steps < 45:
            nxt = words[k + 1]
            if nxt["e"] + 0.35 > limit or nxt["s"] - words[k]["e"] > 1.6:
                break
            k, steps, moved = k + 1, steps + 1, True
        if not _END_RE.search(words[k]["w"]):
            continue                                   # no se cierra a tiempo: se deja como está
        # la frase siguiente es la continuación de la idea ("porque...", "pero..."): se incluye una más
        if k + 1 < len(words) and words[k + 1]["s"] - words[k]["e"] < 1.0 and _norm(words[k + 1]["w"]) in _CONNECT:
            j = k + 1
            while j + 1 < len(words) and not _END_RE.search(words[j]["w"]) and j - k < 45:
                if words[j + 1]["e"] + 0.35 > limit or words[j + 1]["s"] - words[j]["e"] > 1.6:
                    break
                j += 1
            if _END_RE.search(words[j]["w"]) and words[j]["e"] + 0.35 <= limit:
                k, moved = j, True
        if not moved:
            continue
        ne = words[k]["e"] + 0.35
        if any(o is not c and _overlaps((c.start, ne), (o.start, o.end), gap=0.3) for o in clips):
            continue
        c.end = ne
    return clips


def complete_endings(clips: list, tr: dict, opts: Options) -> list:
    """Pasada de la IA solo para los finales: enseña a la IA lo que viene DESPUÉS del corte y le pregunta si la idea
    ya quedó cerrada; si no, mueve el final (y el inicio si hace falta) hasta que la idea quede completa."""
    from pydantic import BaseModel, Field

    class Final(BaseModel):
        clip: int = Field(description="número del clip")
        idea_completa: bool = Field(description="true si en el corte actual la idea ya quedó cerrada")
        start_word: int = Field(description="índice de la primera palabra del clip (igual que ahora salvo que haga falta empezar más tarde)")
        end_word: int = Field(description="índice de la última palabra donde la idea queda cerrada (al final de una frase)")

    class Finales(BaseModel):
        finales: list[Final]

    words = [w for s in tr["segments"] for w in s.get("words", [])]
    if not words or not clips:
        return clips
    blocks = []
    for c in clips:
        a = next((k for k, w in enumerate(words) if w["s"] >= c.start - 0.05), None)
        b = max((k for k, w in enumerate(words) if w["e"] <= c.end + 0.05), default=None)
        if a is None or b is None or b <= a:
            continue
        tail = [k for k in range(b + 1, len(words)) if words[k]["s"] <= c.end + 28][:90]
        inside = " ".join(f"[{k}]{words[k]['w']}" for k in range(a, b + 1))
        after = " ".join(f"[{k}]{words[k]['w']}" for k in tail) or "(no hay más texto)"
        blocks.append(f"CLIP {c.index} — \"{c.title}\" · dura {c.end - c.start:.0f} s · palabras {a} a {b}\n"
                      f"TEXTO DEL CLIP: {inside}\n=== AQUÍ TERMINA EL CORTE ACTUAL ===\nLO QUE SE DICE DESPUÉS: {after}")
    if not blocks:
        return clips
    prompt = f"""Eres editor de clips virales. Revisa SOLO LOS FINALES de estos clips. El problema que queremos evitar: un clip con
buen gancho y desarrollo que se corta ANTES de que quien habla termine la idea.

{chr(10).join(blocks)}

Para cada clip decide:
- idea_completa: ¿el clip termina cuando la idea, historia o argumento ya quedó cerrado (conclusión, remate, frase final)?
  Si la última frase queda abierta, acaba en coma, o lo que se dice después la completa o la explica ("porque...", "entonces...",
  "por eso...", la conclusión, el remate), la idea NO está completa.
- end_word: la palabra donde la idea queda cerrada, siempre al final de una frase. Si no está completa, avanza hasta el cierre
  usando "LO QUE SE DICE DESPUÉS". Si ya está completa, deja la misma palabra final. Si hay relleno ajeno al final
  (otro tema que empieza), retrocede hasta el cierre real.
- start_word: igual que ahora, salvo que alargar el final haga pasar de {opts.max_len:.0f} segundos: en ese caso empieza más
  tarde (en otro gancho, en inicio de frase) para que quepa la idea COMPLETA. Nunca sacrifiques el final.
- Duración total (de start_word a end_word) entre {opts.min_len:.0f} y {opts.max_len:.0f} segundos."""
    res = ask_claude(prompt, Finales, opts)
    by = {f.clip: f for f in res.finales}
    for c in clips:
        f = by.get(c.index)
        if not f or not (0 <= f.start_word < f.end_word < len(words)):
            continue
        ns, ne = max(0.0, words[f.start_word]["s"] - 0.1), words[f.end_word]["e"] + 0.35
        if not (opts.min_len * 0.9 <= ne - ns <= opts.max_len * 1.1):
            continue
        if abs(ns - c.start) > 20 or abs(ne - c.end) > 25:
            continue
        if any(o is not c and _overlaps((ns, ne), (o.start, o.end), gap=0.3) for o in clips):
            continue
        c.start, c.end = ns, ne
    return clips


def _silences_around(src: Path, t: float, radius: float = 0.8) -> list:
    """Silencios (inicio, fin) en segundos absolutos alrededor del instante t."""
    t0 = max(0.0, t - radius)
    r = _sp_run(["ffmpeg", "-v", "error", "-ss", f"{t0:.3f}", "-t", f"{2 * radius:.3f}", "-i", str(src),
                 "-vn", "-ac", "1", "-ar", "16000", "-f", "s16le", "-"], capture_output=True)
    a = np.frombuffer(r.stdout or b"", dtype=np.int16).astype(np.float32) / 32768.0
    hop = 320  # 20 ms
    if len(a) < hop * 10:
        return []
    fr = a[: len(a) // hop * hop].reshape(-1, hop)
    db = 20 * np.log10(np.sqrt((fr ** 2).mean(axis=1)) + 1e-6)
    thr = min(float(np.percentile(db, 90)) - 22, -35.0)   # 22 dB por debajo de la voz
    quiet = db < thr
    out, k = [], 0
    while k < len(quiet):
        if quiet[k]:
            j = k
            while j < len(quiet) and quiet[j]:
                j += 1
            if (j - k) * 0.02 >= 0.08:
                out.append((t0 + k * 0.02, t0 + j * 0.02))
            k = j
        else:
            k += 1
    return out


def snap_to_silence(src: Path, clips: list) -> list:
    """Mueve el inicio y el final de cada clip a un silencio real del audio (como haría un editor),
    en vez de usar un margen fijo que puede cortar una respiración o media palabra."""
    for c in clips:
        try:
            w0, w1 = c.start + 0.1, c.end - 0.35         # primera y última palabra (aprox.)
            pre = [s for s in _silences_around(src, w0) if s[0] <= w0 + 0.15]
            if pre:
                s0, s1 = min(pre, key=lambda s: abs(s[1] - w0))
                if abs(s1 - w0) <= 0.6:
                    c.start = max(0.0, max(s0 + 0.04, s1 - 0.12))
            post = [s for s in _silences_around(src, w1) if s[1] >= w1 - 0.15]
            if post:
                s0, s1 = min(post, key=lambda s: abs(s[0] - w1))
                if abs(s0 - w1) <= 0.6:
                    c.end = max(c.start + 1.0, min(s1 - 0.04, s0 + 0.28))
        except Cancelled:
            raise
        except Exception:
            pass
    return clips


LAST_SELECTION: dict = {}


def select_clips(src: Path, tr: dict, opts: Options, title: str, progress: ProgressFn = _noop) -> list[Clip]:
    global _AI_NOTIFY
    _AI_NOTIFY = progress
    LAST_SELECTION.clear()
    LAST_SELECTION.update(mode="ia", reason="")
    backend = ai_backend() if opts.use_ai else None
    clips: list[Clip] = []
    if backend:
        try:
            via = backend_name(backend)
            progress(42, f"La IA ({via}) está eligiendo los mejores momentos...")
            clips = select_ai(tr, opts, title, src)
            if clips and opts.refine:
                progress(43, "La IA está afinando el inicio y el final de cada clip...")
                try:
                    clips = refine_boundaries(clips, tr, opts)
                except Exception as e:
                    progress(43, f"No se pudo afinar los cortes ({str(e)[:80]}); se usan los originales.")
            if clips and opts.complete_ideas:
                progress(43.3, "La IA comprueba que cada clip termine cuando la idea queda cerrada...")
                try:
                    clips = complete_endings(clips, tr, opts)
                except Exception as e:
                    progress(43.3, f"No se pudo revisar los finales con IA ({str(e)[:80]}).")
        except Exception as e:  # cae al algoritmo local
            progress(42, f"IA no disponible ({str(e)[:80]}), usando algoritmo local...")
            LAST_SELECTION.update(mode="basico", reason=f"La IA falló: {str(e)[:160]}")
    if clips and len(clips) < opts.num_clips:
        progress(43.5, f"La IA solo encontró {len(clips)} momento(s) realmente bueno(s): no se rellena con clips flojos.")
    if not clips:
        if not opts.use_ai and not backend:
            LAST_SELECTION.update(mode="local", reason="Selección local gratuita (volumen, risas, ganchos y ritmo). La IA solo interviene al pulsar «Optimizar con IA».")
        elif LAST_SELECTION.get("mode") != "basico":
            LAST_SELECTION.update(mode="basico", reason="La IA no encontró momentos que valgan la pena." if backend else
                                  ("Desactivaste la IA para elegir momentos." if not opts.use_ai else "No hay una IA activa (Ajustes → Inteligencia artificial)."))
        progress(43, "Analizando energía, ganchos y ritmo...")
        extra = select_heuristic(src, tr, opts)
        for c in extra:
            if len(clips) >= opts.num_clips:
                break
            if not any(_overlaps((c.start, c.end), (x.start, x.end), gap=0.5) for x in clips):
                c.index = len(clips) + 1
                clips.append(c)
    if clips and opts.complete_ideas:
        clips = extend_to_sentence_end(clips, tr, opts)      # red de seguridad: nunca terminar a mitad de frase
    if clips and opts.snap_silence and src:
        clips = snap_to_silence(src, clips)
    return clips


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
    """Detección permisiva (solo cuando el usuario elige el modo stream a mano)."""
    n = max(1, sum(1 for d in dets if d is not None))
    counts: dict = {}
    for faces in dets:
        for cell in {(int(cx / src_w * 8), int(cy / src_h * 8)) for cx, cy, fh in (faces or [])
                     if fh < src_h * 0.22}:
            counts[cell] = counts.get(cell, 0) + 1
    cam = set()
    for (gx, gy), c in counts.items():
        edge = gx <= 2 or gx >= 5          # pegada a un lado (arriba, abajo o a media altura)
        if edge and c >= 0.3 * n:
            cam.add((gx, gy))
    return cam


def _find_facecam(dets: list, motion: Optional[np.ndarray], src_w: int, src_h: int) -> set:
    """Detección estricta de la webcam de un streamer (modo automático).

    Solo es webcam si TODO se cumple:
      - una cara pequeña (5-20 % del alto) metida en una esquina de verdad,
      - presente en buena parte del clip y prácticamente inmóvil (es un recuadro pegado encima),
      - no hay otra persona grande en cámara (eso sería un video normal / podcast),
      - lo de fuera del recuadro se mueve tanto o más que la propia cara (es un juego, no una pared).
    Una persona sentada a un lado en un plano normal NO pasa estas pruebas.
    """
    n = len(dets)
    if n < 6:
        return set()
    big = sum(1 for faces in dets if any(fh > src_h * 0.25 for _, _, fh in faces))
    if big > 0.3 * n:
        return set()
    cands = [(cx, cy, fh) for faces in dets for cx, cy, fh in faces
             if src_h * 0.05 <= fh <= src_h * 0.20
             and (cx < src_w * 0.30 or cx > src_w * 0.70)]
    if not cands:
        return set()
    counts: dict = {}
    for cx, cy, fh in cands:
        cell = (int(cx / src_w * 8), int(cy / src_h * 8))
        counts[cell] = counts.get(cell, 0) + 1
    cell, c = max(counts.items(), key=lambda kv: kv[1])
    near = [f for f in cands if abs(int(f[0] / src_w * 8) - cell[0]) <= 1 and abs(int(f[1] / src_h * 8) - cell[1]) <= 1]
    frames_with = sum(1 for faces in dets if any(
        abs(int(cx / src_w * 8) - cell[0]) <= 1 and abs(int(cy / src_h * 8) - cell[1]) <= 1 for cx, cy, _ in faces))
    if frames_with < 0.55 * n:
        return set()
    # Otra persona en el plano (podcast, entrevista, videollamada, reacción en pantalla dividida):
    # un juego casi nunca muestra más caras, así que NO es un stream con webcam.
    others = sum(1 for faces in dets if any(
        fh >= src_h * 0.12 and not (abs(int(cx / src_w * 8) - cell[0]) <= 1 and abs(int(cy / src_h * 8) - cell[1]) <= 1)
        for cx, cy, fh in faces))
    if others > 0.25 * n:      # personajes del juego (caras pequeñas) no cuentan; una persona real grande sí
        return set()
    arr = np.array(near, dtype=float)
    if np.std(arr[:, 0]) > src_w * 0.03 or np.std(arr[:, 1]) > src_h * 0.04:
        return set()
    if motion is not None:
        mh, mw = motion.shape
        cx, cy, fh = np.median(arr, axis=0)
        bw, bh = 2.4 * fh, 2.0 * fh
        x0, x1 = int(max(0, (cx - bw / 2) / src_w * mw)), int(min(mw, (cx + bw / 2) / src_w * mw))
        y0, y1 = int(max(0, (cy - bh / 2) / src_h * mh)), int(min(mh, (cy + bh / 2) / src_h * mh))
        mask = np.ones_like(motion, dtype=bool)
        mask[y0:y1, x0:x1] = False
        inside = float(motion[~mask].mean()) if (~mask).any() else 0.0
        outside = float(motion[mask].mean())
        if outside < 3.5 or outside < 0.8 * inside:   # fondo quieto: es un plano normal, no un juego
            return set()
    cells = {(gx, gy) for gx in range(cell[0] - 1, cell[0] + 2) for gy in range(cell[1] - 1, cell[1] + 2)}
    return cells


def _hist(frame):
    small = cv2.resize(frame, (64, 36))
    hsv = cv2.cvtColor(small, cv2.COLOR_BGR2HSV)
    hst = cv2.calcHist([hsv], [0, 1], None, [16, 8], [0, 180, 0, 256])
    return cv2.normalize(hst, hst).flatten()


SPLIT_TOP = 0.38   # fracción de la altura para la webcam en el modo stream

CAM_MAX_UP = 2.2   # ampliación máxima de la webcam antes de pasar a la tarjeta nítida sobre fondo difuminado
CAM_FILL_UP = 2.0  # al seguir la cara: se aleja el encuadre hasta que la webcam no se amplíe más de esto (si no, borrosa)


def _unsharp(img: np.ndarray, amount: float = 0.6, sigma: float = 1.0) -> np.ndarray:
    blur = cv2.GaussianBlur(img, (0, 0), sigma)
    return cv2.addWeighted(img, 1.0 + amount, blur, -amount, 0)


def _cam_panel(crop: np.ndarray, W: int, H: int, max_up: float = CAM_MAX_UP) -> np.ndarray:
    """Panel de la webcam del streamer (W x H) con la mejor nitidez posible.
    La webcam de un stream es pequeña (a veces 300 px de ancho): estirarla a 1080 px la deja borrosa. Por eso se
    limpia la compresión antes de ampliar, se amplía con Lanczos y se afina; y si hay que ampliar más de `max_up`
    veces, se muestra en una "tarjeta" nítida sobre su propio fondo difuminado en vez de estirarla de borde a borde."""
    h, w = crop.shape[:2]
    clean = cv2.bilateralFilter(crop, 5, 18, 5) if max(W / w, H / h) > 1.3 else crop
    up_fill = max(W / w, H / h)
    if up_fill <= max_up:
        return _unsharp(cv2.resize(clean, (W, H), interpolation=cv2.INTER_LANCZOS4), 0.55, 1.0)
    fw, fh = min(W, int(w * max_up) // 2 * 2), min(H, int(h * max_up) // 2 * 2)
    small = cv2.resize(crop, (max(8, W // 10), max(8, H // 10)), interpolation=cv2.INTER_AREA)
    bg = cv2.resize(cv2.GaussianBlur(small, (0, 0), 2.0), (W, H), interpolation=cv2.INTER_CUBIC)
    bg = (bg.astype(np.float32) * 0.6).astype(np.uint8)
    fg = _unsharp(cv2.resize(clean, (fw, fh), interpolation=cv2.INTER_LANCZOS4), 0.7, 1.0)
    x0, y0 = (W - fw) // 2, (H - fh) // 2
    bg[y0:y0 + fh, x0:x0 + fw] = fg
    return bg



def _facecam_box(faces: list, src_w: int, src_h: int) -> tuple[float, float, float]:
    """Cara media de la webcam del streamer: (centro_x, centro_y, alto) en píxeles del original."""
    arr = np.array(faces, dtype=float)
    return tuple(float(v) for v in np.median(arr, axis=0))


def _roi_motion(d: np.ndarray, x0: float, x1: float, y0: float, y1: float) -> float:
    h, w = d.shape
    a, b = int(max(0, min(w - 1, x0))), int(max(1, min(w, x1)))
    c, e = int(max(0, min(h - 1, y0))), int(max(1, min(h, y1)))
    if b <= a or e <= c:
        return 0.0
    return float(d[c:e, a:b].mean())


def _cluster_people(samples: list, k: int) -> list:
    """Agrupa las caras de un plano en k personas por su posición horizontal (k-medias en 1D)."""
    xs = np.array([f[0] for r in samples for f in r], dtype=float)
    centers = np.quantile(xs, [(i + 0.5) / k for i in range(k)])
    for _ in range(8):
        lab = np.argmin(np.abs(xs[:, None] - centers[None, :]), axis=1)
        for j in range(k):
            if np.any(lab == j):
                centers[j] = xs[lab == j].mean()
    return sorted(float(c) for c in centers)


def _speaker_track(act: np.ndarray, speech: np.ndarray, rate: float) -> np.ndarray:
    """act[k, i] = movimiento de la boca de la persona k en la muestra i.
    Devuelve quién habla en cada muestra (-1 = no está claro -> plano abierto)."""
    K, n = act.shape
    win = max(3, int(round(0.6 * rate)) | 1)
    ker = np.ones(win) / win
    sm = np.vstack([np.convolve(np.pad(act[k], (win // 2, win // 2), mode="edge"), ker, mode="valid") for k in range(K)])
    top = sm.max(axis=0)
    floor = 0.3 * float(np.percentile(top[speech], 75)) if speech.any() else 1e9
    order = np.sort(sm, axis=0)
    second = order[-2] if K > 1 else np.zeros(n)
    raw = np.where(speech & (top > floor) & (top > 1.3 * second + 1e-6), sm.argmax(axis=0), -1)

    need, hold, lost = max(2, int(0.45 * rate)), int(1.3 * rate), int(2.5 * rate)
    out = np.full(n, -1)
    cur, cand, cnt, last_sw, unk = -1, -1, 0, -10 ** 9, 0
    for i in range(n):
        r = int(raw[i])
        if r == cur:
            cand, cnt = -1, 0
            unk = unk + 1 if r == -1 else 0
        elif r >= 0:
            unk = 0
            cand, cnt = (r, cnt + 1) if r == cand else (r, 1)
            if cnt >= need and (i - last_sw >= hold or cur == -1):
                cur, last_sw, cand, cnt = r, i, -1, 0
                # el cambio de plano se adelanta al momento en que empezó a hablar
                out[max(0, i - need + 1): i] = cur
        else:
            unk += 1
            if unk >= lost and cur >= 0:   # mucho rato sin un hablante claro: abrir el plano
                cur, last_sw = -1, i
        out[i] = cur
    first = np.argmax(out >= 0) if (out >= 0).any() else None
    if first is not None and first <= int(2.0 * rate):   # no empezar abierto para cortar al segundo
        out[:first] = out[first]
    return out


def analyze_framing(path: Path, crop_w: int, src_w: int, src_h: int, fps: float, cam_mode: str = "strict",
                    wide: str = "auto", focus: str = "speaker", speech: Optional[list] = None):
    """Analiza el clip y decide el encuadre de cada fotograma.

    Devuelve (x central por frame, fracción de muestras con cara, cara de la webcam o None,
    webcam visible por frame o None, ancho del recorte por frame, extra) donde extra contiene:
      "shot": índice de plano por frame · "people": personas (cx, cy, alto) de cada plano
      "speaker": quién habla en cada frame (-1 = plano abierto / una sola persona)
    Con dos o más personas: se enfoca a la que habla (por el movimiento de su boca mientras hay voz)
    y se abre el plano cuando no está claro.
    """
    cap = cv2.VideoCapture(str(path))
    step = max(1, int(round(fps / 10)))  # ~10 muestras/seg
    rate = fps / step
    GW = 480
    gh_ = max(2, int(round(GW * src_h / src_w)))
    gs = GW / src_w
    dets, mouth, cuts, prev_h, n = [], [], [0], None, 0
    prev_g, prev_s, motion, n_motion = None, None, None, 0
    while True:
        if n % 15 == 0:
            check_cancel()
        ok = cap.grab()
        if not ok:
            break
        if n % step == 0:
            ok, fr = cap.retrieve()
            if not ok:
                break
            hst = _hist(fr)
            is_cut = prev_h is not None and cv2.compareHist(prev_h, hst, cv2.HISTCMP_CORREL) < 0.55
            if is_cut:
                cuts.append(len(dets))
            prev_h = hst
            g = cv2.cvtColor(cv2.resize(fr, (GW, gh_), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2GRAY)
            s = cv2.resize(g, (160, 90), interpolation=cv2.INTER_AREA).astype(np.float32)
            if prev_s is not None:
                dd = np.abs(s - prev_s)
                motion = dd if motion is None else motion + dd
                n_motion += 1
            prev_s = s
            faces = _detect_faces(fr)
            ms = []
            if prev_g is not None and not is_cut and faces:
                d = cv2.absdiff(g, prev_g)
                for cx, cy, fh in faces:
                    x, y, h = cx * gs, cy * gs, fh * gs
                    m = _roi_motion(d, x - 0.28 * h, x + 0.28 * h, y + 0.12 * h, y + 0.50 * h)   # boca y mandíbula
                    u = _roi_motion(d, x - 0.35 * h, x + 0.35 * h, y - 0.45 * h, y - 0.05 * h)   # ojos y frente
                    ms.append(max(0.0, m - 0.8 * u))   # se descuenta el movimiento de toda la cabeza
            else:
                ms = [0.0] * len(faces)
            prev_g = g
            dets.append(faces)
            mouth.append(ms)
        n += 1
    cap.release()
    total = n
    extra = {"shot": np.zeros(max(total, 1), dtype=int), "people": [[]], "speaker": np.full(max(total, 1), -1)}
    if not dets:
        return (np.full(max(total, 1), src_w / 2), 0.0, None, None, np.full(max(total, 1), float(crop_w)), extra)
    if motion is not None:
        motion = motion / max(1, n_motion)
    if cam_mode == "off":
        cam = set()
    elif cam_mode == "lenient":
        cam = _facecam_cells(dets, src_w, src_h)
    else:
        cam = _find_facecam(dets, motion, src_w, src_h)

    def expand(arr, fill_dtype=None):
        out = np.repeat(arr, step)[:total]
        if len(out) < total:
            out = np.pad(out, (0, total - len(out)), mode="edge")
        return out

    cam_box, cam_on = None, None
    if cam:
        in_cam = lambda f: (int(f[0] / src_w * 8), int(f[1] / src_h * 8)) in cam  # noqa: E731
        cam_faces = [f for faces in dets for f in faces if in_cam(f)]
        cam_box = _facecam_box(cam_faces, src_w, src_h)
        # ¿la webcam está visible en cada momento? (el streamer a veces la oculta)
        on = np.array([any(in_cam(f) for f in faces) for faces in dets], dtype=float)
        win = max(3, int(round(1.5 * rate)) | 1)  # ~1.5 s: ignora fallos sueltos del detector
        pad = np.pad(on, (win // 2, win // 2), mode="edge")
        on = np.array([np.median(pad[k:k + win]) for k in range(len(on))]) >= 0.5
        cam_on = expand(on)

    xs, people = [], []
    for faces, ms in zip(dets, mouth):
        real = [(f[0], f[1], f[2], m) for f, m in zip(faces, ms)
                if (int(f[0] / src_w * 8), int(f[1] / src_h * 8)) not in cam and f[2] >= src_h * 0.05]
        if real:   # descartar caras diminutas del fondo (público, carteles...)
            mx = max(f[2] for f in real)
            real = [f for f in real if f[2] >= 0.45 * mx]
        people.append(real)
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
        win = max(3, int(round(0.8 * rate)) | 1)
        pad = np.pad(filled, (win // 2, win // 2), mode="edge")
        target = np.array([np.median(pad[k:k + win]) for k in range(len(filled))])
        cur = float(np.median(target[: min(len(target), win + 1)]))
        away, need_away = 0, max(2, int(round(0.7 * rate)))
        for k in range(len(target)):
            if abs(target[k] - cur) > crop_w * 0.2:
                away += 1
                if away >= need_away:
                    cur, away = float(target[k]), 0
            else:
                away = 0
            smooth[a + k] = cur
    if np.all(np.isnan(smooth)):
        smooth[:] = src_w / 2
    else:
        idx = np.arange(len(smooth))
        good = ~np.isnan(smooth)
        smooth = np.interp(idx, idx[good], smooth[good])
    smooth = np.clip(smooth, half, src_w - half)

    # ¿hay voz en cada muestra? (tiempos de las palabras del clip)
    ns = len(smooth)
    sp = np.ones(ns, dtype=bool)
    if speech:
        sp[:] = False
        for s0, s1 in speech:
            sp[max(0, int((s0 - 0.1) * rate)): min(ns, int((s1 + 0.1) * rate) + 1)] = True

    widths = np.full(ns, float(crop_w))
    spk = np.full(ns, -1)
    shot_of = np.zeros(ns, dtype=int)
    shot_people: list = []
    min_w = {"open": src_w * 0.82, "group": crop_w * 1.7}.get(wide, crop_w)
    for si, (a, b) in enumerate(zip(cuts[:-1], cuts[1:])):
        shot_of[a:b] = si
        shot_people.append([])
        shot = people[a:b]
        if not shot:
            continue
        multi = [r for r in shot if len(r) >= 2]
        is_multi = len(multi) >= max(2, 0.2 * len(shot))
        if not is_multi and wide in ("auto", "group"):
            continue
        src_faces = [f for r in (multi if is_multi else shot) for f in r]
        if src_faces:
            lefts = [f[0] - f[2] * 0.95 for f in src_faces]
            rights = [f[0] + f[2] * 0.95 for f in src_faces]
            L, R = float(np.percentile(lefts, 5)), float(np.percentile(rights, 95))
            if not is_multi:   # solo se ve una cara: centrar entre ella y el centro del plano
                mid = (L + R) / 2
                L, R = min(L, (mid + src_w / 2) / 2 - 1), max(R, (mid + src_w / 2) / 2 + 1)
        else:
            L, R = src_w * 0.5 - 1, src_w * 0.5 + 1
        w = max((R - L) * 1.15, min_w, crop_w)
        if w >= src_w * 0.8:
            w = float(src_w)            # casi todo el ancho: mostrar el plano completo
        w = min(w, float(src_w))
        wide_c = float(np.clip((L + R) / 2, w / 2, src_w - w / 2))
        if w > crop_w * 1.05:
            widths[a:b] = w
            smooth[a:b] = wide_c
        if not is_multi:
            continue

        # --- personas del plano y quién habla ---
        K = int(min(3, max(2, round(float(np.median([len(r) for r in multi]))))))
        centers = _cluster_people(multi, K)
        act = np.zeros((K, b - a))
        per = [[] for _ in range(K)]
        for i, r in enumerate(shot):
            best = {}
            for f in r:
                k = int(np.argmin([abs(f[0] - c) for c in centers]))
                if k not in best or f[2] > best[k][2]:
                    best[k] = f
            for k, f in best.items():
                act[k, i] = f[3]
                per[k].append(f[:3])
        persons = [tuple(float(v) for v in np.median(np.array(p), axis=0)) if p else (centers[k], src_h * 0.4, src_h * 0.2)
                   for k, p in enumerate(per)]
        shot_people[si] = persons
        if focus != "speaker" or w <= crop_w * 1.05:
            continue
        who = _speaker_track(act, sp[a:b], rate)
        spk[a:b] = who
        for i in range(b - a):
            k = int(who[i])
            if k >= 0:
                widths[a + i] = float(crop_w)
                smooth[a + i] = float(np.clip(persons[k][0], half, src_w - half))

    extra = {"shot": expand(shot_of), "people": shot_people, "speaker": expand(spk)}
    return expand(smooth), found, cam_box, cam_on, expand(widths), extra


# --------------------------------------------------------------------------- #
# 4b. Tipo de video (para el encuadre automático)
# --------------------------------------------------------------------------- #
SCENE_TYPES = ("gameplay_con_webcam", "gameplay_sin_webcam", "persona_a_camara", "varias_personas",
               "pantalla_o_presentacion", "otro")


def _grab_jpeg(src: Path, t: float, width: int = 768) -> Optional[bytes]:
    r = _sp_run(["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", str(src), "-frames:v", "1",
                        "-vf", f"scale={width}:-2", "-f", "image2", "-c:v", "mjpeg", "-q:v", "4", "-"],
                       capture_output=True)
    return r.stdout or None


def classify_video(src: Path, workdir: Path, opts: Options, duration: float) -> dict:
    """Claude mira 4 fotogramas del video y dice qué tipo de video es. Se guarda en caché."""
    cache = workdir / "scene.json"
    if cache.exists():
        return json.loads(cache.read_text(encoding="utf-8"))
    from pydantic import BaseModel, Field

    class Escena(BaseModel):
        tipo: str = Field(description=" | ".join(SCENE_TYPES))
        razon: str
        cam_x0: float = Field(default=0.0, description="solo gameplay_con_webcam: borde izquierdo del recuadro de la webcam, fracción 0-1 del ancho (0 si no hay)")
        cam_y0: float = Field(default=0.0, description="borde superior del recuadro de la webcam, fracción 0-1 del alto")
        cam_x1: float = Field(default=0.0, description="borde derecho del recuadro de la webcam, fracción 0-1 del ancho")
        cam_y1: float = Field(default=0.0, description="borde inferior del recuadro de la webcam, fracción 0-1 del alto")

    times = [duration * f for f in (0.15, 0.38, 0.62, 0.85)]
    imgs = [(f"Fotograma a los {t:.0f} s", b) for t in times if (b := _grab_jpeg(src, t))]
    if not imgs:
        return {}
    prompt = f"""Mira estos fotogramas de un video y clasifícalo para recortarlo a formato vertical.
Tipos:
- gameplay_con_webcam: partida de videojuego a pantalla completa (se ve la interfaz o el mundo del juego) con
  la cámara del jugador en un RECUADRO pequeño superpuesto (normalmente en una esquina). Un podcast, una
  entrevista, una conversación, una videollamada o gente hablando NO es gameplay aunque haya recuadros.
- gameplay_sin_webcam: videojuego sin cámara del jugador.
- persona_a_camara: una persona hablando a cámara en un plano normal (aunque esté a un lado del encuadre).
- varias_personas: podcast, entrevista o conversación con dos o más personas en plano.
- pantalla_o_presentacion: grabación de pantalla, diapositivas, tutorial de software, texto o gráficos.
- otro: cualquier otra cosa (vlog, deporte, paisaje...).
Importante: una persona sentada a un lado del plano NO es una webcam; solo es webcam si es un recuadro
superpuesto sobre un juego. Si es gameplay_con_webcam, indica en cam_x0/cam_y0/cam_x1/cam_y1 (fracciones 0-1 del
fotograma) el rectángulo EXACTO del recuadro de la webcam (solo la cámara del jugador, sin el juego). Tipos válidos: {", ".join(SCENE_TYPES)}."""
    try:
        res = ask_claude(prompt, Escena, opts, imgs).model_dump()
    except Exception as e:
        return {"error": str(e)[:200]}
    if res.get("tipo") not in SCENE_TYPES:
        res["tipo"] = "otro"
    cache.write_text(json.dumps(res, ensure_ascii=False), encoding="utf-8")
    return res


def locate_player(clip_path: Path, dur: float, opts: Options) -> Optional[tuple]:
    """La IA reconoce el personaje del jugador en unos fotogramas del clip y devuelve (tiempos, xs, ys)
    en fracciones 0-1 del fotograma, o None si no se ve / no hay IA."""
    if not (opts.use_ai and ai_backend()) or dur < 2:
        return None
    from pydantic import BaseModel, Field

    class Pos(BaseModel):
        n: int = Field(description="número del fotograma (1, 2, 3...)")
        visible: bool = Field(description="false si no se ve al personaje del jugador")
        x: float = Field(description="centro del personaje, fracción 0-1 del ancho del fotograma")
        y: float = Field(description="centro del personaje, fracción 0-1 del alto del fotograma")

    class Jugador(BaseModel):
        personaje: str = Field(description="breve descripción del personaje que controla el jugador")
        posiciones: list[Pos]

    n = int(min(14, max(4, round(dur / 3.5))))
    times = [dur * (0.04 + 0.92 * i / (n - 1)) for i in range(n)]
    imgs = []
    for i, t in enumerate(times):
        b = _grab_jpeg(clip_path, t, 640)
        if b:
            imgs.append((f"Fotograma {i + 1} (segundo {t:.1f})", b))
    if len(imgs) < 3:
        return None
    prompt = f"""Estos fotogramas (en orden) son del mismo clip de un streamer jugando un videojuego.
Reconoce el PERSONAJE QUE CONTROLA EL JUGADOR (el avatar o personaje principal; en tercera persona el que sigue la
cámara; en primera persona si no se ve al personaje, usa el centro de la mira/arma) y di dónde está en cada fotograma.
Ignora la cámara del streamer (recuadro con una persona real), la interfaz y a los enemigos u otros jugadores.
Devuelve una posición por cada uno de los {len(imgs)} fotogramas (x, y como fracción 0-1 del fotograma completo);
visible=false si en ese fotograma no se ve."""
    try:
        res = ask_claude(prompt, Jugador, opts, imgs).model_dump()
    except Exception:
        return None
    pts = [(times[p["n"] - 1], float(p["x"]), float(p["y"])) for p in res.get("posiciones", [])
           if p.get("visible") and 1 <= p.get("n", 0) <= len(times) and 0 <= p["x"] <= 1 and 0 <= p["y"] <= 1]
    if len(pts) < 2:
        return None
    pts.sort()
    return [q[0] for q in pts], [q[1] for q in pts], [q[2] for q in pts]


def player_track(loc: tuple, n_frames: int, fps: float) -> tuple:
    """Posición (x, y) del personaje en cada fotograma: interpolada y suavizada (sin tirones)."""
    ts, xs, ys = loc
    t = np.arange(n_frames) / fps
    x = np.interp(t, ts, xs)
    y = np.interp(t, ts, ys)
    win = max(3, int(fps * 1.2) | 1)
    ker = np.ones(win) / win
    sm = lambda a: np.convolve(np.pad(a, (win // 2, win // 2), mode="edge"), ker, mode="valid")  # noqa: E731
    return sm(x), sm(y)


# --------------------------------------------------------------------------- #
# 4c. Efectos de edición: cortes de silencios, zoom, barra de progreso
# --------------------------------------------------------------------------- #
def keep_intervals(words: list, dur: float, max_gap: float = 0.45, pad: float = 0.12) -> list[tuple[float, float]]:
    """Tramos a conservar quitando pausas de más de max_gap segundos entre palabras."""
    if not words:
        return [(0.0, dur)]
    iv, cur_s, prev_e = [], 0.0, None
    for w in words:
        if prev_e is not None and w["s"] - prev_e > max_gap:
            iv.append((cur_s, min(dur, prev_e + pad)))
            cur_s = max(0.0, w["s"] - pad)
        prev_e = w["e"]
    iv.append((cur_s, dur))
    iv = [(a, b) for a, b in iv if b - a > 0.08]
    # demasiados cortes: unir los huecos más pequeños
    while len(iv) > 60:
        k = min(range(len(iv) - 1), key=lambda i: iv[i + 1][0] - iv[i][1])
        iv[k:k + 2] = [(iv[k][0], iv[k + 1][1])]
    return iv


def remap_time(t: float, iv: list) -> float:
    """Tiempo original del clip -> tiempo tras quitar los silencios."""
    acc = 0.0
    for a, b in iv:
        if t < a:
            return acc
        if t <= b:
            return acc + (t - a)
        acc += b - a
    return acc


def zoom_curve(n_frames: int, fps: float, cut_times: list, emph_times: list, base: float = 1.0) -> np.ndarray:
    """Escala por fotograma: alterna plano normal / plano cerrado en cada corte (como un editor)
    y da un 'golpe' de zoom suave en las palabras clave."""
    t = np.arange(n_frames) / fps
    z = np.full(n_frames, base, dtype=float)
    # cambio de plano en cada corte (oculta los saltos de los cortes de silencio)
    level, edges = 0, sorted(c for c in cut_times if c > 0.3)
    k = 0
    for i in range(n_frames):
        while k < len(edges) and t[i] >= edges[k]:
            level ^= 1
            k += 1
        z[i] = base * (1.035 if level else 1.0)
    # golpes en palabras clave: sube 0.12 s, aguanta 0.35 s, baja 0.35 s
    for e in emph_times:
        up = (t - e) / 0.12
        down = 1 - (t - e - 0.47) / 0.35
        env = np.clip(np.minimum(up, np.minimum(1.0, down)), 0, 1)
        env = env * env * (3 - 2 * env)  # suavizado
        z = np.maximum(z, z * (1 + 0.025 * env))
    return np.clip(z, 1.0, 1.07)


def apply_zoom(frame: np.ndarray, z: float, cy_frac: float = 0.42) -> np.ndarray:
    if z <= 1.001:
        return frame
    h, w = frame.shape[:2]
    cw, ch = int(w / z), int(h / z)
    x0 = (w - cw) // 2
    y0 = int(np.clip(h * cy_frac - ch * cy_frac, 0, h - ch))
    return cv2.resize(frame[y0:y0 + ch, x0:x0 + cw], (w, h), interpolation=cv2.INTER_LINEAR)


def draw_progress(frame: np.ndarray, frac: float, color_bgr: tuple, height: int = 9) -> None:
    w = frame.shape[1]
    frame[:height] = (frame[:height] * 0.35).astype(np.uint8)
    frame[:height, : int(w * min(1.0, frac))] = color_bgr


def _pick_music() -> Optional[Path]:
    import random
    if not MUSIC_DIR.exists():
        return None
    files = [f for f in MUSIC_DIR.iterdir() if f.suffix.lower() in (".mp3", ".m4a", ".wav", ".ogg", ".aac", ".flac")]
    return random.choice(files) if files else None


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


# color de las palabras clave (cifras, palabras fuertes) en cada estilo
EMPH_COLORS = {"viral": "39FF7A", "caja": "FFE600", "karaoke": "FFE600", "neon": "FF3DD8", "minimal": "FFE600"}


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
    if layout == "split":    # subtítulos en el centro, entre las dos personas
        margin_v = int(out_h * 0.478)
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
        emph_c = _ass_color(EMPH_COLORS.get(style, "39FF7A"))
        kws = {_norm(k) for k in (clip.keywords or [])} if opts.highlight_keywords else set()
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
                    is_kw = _norm(g[m]["w"]) in kws
                    if m == k:
                        glow = "\\blur4" if style == "neon" else ""
                        col, big = (emph_c, 126) if is_kw else (act_c, 112)
                        pieces.append(f"{{\\1c{col}{glow}\\fscx88\\fscy88\\t(0,90,\\fscx{big}\\fscy{big})"
                                      f"\\t(90,170,\\fscx{big - 6}\\fscy{big - 6})}}{t}{{\\r}}")
                    elif is_kw:
                        pieces.append(f"{{\\1c{emph_c}}}{t}{{\\r}}")
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
    """Fondo desenfocado y oscurecido. Todo el trabajo se hace en pequeño y solo se amplía el recorte visible (≈4x más rápido)."""
    h, w = frame.shape[:2]
    sc = max(out_w / w, out_h / h)
    sw, sh = max(2, int(w * sc / 8)), max(2, int(h * sc / 8))
    small = cv2.resize(frame, (sw, sh), interpolation=cv2.INTER_AREA)
    small = cv2.convertScaleAbs(cv2.GaussianBlur(small, (0, 0), 6), alpha=0.55)
    cw, ch = min(sw, max(2, round(out_w * sw / (w * sc)))), min(sh, max(2, round(out_h * sh / (h * sc))))
    x0, y0 = (sw - cw) // 2, (sh - ch) // 2
    return cv2.resize(small[y0:y0 + ch, x0:x0 + cw], (out_w, out_h), interpolation=cv2.INTER_LINEAR)


def _cut_clip(src: Path, clip: Clip, iv: Optional[list], fps: float, has_audio: bool, out: Path,
              opts: Optional[Options] = None) -> None:
    """Corta el clip (casi sin pérdida). Si hay tramos `iv`, quita los silencios entre ellos."""
    opts = opts or Options()
    base = ["ffmpeg", "-y", "-v", "error", "-ss", f"{clip.start:.3f}", "-i", str(src), "-t", f"{clip.duration:.3f}"]
    enc = ["-r", f"{fps:.3f}"] + video_encoder(opts, intermediate=True) + ["-c:a", "aac", "-b:a", "256k", str(out)]
    if not iv or len(iv) < 2:
        run(base + ["-map", "0:v:0", "-map", "0:a:0?"] + enc)
        return
    parts, labels = [], []
    for k, (a, b) in enumerate(iv):
        parts.append(f"[0:v:0]trim=start={a:.3f}:end={b:.3f},setpts=PTS-STARTPTS[v{k}]")
        lab = f"[v{k}]"
        if has_audio:
            fd = min(0.012, (b - a) / 4)
            parts.append(f"[0:a:0]atrim=start={a:.3f}:end={b:.3f},asetpts=PTS-STARTPTS,"
                         f"afade=t=in:d={fd:.3f},afade=t=out:st={max(0, b - a - fd):.3f}:d={fd:.3f}[a{k}]")
            lab += f"[a{k}]"
        labels.append(lab)
    parts.append("".join(labels) + f"concat=n={len(iv)}:v=1:a={1 if has_audio else 0}[v]" + ("[a]" if has_audio else ""))
    maps = ["-map", "[v]"] + (["-map", "[a]"] if has_audio else [])
    run(base + ["-filter_complex", ";".join(parts)] + maps + enc)


def _avoid_box(x0: int, gw: int, box: tuple, sw: int) -> int:
    """Mueve el recorte [x0, x0+gw] para que no tape la webcam `box`, si hay hueco a su izquierda o derecha."""
    if not (box[0] < x0 + gw and box[2] > x0):
        return x0
    opts_ = []
    if box[0] - gw >= 0:
        opts_.append(int(box[0] - gw))
    if sw - box[2] >= gw:
        opts_.append(int(box[2]))
    return min(opts_, key=lambda v: abs(v - x0)) if opts_ else x0


def render_clip(src: Path, clip: Clip, tr: dict, opts: Options, outdir: Path, meta: dict,
                progress: ProgressFn = _noop, p0: float = 0, p1: float = 100, scene: Optional[dict] = None) -> Clip:
    """Crea el clip. Si el codificador de la GPU (AMD/NVIDIA/Intel) falla, reintenta solo con el procesador (x264)."""
    try:
        return _render_clip_once(src, clip, tr, opts, outdir, meta, progress, p0, p1, scene)
    except Cancelled:
        raise
    except (RuntimeError, OSError) as e:
        enc = video_encoder(opts)
        gpu = enc[enc.index("-c:v") + 1] if "-c:v" in enc else ""
        if gpu in ("h264_amf", "h264_nvenc", "h264_qsv"):
            progress(p0, f"Clip {clip.index}: el codificador de la GPU ({gpu}) falló; reintento con el procesador. "
                         f"Motivo: {str(e).strip()[-220:]}")
            return _render_clip_once(src, clip, tr, replace(opts, device="cpu"), outdir, meta, progress, p0, p1, scene)
        raise


def _render_clip_once(src: Path, clip: Clip, tr: dict, opts: Options, outdir: Path, meta: dict,
                      progress: ProgressFn = _noop, p0: float = 0, p1: float = 100, scene: Optional[dict] = None) -> Clip:
    out_w, out_h = ASPECTS.get(opts.aspect, ASPECTS["9:16"])
    fps = min(opts.fps or meta["fps"], 60)
    name = f"{clip.index:02d}_{slug(clip.title)}"
    tmp = outdir / f".{name}_cut.mp4"
    final = outdir / f"{name}.mp4"
    ass = outdir / f".{name}.ass"

    # palabras del clip con tiempos relativos al inicio del clip
    words = [dict(w, s=w["s"] - clip.start, e=w["e"] - clip.start)
             for s in tr["segments"] for w in s["words"]
             if w["s"] >= clip.start - 0.05 and w["e"] <= clip.end + 0.05]

    # 6.1 corte preciso (+ quitar silencios)
    iv = None
    if opts.jumpcuts and words:
        iv = keep_intervals(words, clip.duration)
        removed = clip.duration - sum(b - a for a, b in iv)
        if removed < 0.4:
            iv = None
    progress(p0, f"Clip {clip.index}: cortando" + (" y quitando silencios..." if iv else "..."))
    _cut_clip(src, clip, iv, fps, meta.get("has_audio", True), tmp, opts)
    if iv:
        words = [dict(w, s=remap_time(w["s"], iv), e=remap_time(w["e"], iv)) for w in words]
    m = probe(tmp)
    sw, sh = m["width"], m["height"]
    new_dur = m["duration"] or clip.duration

    # 6.2 encuadre
    target_ratio = out_w / out_h
    crop_w = min(sw, int(round(sh * target_ratio / 2) * 2))
    crop_h = sh if crop_w < sw else min(sh, int(round(sw / target_ratio / 2) * 2))
    layout = opts.layout
    cam_mode = "lenient" if layout == "gaming" else "strict"
    wide = "auto"                                # abre el plano si hay 2+ personas
    focus, split = "speaker", False              # con 2+ personas: enfocar a quien habla
    if layout == "wide":                         # "Abierto": que salga casi todo el plano
        layout, wide, cam_mode, focus = "track", "open", "off", "wide"
    elif layout == "speaker":                    # "Seguir a quien habla"
        layout, cam_mode = "track", "off"
    elif layout == "split":                      # "Dividido": una persona arriba y otra abajo
        layout, cam_mode, focus, split = "track", "off", "wide", True
    tipo = (scene or {}).get("tipo")
    if layout == "auto" and tipo == "gameplay_con_webcam":
        cam_mode = "lenient"                     # la IA ya vio que es un stream: detección de webcam permisiva
    if layout == "auto" and tipo:
        if tipo == "pantalla_o_presentacion":
            layout = "blur"                      # se ve la pantalla completa
        elif tipo == "gameplay_sin_webcam":
            layout = "gamecenter"
        elif tipo in ("persona_a_camara", "varias_personas", "otro"):
            cam_mode = "off"                     # nunca dividir: seguir a la persona
            if tipo == "varias_personas":
                wide = "group"                   # podcast/entrevista: que salgan todos
    xs, cam, cam_on, ws, fx = None, None, None, None, None
    ai_cam = None
    if crop_w < sw and layout in ("auto", "track", "gaming"):
        progress(p0 + (p1 - p0) * 0.15, f"Clip {clip.index}: analizando el encuadre y quién habla...")
        speech, cur_iv = [], None
        for w in words:                           # tramos con voz (para saber cuándo mirar las bocas)
            if cur_iv and w["s"] - cur_iv[1] < 0.35:
                cur_iv[1] = w["e"]
            else:
                cur_iv = [w["s"], w["e"]]
                speech.append(cur_iv)
        xs, found, cam, cam_on, ws, fx = analyze_framing(tmp, crop_w, sw, sh, fps, cam_mode=cam_mode, wide=wide,
                                                         focus=focus, speech=speech or None)
        if fx is not None and (fx["speaker"] >= 0).any():
            changes = int(np.count_nonzero(np.diff(fx["speaker"])))
            progress(p0 + (p1 - p0) * 0.22, f"Clip {clip.index}: conversación detectada -> enfoco a quien habla ({changes} cambios de plano)")
        ai_cam = None
        if layout == "auto" and not cam and tipo == "gameplay_con_webcam":
            sc_ = scene or {}
            x0_, y0_, x1_, y1_ = (float(sc_.get(k, 0) or 0) for k in ("cam_x0", "cam_y0", "cam_x1", "cam_y1"))
            if 0 <= x0_ < x1_ <= 1 and 0 <= y0_ < y1_ <= 1 and (x1_ - x0_) * (y1_ - y0_) < 0.30:
                ai_cam = (x0_ * sw, y0_ * sh, x1_ * sw, y1_ * sh)     # recuadro de webcam que vio la IA
                cam = ((ai_cam[0] + ai_cam[2]) / 2, (ai_cam[1] + ai_cam[3]) / 2, (ai_cam[3] - ai_cam[1]) * 0.55)
                cam_on = np.ones(len(xs), dtype=bool)
        if layout == "auto":
            if cam:              # stream de videojuego: webcam arriba + juego abajo
                layout = "gaming"
            elif tipo == "gameplay_con_webcam":
                layout = "gamecenter"
            else:
                layout = "track" if found >= 0.35 else "blur"
        if layout == "gaming":
            xs, ws, fx = None, None, None  # el juego va con recorte fijo al centro (personaje en 3ª persona)
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
        fcx += -0.15 * fhh if fcx < sw / 2 else 0.15 * fhh
        cw = min(sw, max(2.1 * fhh, out_w / CAM_FILL_UP))   # se aleja hasta que haya resolución suficiente
        ch = min(sh, cw * top_h / out_w)
        cw = ch * out_w / top_h
        cx0 = int(np.clip(fcx - cw / 2, 0, sw - cw))
        cy0 = int(np.clip(fcy - ch * 0.45, 0, sh - ch))
        cam_rect = (cx0, cy0, int(cx0 + cw), int(cy0 + ch))
        if ai_cam:      # recuadro exacto de la IA, ampliado a la proporción del panel superior
            ax0, ay0, ax1, ay1 = ai_cam
            bw_, bh_ = max(ax1 - ax0, 8), max(ay1 - ay0, 8)
            ratio = out_w / top_h
            if bw_ / bh_ < ratio:
                bw_ = bh_ * ratio
            else:
                bh_ = bw_ / ratio
            bw_, bh_ = min(bw_, sw), min(bh_, sh)
            bw_, bh_ = min(bw_, bh_ * ratio), min(bh_, bw_ / ratio)
            ccx, ccy = (ax0 + ax1) / 2, (ay0 + ay1) / 2
            rx0 = int(np.clip(ccx - bw_ / 2, 0, sw - bw_))
            ry0 = int(np.clip(ccy - bh_ / 2, 0, sh - bh_))
            cam_rect = (rx0, ry0, int(rx0 + bw_), int(ry0 + bh_))
        gw = min(sw, int(round(sh * out_w / bot_h / 2) * 2))
        gh = sh if gw < sw else min(sh, int(round(sw * bot_h / out_w / 2) * 2))
        game_rect = ((sw - gw) // 2, (sh - gh) // 2, (sw - gw) // 2 + gw, (sh - gh) // 2 + gh)

    # recuadro completo de la webcam en el original: el panel del juego se aparta de él
    cam_ex = None
    if layout == "gaming":
        if ai_cam:
            cam_ex = tuple(ai_cam)
        elif cam:
            ccx, ccy, cfh = cam
            cam_ex = (max(0, ccx - 1.45 * cfh), max(0, ccy - 1.35 * cfh), min(sw, ccx + 1.45 * cfh), min(sh, ccy + 1.35 * cfh))

    # 6.2b reconocer al personaje del jugador (juego abajo / solo juego): el recorte del juego lo sigue
    char_x = None
    if layout in ("gaming", "gamecenter"):
        try:
            progress(p0 + (p1 - p0) * 0.27, f"Clip {clip.index}: la IA busca a tu personaje en el juego...")
            lp = locate_player(tmp, new_dur, opts)
            if lp:
                char_x, _cy = player_track(lp, max(1, int(new_dur * fps) + 2), fps)
                progress(p0 + (p1 - p0) * 0.29, f"Clip {clip.index}: personaje reconocido -> el juego lo sigue")
        except Cancelled:
            raise
        except Exception:
            char_x = None
    if layout == "gamecenter" and char_x is not None:
        xs = char_x * sw

    # 6.3 subtítulos
    build_ass(words, clip, opts, out_w, out_h, "split" if split else layout, ass)

    # 6.4 zoom dinámico y barra de progreso
    cap = cv2.VideoCapture(str(tmp))
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or max(1, int(new_dur * fps))
    zc = None
    if opts.zoom and layout not in ("gaming",):
        cuts_t, acc = [], 0.0
        for a, b in (iv or [])[:-1]:
            acc += b - a
            cuts_t.append(acc)
        # sin cortes de silencio: cambiar de plano al empezar cada frase
        if not cuts_t:
            cuts_t = [w["s"] for k, w in enumerate(words) if k and words[k - 1]["w"].rstrip().endswith((".", "?", "!"))]
        kws = {_norm(k) for k in clip.keywords}
        emph = [w["s"] for w in words if _norm(w["w"]) in kws]
        zc = zoom_curve(total, fps, cuts_t, emph)
        if ws is not None:          # en planos abiertos no hay zoom (cortaría a las personas)
            n = min(len(zc), len(ws))
            zc[:n][ws[:n] > crop_w + 2] = 1.0
        if layout == "blur":
            zc = None               # en plano completo el zoom solo restaría nitidez
        if split:
            zc = None
    style = opts.caption_style if opts.caption_style in STYLES else "viral"
    bar_rgb = STYLES[style][1].lstrip("#")
    bar_bgr = (int(bar_rgb[4:6], 16), int(bar_rgb[2:4], 16), int(bar_rgb[0:2], 16))

    # 6.5 render final: frames por pipe -> ffmpeg (+ color + subtítulos + audio)
    vchain = []
    if opts.color_pop:
        vchain.append("eq=contrast=1.06:saturation=1.22:brightness=0.01,unsharp=5:5:0.45:5:5:0")
    ass_f = f"ass='{_filter_path(ass)}'"
    if FONTS_DIR.exists() and any(f.suffix.lower() in (".ttf", ".otf") for f in FONTS_DIR.iterdir()):
        ass_f += f":fontsdir='{_filter_path(FONTS_DIR)}'"
    venc = video_encoder(opts)
    pixfmt = venc[venc.index("-pix_fmt") + 1]
    inputs = ["-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{out_w}x{out_h}", "-r", f"{fps:.3f}", "-i", "-",
              "-i", str(tmp)]
    nxt = 2
    logo = Path(opts.logo_path) if (opts.logo_on and opts.logo_path) else None
    if logo is not None and not logo.is_file():
        logo = None
    if logo is not None:       # Kit de marca: el logo como marca de agua (sobre el video, bajo los subtítulos)
        inputs += ["-loop", "1", "-i", str(logo)]
        li, nxt = nxt, nxt + 1
        lw = max(16, int(out_w * min(60.0, max(4.0, float(opts.logo_size))) / 100) // 2 * 2)
        op = min(1.0, max(0.05, float(opts.logo_opacity) / 100))
        mx, my_t, my_b = int(out_w * 0.04), int(out_h * 0.08), int(out_h * 0.14)
        xy = {"tl": f"{mx}:{my_t}", "tr": f"W-w-{mx}:{my_t}", "bl": f"{mx}:H-h-{my_b}",
              "br": f"W-w-{mx}:H-h-{my_b}", "center": "(W-w)/2:(H-h)/2"}.get(opts.logo_pos, f"W-w-{mx}:H-h-{my_b}")
        graph = [f"[0:v]{','.join(vchain) if vchain else 'null'}[base]",
                 f"[{li}:v]scale={lw}:-1,format=rgba,colorchannelmixer=aa={op:.2f}[lg]",
                 f"[base][lg]overlay={xy}:shortest=1[ovr]",
                 f"[ovr]{ass_f},format={pixfmt}[vout]"]
    else:
        vchain += [ass_f, "format=" + pixfmt]
        graph = [f"[0:v]{','.join(vchain)}[vout]"]
    maps = ["-map", "[vout]"]
    if m["has_audio"]:
        voice = "loudnorm=I=-14:TP=-1.5:LRA=11," if opts.loudnorm else ""
        graph.append(f"[1:a]{voice}aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo[voice]")
        song = _pick_music() if opts.music else None
        if song:
            inputs += ["-stream_loop", "-1", "-i", str(song)]
            graph.append("[voice]asplit=2[v1][v2]")
            graph.append(f"[{nxt}:a]aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo,"
                         f"volume={opts.music_volume:.3f},afade=t=in:d=0.8[mus]")
            graph.append("[mus][v2]sidechaincompress=threshold=0.02:ratio=8:attack=15:release=350[duck]")
            graph.append("[v1][duck]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.95[aout]")
            progress(p0 + (p1 - p0) * 0.28, f"Clip {clip.index}: música de fondo -> {song.name}")
        else:
            graph[-1] = graph[-1].replace("[voice]", "[aout]")
        maps += ["-map", "[aout]"]
    cmd = (["ffmpeg", "-y", "-v", "error"] + inputs + ["-filter_complex", ";".join(graph)] + maps +
           venc + ["-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart", "-shortest", "-t", f"{new_dur:.3f}", str(final)])
    proc = _sp_popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)

    k = 0
    broken = None
    try:
        while True:
            check_cancel()
            tight_done = False
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
                top = _cam_panel(fr[y0:y1, x0:x1], out_w, top_h)
                x0, y0, x1, y1 = game_rect
                gx0 = x0
                if char_x is not None:
                    gx0 = int(np.clip(char_x[min(k, len(char_x) - 1)] * sw - gw / 2, 0, sw - gw))
                if cam_ex:
                    gx0 = _avoid_box(gx0, gw, cam_ex, sw)
                x0, x1 = gx0, gx0 + gw
                bot = cv2.resize(fr[y0:y1, x0:x1], (out_w, bot_h), interpolation=cv2.INTER_LANCZOS4)
                if cam_ex and cam_ex[0] < x1 and cam_ex[2] > x0:      # no hay hueco sin webcam: se tapa difuminada
                    bx0, bx1 = int(max(cam_ex[0], x0) - x0), int(min(cam_ex[2], x1) - x0)
                    by0, by1 = int(cam_ex[1]), int(min(cam_ex[3], sh))
                    sx, sy = out_w / (x1 - x0), bot_h / (y1 - y0)
                    rx0, rx1, ry0, ry1 = int(bx0 * sx), int(bx1 * sx), int((by0 - y0) * sy), int((by1 - y0) * sy)
                    if rx1 > rx0 and ry1 > ry0:
                        reg = bot[max(0, ry0):ry1, rx0:rx1]
                        if reg.size:
                            sm_ = cv2.resize(reg, (max(2, reg.shape[1] // 24), max(2, reg.shape[0] // 24)), interpolation=cv2.INTER_AREA)
                            bot[max(0, ry0):ry1, rx0:rx1] = cv2.resize(cv2.GaussianBlur(sm_, (0, 0), 1.5), (reg.shape[1], reg.shape[0]), interpolation=cv2.INTER_CUBIC)
                outf = np.vstack([top, bot])
                outf[top_h - 3 : top_h + 3] = 0   # línea separadora
            else:
                cx = xs[min(k, len(xs) - 1)] if xs is not None else sw / 2
                w = int(ws[min(k, len(ws) - 1)]) if ws is not None else crop_w
                duo = None
                if split and fx is not None and layout == "track":
                    duo = fx["people"][int(fx["shot"][min(k, len(fx["shot"]) - 1)])]
                if duo and len(duo) >= 2:
                    # pantalla dividida: cada persona en su mitad (la de la izquierda arriba)
                    hh = out_h // 2
                    cw2 = int(min(sw, sh * out_w / hh, max(sw / len(duo) * 1.05, 2.6 * max(d[2] for d in duo) * out_w / hh)))
                    ch2 = int(cw2 * hh / out_w)
                    halves = []
                    for pcx, pcy, pfh in (duo[0], duo[-1]):
                        px0 = int(np.clip(pcx - cw2 / 2, 0, sw - cw2))
                        py0 = int(np.clip(pcy + 0.25 * pfh - ch2 / 2, 0, sh - ch2))
                        halves.append(cv2.resize(fr[py0:py0 + ch2, px0:px0 + cw2], (out_w, hh),
                                                 interpolation=cv2.INTER_LANCZOS4))
                    outf = np.vstack(halves)
                    if outf.shape[0] < out_h:
                        outf = np.vstack([outf, outf[-1:].repeat(out_h - outf.shape[0], axis=0)])
                    outf[hh - 3: hh + 3] = 0
                elif w > crop_w + 2:
                    # plano abierto: se ven todas las personas; arriba y abajo, fondo desenfocado
                    x0 = int(np.clip(cx - w / 2, 0, sw - w))
                    region = fr[:, x0 : x0 + w]
                    canvas = _blur_bg(region, out_w, out_h)
                    fh = min(out_h, int(sh * out_w / w) // 2 * 2)
                    fg = cv2.resize(region, (out_w, fh), interpolation=cv2.INTER_LANCZOS4)
                    y0 = max(0, (out_h - fh) // 2 - int(out_h * 0.04))
                    canvas[y0 : y0 + fh] = fg
                    outf = canvas
                else:
                    # el zoom se aplica aquí, recortando un poco más del original: una sola interpolación
                    z = float(zc[min(k, len(zc) - 1)]) if zc is not None else 1.0
                    cw_, ch_ = int(round(crop_w / z / 2) * 2), int(round(crop_h / z / 2) * 2)
                    x0 = int(np.clip(cx - cw_ / 2, 0, sw - cw_))
                    y0 = int(np.clip((sh - crop_h) // 2 + (crop_h - ch_) * 0.42, 0, sh - ch_))
                    crop = fr[y0 : y0 + ch_, x0 : x0 + cw_]
                    outf = cv2.resize(crop, (out_w, out_h), interpolation=cv2.INTER_LANCZOS4)
                    tight_done = True
            if zc is not None and not tight_done:
                outf = apply_zoom(outf, float(zc[min(k, len(zc) - 1)]))
            if opts.progress_bar:
                outf = np.ascontiguousarray(outf)
                draw_progress(outf, (k + 1) / total, bar_bgr)
            proc.stdin.write(outf.tobytes())
            k += 1
            if k % 30 == 0:
                progress(p0 + (p1 - p0) * (0.3 + 0.68 * k / total), f"Clip {clip.index}: renderizando {k}/{total} frames")
    except (Cancelled, BrokenPipeError, OSError) as exc:
        if isinstance(exc, Cancelled):
            _kill_tree(proc)
            raise
        check_cancel()   # si fue por cancelar, sale como "cancelado" y no como error
        broken = exc     # ffmpeg cerró la entrada: puede haber TERMINADO bien (ya tenía todo el audio/duración) o haber fallado
        try:             # se le deja acabar de escribir el archivo; matarlo aquí borraba su mensaje y a veces el clip bueno
            proc.stdin.close()
        except Exception:
            pass
        try:
            proc.wait(timeout=90)
        except Exception:
            _kill_tree(proc)
    finally:
        cap.release()
        if _CANCEL.get(threading.get_ident()) is not None and _CANCEL[threading.get_ident()].is_set():
            try:
                proc.wait(timeout=10)
            except Exception:
                pass
            final.unlink(missing_ok=True)
        try:
            proc.stdin.close()
        except Exception:
            pass
        err = proc.stderr.read().decode(errors="ignore")
        proc.wait()
        _unregister(proc)
    try:
        check_cancel()
    except Cancelled:
        final.unlink(missing_ok=True)   # no dejar un clip a medias
        raise
    if broken is not None and proc.returncode == 0 and final.exists() and final.stat().st_size > 2048:
        broken = None    # ffmpeg ya había terminado el clip (cortó por duración/audio) y solo cerró la tubería antes de tiempo
    if broken is not None:
        final.unlink(missing_ok=True)
        rc = proc.returncode
        rc_txt = f"código {rc & 0xFFFFFFFF:#x}" if isinstance(rc, int) else "código ?"
        raise RuntimeError(f"ffmpeg se cerró de golpe en el clip {clip.index} ({type(broken).__name__}, {rc_txt}): "
                           f"{err[-1500:].strip() or 'sin mensaje'}\nComando: {' '.join(str(x) for x in cmd)[:900]}")
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg falló en el clip {clip.index}: {err[-1500:]}")

    thumb = outdir / f"{name}.jpg"
    _sp_run(["ffmpeg", "-y", "-v", "error", "-ss", f"{min(1.5, new_dur / 2):.2f}", "-i", str(final),
                    "-frames:v", "1", "-q:v", "3", str(thumb)])
    for f in (tmp, ass):
        f.unlink(missing_ok=True)
    clip.file, clip.thumb = final.name, thumb.name if thumb.exists() else ""
    clip.layout = layout
    clip.out_duration = round(new_dur, 2)
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
        r = _sp_run(["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", str(video), "-frames:v", "1",
                            "-vf", "scale=540:-2", "-q:v", "4", "-f", "image2pipe", "-vcodec", "mjpeg", "-"],
                           capture_output=True)
        if r.returncode == 0 and r.stdout:
            out.append((t, base64.standard_b64encode(r.stdout).decode()))
    return out


def _clip_video_bytes(video: Path, max_mb: float = 17.0) -> Optional[bytes]:
    """Copia liviana del clip (480p, 15 fps, audio mono) para mandársela a la IA: que ocupe menos de ~17 MB."""
    import tempfile
    for h, crf, ab in ((480, 30, "56k"), (360, 34, "40k"), (270, 38, "32k")):
        with tempfile.TemporaryDirectory(prefix="novoclip_v_") as tmp:
            out = Path(tmp) / "c.mp4"
            r = _sp_run(["ffmpeg", "-y", "-v", "error", "-i", str(video), "-vf", f"scale=-2:{h}", "-r", "15", "-c:v", "libx264",
                         "-preset", "veryfast", "-crf", str(crf), "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", ab, "-ac", "1",
                         "-movflags", "+faststart", str(out)], capture_output=True)
            if r.returncode == 0 and out.exists() and out.stat().st_size <= max_mb * 1e6:
                return out.read_bytes()
    return None


def review_clip(clip: Clip, video: Path, tr: dict, opts: Options) -> dict:
    """Claude mira fotogramas + transcripción del clip y dice si está listo para publicar."""
    import base64
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

    vid = None
    if opts.video_ai and ai_backend() in ("gemini", "gemini_inc"):
        try:
            vid = _clip_video_bytes(video)
        except Cancelled:
            raise
        except Exception:   # noqa: BLE001
            vid = None
    video_note = ("Abajo tienes el VIDEO del clip ya editado, con su audio. Míralo y escúchalo entero (no solo fotogramas sueltos). "
                  "Además de lo siguiente, fíjate en el AUDIO: si la voz se corta al final, hay saltos bruscos o se oye mal.\n"
                  if vid else f"Abajo tienes {REVIEW_FRAMES} fotogramas del clip ya editado. ")
    prompt = f"""Eres el editor jefe de un canal de TikTok/Shorts/Reels. Revisa este clip antes de publicarlo.

Título: {clip.title}
Gancho (texto arriba los primeros 3 s): {clip.hook or "(ninguno)"}
Duración: {(clip.out_duration or clip.duration):.1f} s · Formato {opts.aspect} · Estilo de subtítulos: {opts.caption_style}

Lo que se dice en el clip:
"{texto}"

Frase justo ANTES del clip en el video original: "{before[0]['text'] if before else '(es el inicio del video)'}"
Frase justo DESPUÉS del clip: "{after[0]['text'] if after else '(es el final del video)'}"

{video_note}Revisa:
1. Encuadre: ¿la persona/sujeto principal está bien centrado o aparece cortado/fuera de cuadro? ¿hay barras negras o fotogramas vacíos?
2. Subtítulos: ¿se leen bien, tapan la cara u otro texto del video, están bien escritos?
3. Gancho: ¿los primeros segundos enganchan? ¿el titular de arriba se lee y tiene sentido?
4. Inicio y final: ¿empieza o termina a mitad de frase/idea? Usa las frases de antes y después para juzgarlo.
5. Contenido: ¿se entiende solo, sin contexto previo? ¿tiene potencial para retener al espectador?

Sé exigente pero justo: aprueba solo si se puede publicar tal cual. Responde en español."""
    if vid:
        try:
            return ask_claude(prompt, Revision, opts, None, [("Video del clip ya editado", vid)]).model_dump()
        except Cancelled:
            raise
        except Exception:   # noqa: BLE001
            prompt = prompt.replace(video_note, f"Abajo tienes {REVIEW_FRAMES} fotogramas del clip ya editado. ")   # el modelo no acepta video: fotogramas
    images = [(f"Fotograma a los {t:.1f} s", base64.b64decode(b64)) for t, b64 in _frames_b64(video, clip.out_duration or clip.duration)]
    return ask_claude(prompt, Revision, opts, images).model_dump()


# --------------------------------------------------------------------------- #
# Orquestador
# --------------------------------------------------------------------------- #
def low_res_warning(meta: Optional[dict]) -> Optional[str]:
    """Si YouTube solo entregó una versión de baja resolución, explica por qué y cómo arreglarlo."""
    if not meta or meta.get("height", 1080) >= 720:
        return None
    return (f"⚠️ YouTube solo entregó el video en {meta['width']}x{meta['height']}: los clips saldrán borrosos. "
            "Suele pasar cuando falta Deno o el descargador está viejo: instala Deno (winget install DenoLand.Deno), "
            "actualiza yt-dlp y vuelve a generar.")


def parse_json3(data: dict) -> list:
    """Subtítulos de YouTube (formato json3) -> palabras con tiempos [{"w", "s", "e"}]."""
    words = []
    for ev in data.get("events", []):
        t0 = ev.get("tStartMs")
        segs = ev.get("segs")
        if t0 is None or not segs:
            continue
        ev_end = t0 + (ev.get("dDurationMs") or 0)
        toks = []
        for sg in segs:
            txt = (sg.get("utf8") or "").replace("\n", " ").strip()
            if txt:
                toks.append((t0 + (sg.get("tOffsetMs") or 0), txt))
        timed = len(toks) > 1 and any(t != toks[0][0] for t, _ in toks)
        for k, (t, txt) in enumerate(toks):
            parts = txt.split()
            # subtítulos manuales: una línea entera sin tiempos por palabra -> se reparten en la duración
            if timed:
                end = toks[k + 1][0] if k + 1 < len(toks) else min(ev_end, t + 600 * len(parts))
            else:
                end = ev_end if ev_end > t else t + 400 * len(parts)
            step = max(1, (end - t)) / max(1, len(parts))
            for j, pw in enumerate(parts):
                if re.fullmatch(r"\[.*\]|\(.*\)|♪+", pw):
                    continue
                words.append({"w": pw, "s": round((t + j * step) / 1000, 3), "e": round((t + (j + 1) * step) / 1000, 3)})
    words.sort(key=lambda w: w["s"])
    out = []
    for w in words:   # los subtítulos automáticos repiten líneas al hacer scroll: quitar duplicados
        if out and w["w"] == out[-1]["w"] and w["s"] - out[-1]["s"] < 0.05:
            continue
        if out and w["s"] < out[-1]["e"]:
            out[-1]["e"] = max(out[-1]["s"] + 0.01, w["s"])
        out.append(w)
    return out


def fetch_captions(url: str, opts: Options) -> Optional[dict]:
    """Baja los subtítulos de YouTube (manuales o automáticos) sin descargar ni audio ni video.
    Devuelve {"language", "segments", "title", "duration", "source"} o None si el video no tiene."""
    import yt_dlp
    o = {"quiet": True, "no_warnings": True, "noplaylist": True, "skip_download": True}
    o.update(_cookie_opts_now(opts))
    with yt_dlp.YoutubeDL(o) as y:
        info = y.extract_info(url, download=False)
        manual, auto = info.get("subtitles") or {}, info.get("automatic_captions") or {}
        lang = (opts.language or info.get("language") or "").split("-")[0]
        cands = []
        for kind, table in (("manuales", manual), ("automáticos", auto)):
            keys = [k for k in table if k != "live_chat"]
            pref = ([k for k in keys if lang and k.split("-")[0] == lang and k.endswith("-orig")]
                    + [k for k in keys if lang and k == lang]
                    + [k for k in keys if lang and k.split("-")[0] == lang]
                    + [k for k in keys if k.endswith("-orig")])
            if kind == "manuales" and not pref:
                pref = keys[:1]
            cands += [(kind, k, table[k]) for k in pref]
        for kind, key, tracks in cands:
            tr = next((t for t in tracks if t.get("ext") == "json3" and t.get("url")), None)
            if not tr:
                continue
            try:
                raw = y.urlopen(tr["url"]).read()
                words = parse_json3(json.loads(raw.decode("utf-8", errors="replace")))
            except Exception:
                continue
            if len(words) < 30:
                continue
            heatmap = []
            for point in info.get("heatmap") or []:
                try:
                    heatmap.append({
                        "start_time": float(point["start_time"]),
                        "end_time": float(point["end_time"]),
                        "value": float(point["value"]),
                    })
                except (KeyError, TypeError, ValueError):
                    continue
            return {"language": key.split("-")[0], "segments": _group_words(words), "approx": True,
                    "title": info.get("title") or "video", "duration": float(info.get("duration") or 0),
                    "heatmap": heatmap, "source": f"subtítulos {kind} de YouTube ({key})"}
    return None


def align_clip(c: Clip, tr_sec: dict, approx: Optional[dict] = None, pad: float = 2.5) -> None:
    """Los subtítulos de YouTube tienen tiempos aproximados: ajusta el inicio y el final del clip a las
    palabras exactas que Whisper oyó. Si se pasan los subtítulos (`approx`), busca las mismas palabras
    de apertura y de cierre; si no las encuentra, usa la palabra más cercana en el tiempo."""
    ws = [w for s in tr_sec.get("segments", []) for w in s.get("words", [])]
    if not ws:
        return
    w0, w1 = c.start + 0.1, c.end - 0.35
    a = min(ws, key=lambda w: abs(w["s"] - w0))
    b = min(ws, key=lambda w: abs(w["e"] - w1))
    if approx:
        cw = [w for s in approx.get("segments", []) for w in s.get("words", [])
              if w["s"] >= w0 - 0.06 and w["e"] <= w1 + 0.06]
        nw = [_norm(w["w"]) for w in ws]

        def find(seq: list, t: float, last: bool):
            seq = [x for x in seq if x]
            if len(seq) < 2:
                return None
            hits = [k for k in range(len(nw) - len(seq) + 1) if nw[k:k + len(seq)] == seq]
            hits = [k for k in hits if abs((ws[k + len(seq) - 1]["e"] if last else ws[k]["s"]) - t) <= pad]
            if not hits:
                return None
            k = min(hits, key=lambda k: abs((ws[k + len(seq) - 1]["e"] if last else ws[k]["s"]) - t))
            return ws[k + len(seq) - 1] if last else ws[k]

        if len(cw) >= 6:
            a = find([_norm(w["w"]) for w in cw[:3]], w0, False) or a
            b = find([_norm(w["w"]) for w in cw[-3:]], w1, True) or b
    if abs(a["s"] - w0) <= pad and abs(b["e"] - w1) <= pad and b["e"] - a["s"] > 3:
        c.start, c.end = max(0.0, a["s"] - 0.1), b["e"] + 0.35


# --------------------------------------------------------------------------- #
# Modo manual: el usuario elige los segundos exactos de cada clip
# --------------------------------------------------------------------------- #
def parse_ranges(raw) -> list:
    """Valida y normaliza [[inicio, fin], ...] (segundos). Descarta los inválidos."""
    out = []
    for r in raw or []:
        try:
            a, b = float(r[0]), float(r[1])
        except (TypeError, ValueError, IndexError):
            continue
        if a >= 0 and b - a >= 1.0:
            out.append((round(a, 2), round(b, 2)))
    return out[:30]


def transcribe_ranges(listen: Path, workdir: Path, opts: Options, ranges: list, progress: ProgressFn = _noop) -> dict:
    """Transcribe solo los tramos elegidos (no el video entero): mucho más rápido en videos largos."""
    segments, language = [], opts.language
    for k, (a, b) in enumerate(ranges):
        check_cancel()
        pa, pb = max(0.0, a - 2.0), b + 2.0
        sub = workdir / f"rng_{k:02d}"
        sub.mkdir(exist_ok=True)
        wav = sub / "tramo.wav"
        r = _sp_run(["ffmpeg", "-y", "-v", "error", "-ss", f"{pa:.2f}", "-t", f"{pb - pa:.2f}", "-i", str(listen), "-vn",
                     "-ac", "1", "-ar", "16000", str(wav)], capture_output=True)
        if r.returncode != 0 or not wav.exists():
            raise RuntimeError(f"No pude leer el audio del tramo {k + 1} ({a:.0f}-{b:.0f} s): ¿está dentro de la duración del video?")
        progress(12 + 28 * k / max(1, len(ranges)), f"Transcribiendo solo el tramo {k + 1} de {len(ranges)}...")
        t = transcribe(wav, sub, replace(opts, language=language), progress)
        language = language or t.get("language")
        for s_ in t.get("segments", []):
            segments.append(dict(s_, s=s_["s"] + pa, e=s_["e"] + pa,
                                 words=[dict(w, s=w["s"] + pa, e=w["e"] + pa) for w in s_.get("words", [])]))
        shutil.rmtree(sub, ignore_errors=True)
    segments.sort(key=lambda x: x["s"])
    return {"language": language, "segments": segments}


def manual_clips(tr: dict, ranges: list, opts: Options, video_title: str = "") -> list:
    """Clips con EXACTAMENTE los segundos que eligió el usuario. Título, gancho y hashtags los pone la IA si hay; si no, el texto."""
    from pydantic import BaseModel, Field
    words = _all_words(tr)
    texts, clips = [], []
    for i, (a, b) in enumerate(ranges, 1):
        txt = " ".join(w["w"] for w in words if w["s"] >= a - 0.05 and w["e"] <= b + 0.05).strip()
        texts.append(txt)
        first = " ".join(txt.split()[:8]) or f"Clip {i}"
        clips.append(Clip(index=i, start=a, end=b, title=first[:60], hook=" ".join(txt.split()[:6]).upper(), score=60.0,
                          caption=first, hashtags=["#shorts", "#viral", "#fyp"], keywords=_auto_keywords(txt)))
    if not (opts.use_ai and ai_backend()) or not any(texts):
        return clips

    class Meta(BaseModel):
        clip: int = Field(description="número del clip")
        title: str = Field(description="título para publicar, máx 60 caracteres")
        hook: str = Field(description="texto en pantalla los primeros 3 s, máx 7 palabras, que genere curiosidad")
        caption: str = Field(description="descripción con una pregunta que invite a comentar")
        hashtags: list[str] = Field(description="3-6 hashtags")
        keywords: list[str] = Field(description="3-8 palabras EXACTAS dichas en el clip que conviene resaltar")
        virality_score: int = Field(description="0-100: potencial en redes")

    class Metas(BaseModel):
        clips: list[Meta]

    listing = "\n\n".join(f"CLIP {i} ({a:.0f}-{b:.0f} s): {t or '(sin voz)'}" for i, ((a, b), t) in enumerate(zip(ranges, texts), 1))
    prompt = f"""Eres editor de clips virales para TikTok/Shorts/Reels. El usuario YA eligió estos cortes: no los cambies.
Escribe para cada uno el título, el gancho de pantalla, la descripción, los hashtags y las palabras clave, en el mismo
idioma del video. Video: "{video_title}".

{listing}"""
    try:
        res = ask_claude(prompt, Metas, opts)
    except Cancelled:
        raise
    except Exception:   # noqa: BLE001
        return clips
    by = {m.clip: m for m in res.clips}
    for c in clips:
        m = by.get(c.index)
        if m:
            c.title, c.hook, c.caption, c.score = m.title, m.hook, m.caption, float(m.virality_score)
            c.hashtags = [h if h.startswith("#") else "#" + h for h in m.hashtags]
            c.keywords = [_norm(k) for kw in m.keywords for k in kw.split() if _norm(k)][:10]
    return clips



def process(source: str, workdir: Path, opts: Options, progress: ProgressFn = _noop,
            on_update: Optional[Callable[[dict], None]] = None) -> dict:
    global _AI_PROVIDER
    _AI_PROVIDER = norm_provider(opts.ai_provider)
    _report = progress

    def progress(pct: float, msg: str) -> None:  # noqa: F811 - cada aviso de progreso comprueba si se canceló
        check_cancel()
        _report(pct, msg)

    if opts.whisper_model == "auto" or opts.speed == "auto":
        progress(0.5, "Leyendo los componentes de tu equipo...")
        opts = resolve_auto(opts)
        prof = system_profile()
        progress(0.8, f"Tu equipo: {prof['summary']} → transcripción '{opts.whisper_model}' en {prof['transcribe_on']}, "
                      f"render en {prof['render_on']}")
    if parse_ranges(opts.manual_ranges):
        opts = replace(opts, jumpcuts=False, num_clips=len(parse_ranges(opts.manual_ranges)))   # los segundos elegidos se respetan: no se quitan silencios

    workdir.mkdir(parents=True, exist_ok=True)
    (workdir / "job.json").write_text(json.dumps({"source": source, "opts": asdict(opts)}, ensure_ascii=False),
                                      encoding="utf-8")
    is_url = bool(re.match(r"^https?://", source))
    audio: Optional[Path] = None     # descarga rápida: primero solo el audio
    src: Optional[Path] = None
    title = Path(source).stem
    caps: Optional[dict] = None      # modo instantáneo: subtítulos de YouTube, sin bajar nada
    if is_url and opts.smart_download and opts.use_captions:
        try:
            progress(1, "Leyendo los subtítulos de YouTube (sin descargar el video)...")
            caps = fetch_captions(source, opts)
        except Cancelled:
            raise
        except Exception as e:
            progress(1, f"No se pudieron leer los subtítulos ({str(e)[:80]}).")
        if caps:
            title = caps["title"]
            (workdir / "captions.json").write_text(json.dumps(caps, ensure_ascii=False), encoding="utf-8")
            progress(12, f"Listo en segundos: {caps['source']}. No hace falta descargar ni transcribir el video entero.")
        else:
            progress(1, "Este video no tiene subtítulos en YouTube; bajo solo el audio.")
    if is_url and opts.smart_download and not caps:
        try:
            progress(1, "Descarga rápida: bajando solo el audio para elegir los clips...")
            audio, title = download(source, workdir, opts, progress, audio_only=True, stem="audio",
                                    label="Descargando el audio...")
        except Cancelled:
            raise
        except Exception as e:
            progress(1, f"No se pudo bajar solo el audio ({str(e)[:80]}); descargo el video completo...")
            audio = None
    if is_url and audio is None and not caps:
        progress(1, "Descargando video de YouTube...")
        src, title = download(source, workdir, opts, progress)
    elif not is_url:
        src = Path(source)

    listen = audio or src            # de aquí salen la transcripción y la selección
    meta = probe(src) if src else None
    if meta:
        progress(11, f"Video: {meta['width']}x{meta['height']} @ {meta['fps']:.0f}fps, {meta['duration']:.0f}s")
        if low_res_warning(meta):
            progress(11, low_res_warning(meta))
        if not meta["has_audio"]:
            raise RuntimeError("Este video no tiene pista de audio: no se puede transcribir ni elegir clips.")

    if use_gpu(opts):
        progress(11.5, "Detectando GPU...")
    progress(11.8, "Aceleración: " + describe_device(opts))
    manual = parse_ranges(opts.manual_ranges)
    if manual:
        progress(12, f"Modo manual: {len(manual)} clip(s) con los segundos que elegiste (sin cambiarlos).")
        tr = caps if caps else transcribe_ranges(listen, workdir, opts, manual, progress)
        clips = manual_clips(tr, manual, opts, title)
    else:
        tr = caps if caps else transcribe(listen, workdir, opts, progress)
        _attach_replay_signals(tr, workdir, caps)
        if tr.get("replay"):
            progress(42.5, f"YouTube aporta {len(tr['replay'])} tramo(s) repetido(s) por la audiencia; se tendrán en cuenta al ordenar los clips.")
        clips = select_clips(listen, tr, opts, title, progress)
    if not clips:
        raise RuntimeError("No se encontraron segmentos con voz para recortar.")
    sec_pad = 10.0      # margen de video que se guarda alrededor de cada clip: permite editarlo y optimizarlo sin volver a descargar

    def full_video() -> None:
        """Plan B de la descarga rápida: bajar el video entero."""
        nonlocal src, meta, tr, caps
        progress(44, "Descargando el video completo...")
        src, _ = download(source, workdir, opts, progress)
        meta = probe(src)
        if caps:                       # ahora sí hay audio: tiempos exactos con Whisper
            exact = transcribe(src, workdir, opts, progress)
            for x in clips:
                if x not in done:
                    align_clip(x, exact, tr)
            tr, caps = exact, None

    warned = {"res": False}

    def section_for(c: Clip):
        """Baja solo el trozo del clip. Devuelve (archivo, desplazamiento, datos del video) o None si falla."""
        a, b = max(0.0, c.start - sec_pad), c.end + sec_pad
        try:
            f, _ = download(source, workdir, opts, progress, section=(a, b), stem=f"trozo_{c.index:02d}",
                            label=f"Clip {c.index}: descargando solo ese trozo ({c.duration:.0f} s)...")
            m = probe(f)
            w = low_res_warning(m)
            if w and not warned["res"]:
                warned["res"] = True
                progress(45, w)
            if m["duration"] < (c.end - a) - 0.5 or m["duration"] > (b - a) + 3.0 or not m["has_audio"]:   # el trozo no cubre el clip
                return None
            return f, a, m
        except Cancelled:
            raise
        except Exception as e:
            progress(45, f"No se pudo bajar el trozo ({str(e)[:80]}).")
            return None

    def shifted(off: float) -> dict:
        return {"language": tr.get("language"), "segments": [
            {"s": s["s"] - off, "e": s["e"] - off, "text": s["text"],
             "words": [dict(w, s=w["s"] - off, e=w["e"] - off) for w in s.get("words", [])]}
            for s in tr["segments"]]}

    outdir = workdir / "clips"
    outdir.mkdir(exist_ok=True)
    span = 55 / len(clips)
    reviewing = opts.review and ai_backend() is not None
    scene = None
    done = []
    for n, c in enumerate(clips):
        p0 = 45 + n * span
        p_end = p0 + span * (0.85 if reviewing else 1)
        part = None
        if src is None:                       # descarga rápida: solo el trozo de este clip
            progress(p0, f"Clip {c.index}: descargando solo ese trozo...")
            part = section_for(c)
            if part is None:
                progress(p0, "La descarga por trozos falló; cambio a descargar el video completo.")
                full_video()
        v_src, off, v_meta = part if part else (src, 0.0, meta)
        v_tr = shifted(off) if off else tr
        exact_ok, cap_tr = False, v_tr
        if part and caps:
            # Subtítulos = tiempos aproximados. Se transcribe SOLO este trozo (unos segundos) para
            # tener cada palabra en su sitio en los subtítulos animados y cortar con exactitud.
            try:
                sub_dir = workdir / f"tr_{c.index:02d}"
                sub_dir.mkdir(exist_ok=True)
                o2 = replace(opts, language=opts.language or caps.get("language"))
                sec_tr = transcribe(v_src, sub_dir, o2,
                                    lambda pc, m, i=c.index: progress(p0, f"Clip {i}: afinando los tiempos de ese trozo..."))
                if sec_tr.get("segments"):
                    v_tr, exact_ok = sec_tr, True
                shutil.rmtree(sub_dir, ignore_errors=True)
            except Cancelled:
                raise
            except Exception as e:
                progress(p0, f"Clip {c.index}: no se pudo afinar ({str(e)[:60]}); uso los tiempos de YouTube.")
        if scene is None and opts.layout == "auto" and opts.use_ai and ai_backend():
            progress(p0, "La IA está identificando el tipo de video (persona, podcast, gameplay, pantalla)...")
            scene = classify_video(v_src, workdir, opts, v_meta["duration"])
            if scene.get("tipo"):
                progress(p0, f"Tipo de video: {scene['tipo'].replace('_', ' ')}")
        c.start, c.end = c.start - off, c.end - off
        if exact_ok and not opts.manual_ranges:    # en modo manual los segundos del usuario no se tocan
            align_clip(c, v_tr, cap_tr)
            if opts.snap_silence:
                snap_to_silence(v_src, [c])
        try:
            c = render_clip(v_src, c, v_tr, opts, outdir, v_meta, progress, p0, p_end, scene=scene)
            if reviewing:
                progress(p_end, f"Clip {c.index}: la IA está revisando el resultado...")
                try:
                    c.review = review_clip(c, outdir / c.file, v_tr, opts)
                except Exception as e:
                    c.review = {"error": str(e)[:200]}
        finally:
            c.start, c.end = c.start + off, c.end + off
            if part:
                _keep_clip_source(workdir, c, part[0], off, part[2])   # el trozo se conserva para editar el clip después
        try:   # palabras alrededor del clip, para poder editarlo después
            exact = [dict(w, s=w["s"] + off, e=w["e"] + off) for w in _all_words(v_tr)] if exact_ok else None
            save_clip_words(workdir, c, tr, exact)
        except Exception:
            pass
        meta = meta or v_meta
        done.append(c)
        if on_update:                           # el clip aparece en la página en cuanto está listo
            on_update({"title": title, "language": tr.get("language"), "source": meta, "scene": scene or {},
                       "partial": True, "total": len(clips), "selection": dict(LAST_SELECTION),
                       "clips": [dict(asdict(x), duration=round(x.out_duration or x.duration, 2)) for x in done]})
    result = {"title": title, "language": tr.get("language"), "source": meta, "scene": scene or {},
              "selection": dict(LAST_SELECTION) if not manual else {"mode": "manual", "reason": ""},
              "clips": [dict(asdict(c), duration=round(c.out_duration or c.duration, 2)) for c in done]}
    (workdir / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    progress(100, f"¡Listo! {len(done)} clips generados.")
    return result


# --------------------------------------------------------------------------- #
# 10. Editor de cortes: ver y modificar un clip ya generado y volver a generarlo
# --------------------------------------------------------------------------- #
EDIT_MARGIN = 30.0   # segundos de transcripción guardados antes y después de cada clip


def _all_words(tr: dict) -> list:
    return [w for s in tr.get("segments", []) for w in s.get("words", [])]


def save_clip_words(workdir: Path, c: Clip, tr_abs: dict, exact: Optional[list] = None) -> None:
    """Guarda las palabras alrededor del clip (tiempos del video original) para poder editarlo luego.
    `exact`: palabras precisas de Whisper en una zona; sustituyen a las aproximadas en esa zona."""
    a, b = c.start - EDIT_MARGIN, c.end + EDIT_MARGIN
    words = [dict(w) for w in _all_words(tr_abs) if a <= w["s"] <= b]
    if exact:
        lo, hi = exact[0]["s"], exact[-1]["e"]
        words = [w for w in words if w["e"] < lo or w["s"] > hi] + [dict(w) for w in exact if a <= w["s"] <= b]
        words.sort(key=lambda w: w["s"])
    d = workdir / "edit"
    d.mkdir(exist_ok=True)
    (d / f"{c.index:02d}.json").write_text(json.dumps(words, ensure_ascii=False), encoding="utf-8")


def _job_info(workdir: Path) -> dict:
    try:
        return json.loads((workdir / "job.json").read_text(encoding="utf-8"))
    except Exception:
        return {}


EDIT_TOGGLES = ("zoom", "jumpcuts", "progress_bar", "color_pop", "music", "highlight_keywords", "loudnorm", "logo_on")


def load_clip_for_edit(workdir: Path, index: int) -> dict:
    """Datos para el editor: el clip y las palabras de alrededor con sus tiempos."""
    res = json.loads((workdir / "result.json").read_text(encoding="utf-8"))
    c = next((x for x in res["clips"] if int(x["index"]) == int(index)), None)
    if c is None:
        raise KeyError("clip no encontrado")
    f = workdir / "edit" / f"{int(index):02d}.json"
    if f.exists():
        words = json.loads(f.read_text(encoding="utf-8"))
    else:   # trabajos antiguos: sacarlas de la transcripción completa si está
        words = []
        for name in ("transcript.json", "captions.json"):
            p = workdir / name
            if p.exists():
                words = [w for w in _all_words(json.loads(p.read_text(encoding="utf-8")))
                         if c["start"] - EDIT_MARGIN <= w["s"] <= c["end"] + EDIT_MARGIN]
                break
    job = _job_info(workdir)
    o = job.get("opts", {})
    return {"clip": c, "words": words, "editable": bool(job) and (not res.get("live") or _live_src(workdir, index) is not None),
            "layout": c.get("edit_layout") or o.get("layout", "auto"),
            "caption_style": c.get("edit_style") or o.get("caption_style", "viral"),
            "styles": list(STYLES) + ["none"],
            "show_hook": bool(c.get("edit_show_hook", o.get("show_hook", True))),
            "has_logo": bool(o.get("logo_path")) and Path(o.get("logo_path", "")).is_file(),
            "toggles": {k: bool(c.get("edit_toggles", {}).get(k, o.get(k, getattr(Options, k)))) for k in EDIT_TOGGLES}}


def _local_video(workdir: Path, job: dict) -> Optional[Path]:
    """Video completo ya disponible en el disco (descarga completa o archivo subido)."""
    for f in workdir.glob("source.*"):
        if f.suffix.lower() in (".mp4", ".mkv", ".webm", ".mov") and ".f" not in f.stem:
            return f
    src = job.get("source") or ""
    if src and not re.match(r"^https?://", src) and Path(src).exists():
        return Path(src)
    return None


def rerender_clip(workdir: Path, index: int, edits: dict, progress: ProgressFn = _noop) -> dict:
    """Vuelve a generar un clip con los cambios del editor (inicio/fin, textos, palabras, encuadre, estilo)."""
    _report = progress

    def progress(pct: float, msg: str) -> None:  # noqa: F811
        check_cancel()
        _report(pct, msg)

    job = _job_info(workdir)
    if not job:
        raise RuntimeError("Este trabajo es de una versión anterior y no se puede editar. Genera los clips de nuevo.")
    base = Options()
    o = replace(base, **{k: v for k, v in job.get("opts", {}).items() if hasattr(base, k)})
    o = resolve_auto(o)
    global _AI_PROVIDER
    _AI_PROVIDER = norm_provider(o.ai_provider)
    if edits.get("layout"):
        o.layout = edits["layout"]
    if edits.get("caption_style"):
        o.caption_style = edits["caption_style"]
    if "show_hook" in edits:
        o.show_hook = bool(edits["show_hook"])
    for k in EDIT_TOGGLES:       # interruptores de este clip: subtítulos, zoom, silencios, barra, color, música...
        if k in edits and edits[k] is not None:
            setattr(o, k, bool(edits[k]))

    res_path = workdir / "result.json"
    res = json.loads(res_path.read_text(encoding="utf-8"))
    pos = next((k for k, x in enumerate(res["clips"]) if int(x["index"]) == int(index)), None)
    if pos is None:
        raise KeyError("clip no encontrado")
    old = res["clips"][pos]
    fields_ok = {f.name for f in Clip.__dataclass_fields__.values()}
    c = Clip(**{k: v for k, v in old.items() if k in fields_ok})
    for k in ("title", "hook", "caption"):
        if k in edits and edits[k] is not None:
            setattr(c, k, str(edits[k]))
    if "hashtags" in edits:
        tags = edits["hashtags"] if isinstance(edits["hashtags"], list) else str(edits["hashtags"]).split()
        c.hashtags = [t if t.startswith("#") else "#" + t for t in tags if t.strip()]
    if "keywords" in edits:
        c.keywords = [_norm(k) for k in edits["keywords"] if _norm(k)]
    start, end = float(edits.get("start", c.start)), float(edits.get("end", c.end))
    if end - start < 1.0:
        raise RuntimeError("El clip tiene que durar al menos 1 segundo.")
    c.start, c.end = max(0.0, start), end

    # palabras (con las correcciones de texto del usuario)
    wf = workdir / "edit" / f"{int(index):02d}.json"
    words = edits.get("words") or (json.loads(wf.read_text(encoding="utf-8")) if wf.exists() else
                                   load_clip_for_edit(workdir, index)["words"])
    words = [{"w": str(w["w"]).strip(), "s": float(w["s"]), "e": float(w["e"])} for w in words if str(w["w"]).strip()]
    wf.parent.mkdir(exist_ok=True)
    wf.write_text(json.dumps(words, ensure_ascii=False), encoding="utf-8")
    tr_abs = {"language": res.get("language"), "segments": _group_words(words)}

    # video: el completo si está en el disco; si no, solo el trozo necesario
    live = _live_src(workdir, index)
    if res.get("live") and not live:
        raise RuntimeError("Este clip de directo no guardó su trozo de video, así que no se puede volver a editar.")
    src = None if res.get("live") else _local_video(workdir, job)
    part, off = None, 0.0
    if src is None and live:
        src, off, kept_end = live[0], live[1], live[1] + live[2]
        url = job.get("source") or ""
        if not res.get("live") and (c.start < off - 0.05 or c.end > kept_end + 0.05) and re.match(r"^https?://", url):
            try:    # el rango pedido sale del video guardado: se intenta bajar el trozo que falta
                a, b = max(0.0, c.start - 1.5), c.end + 1.5
                progress(10, f"Descargando solo el trozo del clip ({c.end - c.start:.0f} s)...")
                part, _ = download(url, workdir, o, progress, section=(a, b), stem=f"editar_{int(index):02d}",
                                   label="Descargando el trozo del clip...")
                src, off = part, a
            except Exception:   # noqa: BLE001  (Cancelled es BaseException y sigue de largo)
                part = None
                progress(10, f"Solo hay video guardado hasta {kept_end:.0f} s; recorto el clip a ese tramo.")
        if part is None:    # solo hay video dentro del trozo guardado
            c.start, c.end = max(c.start, off), min(c.end, kept_end)
            if c.end - c.start < 1.0:
                raise RuntimeError("Ese rango queda fuera del video guardado de este clip.")
    elif src is None:
        url = job.get("source") or ""
        if not re.match(r"^https?://", url):
            raise RuntimeError("No se encuentra el video original de este trabajo.")
        a, b = max(0.0, c.start - 1.5), c.end + 1.5
        progress(10, f"Descargando solo el trozo del clip ({c.end - c.start:.0f} s)...")
        part, _ = download(url, workdir, o, progress, section=(a, b), stem=f"editar_{int(index):02d}",
                           label="Descargando el trozo del clip...")
        src, off = part, a
    meta = probe(src)
    v_tr = {"language": tr_abs["language"], "segments": [
        {"s": s["s"] - off, "e": s["e"] - off, "text": s["text"],
         "words": [dict(w, s=w["s"] - off, e=w["e"] - off) for w in s["words"]]} for s in tr_abs["segments"]]}

    outdir = workdir / "clips"
    for name in (old.get("file"), old.get("thumb")):   # borrar la versión anterior
        if name:
            (outdir / name).unlink(missing_ok=True)
    c.start, c.end = c.start - off, c.end - off
    try:
        c = render_clip(src, c, v_tr, o, outdir, meta, progress, 20, 98, scene=res.get("scene") or None)
    finally:
        c.start, c.end = c.start + off, c.end + off
        if part:
            part.unlink(missing_ok=True)
    c.review = {}
    new = dict(asdict(c), duration=round(c.out_duration or c.duration, 2),
               edited=True, edit_layout=o.layout, edit_style=o.caption_style,
               edit_toggles={k: bool(getattr(o, k)) for k in EDIT_TOGGLES}, edit_show_hook=bool(o.show_hook), rev=int(time.time()))
    res["clips"][pos] = new
    res_path.write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    progress(100, f"Clip {c.index} actualizado.")
    return res


def update_clip_meta(workdir: Path, index: int, meta: dict) -> dict:
    """Guarda al instante el título, la descripción y los hashtags de un clip (no hace falta volver a generar el video:
    esos textos son para publicar). El titular que va dentro del video sí necesita volver a generar."""
    res_path = workdir / "result.json"
    res = json.loads(res_path.read_text(encoding="utf-8"))
    pos = next((k for k, x in enumerate(res["clips"]) if int(x["index"]) == int(index)), None)
    if pos is None:
        raise KeyError("clip no encontrado")
    c = res["clips"][pos]
    for k in ("title", "caption"):
        if meta.get(k) is not None:
            c[k] = str(meta[k]).strip()
    if meta.get("hashtags") is not None:
        tags = meta["hashtags"] if isinstance(meta["hashtags"], list) else str(meta["hashtags"]).split()
        c["hashtags"] = [t if t.startswith("#") else "#" + t for t in (str(x).strip() for x in tags) if t]
    c["meta_edited"] = True
    res_path.write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    return res


# --------------------------------------------------------------------------- #
# Optimizar un clip con la IA (después de generarlo)
# --------------------------------------------------------------------------- #
_OPT_FIELDS = ("start", "end", "title", "hook", "caption", "hashtags", "keywords")


def _set_clip_fields(workdir: Path, index: int, fields_: dict) -> dict:
    res_path = workdir / "result.json"
    res = json.loads(res_path.read_text(encoding="utf-8"))
    pos = next((k for k, x in enumerate(res["clips"]) if int(x["index"]) == int(index)), None)
    if pos is None:
        raise KeyError("clip no encontrado")
    for k, v in fields_.items():
        if v is None:
            res["clips"][pos].pop(k, None)
        else:
            res["clips"][pos][k] = v
    res_path.write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    return res["clips"][pos]


def optimize_clip(workdir: Path, index: int, progress: ProgressFn = _noop) -> dict:
    """La IA mejora un clip ya generado: afina el inicio y el final (para que empiece en el gancho y termine cuando la
    idea queda cerrada), y reescribe título, gancho, descripción, hashtags y palabras clave. Guarda lo anterior para deshacer."""
    from pydantic import BaseModel, Field
    global _AI_PROVIDER
    job = _job_info(workdir)
    if not job:
        raise RuntimeError("Este trabajo es de una versión anterior y no se puede optimizar.")
    base = Options()
    o = resolve_auto(replace(base, **{k: v for k, v in job.get("opts", {}).items() if hasattr(base, k)}))
    _AI_PROVIDER = norm_provider(o.ai_provider)
    if not ai_backend():
        raise RuntimeError("Para optimizar con IA necesitas tener una IA activa (Ajustes → Inteligencia artificial).")
    data = load_clip_for_edit(workdir, index)
    c, words = data["clip"], data["words"]
    if not words:
        raise RuntimeError("No hay transcripción guardada de este clip para optimizar.")
    progress(5, "La IA está leyendo el clip y lo que viene antes y después...")
    cur = [k for k, w in enumerate(words) if w["s"] >= c["start"] - 0.05 and w["e"] <= c["end"] + 0.05]
    if not cur:
        raise RuntimeError("No encontré palabras dentro de este clip.")
    a0, b0 = cur[0], cur[-1]
    lo_i = max(0, a0 - 60)
    hi_i = min(len(words), b0 + 90)
    listing = " ".join(("»" if k == a0 else "") + f"[{k}|{words[k]['s']:.1f}]{words[k]['w']}" + ("«" if k == b0 else "")
                       for k in range(lo_i, hi_i))
    dur = c["end"] - c["start"]
    lo, hi = max(5.0, min(o.min_len, dur * 0.7)), max(o.max_len, dur * 1.25)
    rv = c.get("review") or {}
    review_txt = ""
    if rv and not rv.get("error"):
        probs = "\n".join(f"- [{p.get('gravedad', '?')}] {p.get('tipo', '')}: {p.get('detalle', '')}"
                          + (f" (hacia el segundo {p['segundo']:.0f} del clip)" if p.get("segundo") is not None else "")
                          for p in rv.get("problemas", []))
        sugs = "\n".join(f"- {x}" for x in rv.get("sugerencias", []))
        review_txt = f"""
LA REVISIÓN ANTERIOR DE ESTE CLIP (nota {rv.get('nota', '?')}/100: {rv.get('resumen', '')}) DETECTÓ:
Problemas:
{probs or '(ninguno)'}
Sugerencias:
{sugs or '(ninguna)'}
ARREGLA todo lo que esté a tu alcance con tus cambios: problemas de inicio, final, gancho o contenido se arreglan moviendo los cortes
y reescribiendo los textos; un problema de encuadre se arregla eligiendo otro "layout"; lo que no se pueda arreglar así, anótalo en "no_resuelto".
"""

    # Reparto: SONNET (cortes, encuadre, palabras clave) -> HAIKU (textos) -> OPUS verifica. Opus solo lee un resumen corto.
    class Tech(BaseModel):
        start_word: int = Field(description="índice de la primera palabra del clip (el gancho)")
        end_word: int = Field(description="índice de la última palabra (donde la idea queda cerrada, fin de frase)")
        keywords: list[str] = Field(description="3-8 palabras EXACTAS del clip que conviene resaltar")
        layout: str = Field(default="", description="solo si la revisión detectó un problema de ENCUADRE: auto | speaker | wide | track | blur | gaming | gamecenter | split. Vacío = no cambiar")
        cambios: list[str] = Field(description="2-4 frases cortas, en español, explicando qué cambiaste en el corte y por qué")
        no_resuelto: list[str] = Field(default_factory=list, description="problemas de la revisión que NO se pueden arreglar solos; vacío si arreglaste todo")

    class Copy(BaseModel):
        title: str = Field(description="título para publicar, máx 60 caracteres")
        hook: str = Field(description="texto en pantalla los primeros 3 s, máx 7 palabras, que genere curiosidad")
        caption: str = Field(description="descripción con una pregunta que invite a comentar")
        hashtags: list[str] = Field(description="3-6 hashtags")

    class Verify(BaseModel):
        ok: bool = Field(description="true si todo está bien")
        fix: str = Field(default="", description="si ok es false: tech | copy | both")
        motivo: str = Field(default="", description="qué está mal, máx 120 caracteres")

    probs_all = rv.get("problemas", []) if (rv and not rv.get("error")) else []
    TECH_TYPES = {"inicio", "final", "contenido", "encuadre", "gancho"}
    need_tech = not (rv and not rv.get("error")) or any(str(p.get("tipo")) in TECH_TYPES for p in probs_all)
    pending = [f"{p.get('tipo', 'otro')}: {p.get('detalle', '')}"[:160] for p in probs_all if str(p.get("tipo")) not in TECH_TYPES]
    tech_prompt = f"""Eres el editor técnico de un canal de TikTok/Shorts/Reels. Ajusta el CORTE de este clip YA GENERADO para que retenga más.
Cada palabra aparece como [índice|segundo]palabra. » marca el inicio actual y « el final actual; hay contexto antes y después.

Duración actual: {dur:.1f} s

{listing}
{review_txt}
Haz esto:
1. INICIO: que el clip empiece en la primera palabra del gancho (sin muletillas, saludos ni conectores como "y", "bueno", "entonces"),
   sin cortar una frase a la mitad.
2. FINAL: que termine cuando la idea o la historia queda CERRADA, al final de una frase. NUNCA cortes mientras quien habla sigue
   explicando: si lo que se dice después completa la idea, inclúyelo. Si hay relleno ajeno al final, quítalo.
3. Duración total (de start_word a end_word): entre {lo:.0f} y {hi:.0f} segundos.
4. keywords: palabras que se dicen y conviene resaltar. layout solo si hay un problema de encuadre.
5. Si el clip ya está bien, deja los mismos índices.
En "cambios" explica brevemente qué mejoraste."""

    def run_tech(extra: str = ""):
        t = ask_claude(tech_prompt + extra, Tech, o, role="tech")
        cut = None
        if 0 <= t.start_word < t.end_word < len(words):
            s2, e2 = max(0.0, words[t.start_word]["s"] - 0.1), words[t.end_word]["e"] + 0.35
            if lo * 0.9 <= e2 - s2 <= hi * 1.05 and abs(s2 - c["start"]) <= 25 and abs(e2 - c["end"]) <= 30:
                cut = (s2, e2, t.start_word, t.end_word)
        return t, cut

    def cut_text(cut) -> str:
        a, b = (cut[2], cut[3]) if cut else (a0, b0)
        return " ".join(w["w"] for w in words[a:b + 1])

    def run_copy(cut, extra: str = ""):
        pr = f"""Eres el redactor de un canal de TikTok/Shorts/Reels. Escribe los textos de este clip, en el MISMO idioma del clip.
Título actual: {c['title']}
Gancho actual: {c.get('hook') or '(ninguno)'}
Texto del clip:
{cut_text(cut)}

Escribe un título (máx 60 caracteres), un gancho (máx 7 palabras, que genere curiosidad y tenga sentido por sí solo),
una descripción con una pregunta que invite a comentar y 3-6 hashtags. No inventes datos que no se dicen en el clip.{extra}"""
        return ask_claude(pr, Copy, o, role="copy")

    def run_verify(cut, kws_, cp):
        n0, n1 = (cut[2], cut[3]) if cut else (a0, b0)
        t_s, t_e = (cut[0], cut[1]) if cut else (c["start"], c["end"])
        pr = f"""Eres el director de edición. Verifica este clip optimizado. Responde SOLO con el JSON pedido.
Duración: {t_e - t_s:.0f} s (permitido {lo:.0f}-{hi:.0f}).
Primeras 15 palabras: {' '.join(w['w'] for w in words[n0:n0 + 15])}
Últimas 15 palabras: {' '.join(w['w'] for w in words[max(n0, n1 - 14):n1 + 1])}
Lo que se dice justo después del corte: {' '.join(w['w'] for w in words[n1 + 1:n1 + 11])}
Título: {cp.title}
Gancho: {cp.hook}
Descripción: {cp.caption}
Hashtags: {' '.join(cp.hashtags)}
Palabras clave: {', '.join(kws_)}
Problemas que debía arreglar: {'; '.join(f"{p.get('tipo')}: {p.get('detalle', '')}"[:100] for p in probs_all) or '(ninguno)'}
Comprueba: (1) empieza en el gancho, sin muletillas; (2) el final cierra la idea y lo de después no la completa;
(3) título <= 60 caracteres y gancho <= 7 palabras con sentido; (4) las palabras clave aparecen en el clip; (5) cada problema está arreglado.
ok=true si todo bien. Si no: fix = tech (corte), copy (textos) o both, y motivo breve (máx 120 caracteres)."""
        return ask_claude(pr, Verify, o, role="verify")

    can_verify = ai_backend() in ("cli", "api")
    tech, cut, cp, fix, last_motivo, verified = None, None, None, "", "", None
    for rnd in range(2):
        if need_tech and (tech is None or fix in ("tech", "both")):
            progress(15 + rnd * 20, "Sonnet está ajustando el corte..." if rnd == 0 else "Sonnet corrige el corte...")
            t, cut_try = run_tech(f"\nCORRIGE: {last_motivo}" if (last_motivo and fix in ("tech", "both")) else "")
            if cut_try is None and rnd == 0:     # corte no válido: un segundo intento, sin molestar a Opus
                t, cut_try = run_tech("\nEl corte anterior NO es válido: respeta la duración y el máximo de desplazamiento.")
            tech = t
            if cut_try is not None:
                cut = cut_try
        if cp is None or fix in ("copy", "both"):
            progress(20 + rnd * 20, "Haiku está escribiendo los textos..." if rnd == 0 else "Haiku corrige los textos...")
            cp = run_copy(cut, f"\nCORRIGE: {last_motivo}" if (last_motivo and fix in ("copy", "both")) else "")
        if not can_verify:
            break
        progress(28 + rnd * 20, "Opus está verificando el resultado...")
        kws_now = [_norm(k) for kw in (tech.keywords if tech else c.get("keywords", [])) for k in kw.split() if _norm(k)][:10]
        try:
            v = run_verify(cut, kws_now, cp)
        except Cancelled:
            raise
        except Exception:   # noqa: BLE001  (si Opus falla, se aplica igual sin verificar)
            break
        verified = bool(v.ok)
        if v.ok:
            break
        fix, last_motivo = (v.fix if v.fix in ("tech", "copy", "both") else "both"), v.motivo.strip()[:120]
        need_tech = need_tech or fix in ("tech", "both")      # si Opus pide corregir el corte, Sonnet tiene que trabajar aunque antes no hiciera falta
    if verified is False and last_motivo:
        pending.append(f"Opus: {last_motivo}")
    ns, ne = (cut[0], cut[1]) if cut else (c["start"], c["end"])
    kws = [_norm(k) for kw in (tech.keywords if tech else []) for k in kw.split() if _norm(k)][:10]
    tags = [h if h.startswith("#") else "#" + h for h in cp.hashtags]
    cambios = list(tech.cambios) if tech else ["Se mejoraron los textos (el corte ya estaba bien)."]
    if tech and cut is None:
        cambios = ["El corte propuesto no era válido; se mantuvo el original."]
    pending += list(tech.no_resuelto) if tech else []
    cambios.append("Sonnet: corte · Haiku: textos · " + ("Opus verificó." if verified else "sin verificación de Opus."))
    prev = {k: c.get(k) for k in _OPT_FIELDS}
    prev["layout"] = data["layout"]
    layout_new = tech.layout.strip() if (tech and tech.layout.strip() in ("auto", "speaker", "wide", "track", "blur", "gaming", "gamecenter", "split")) else ""
    layout_changed = bool(layout_new) and layout_new != data["layout"]
    new = {"start": ns, "end": ne, "title": cp.title.strip() or c["title"], "hook": cp.hook.strip(), "caption": cp.caption.strip() or c.get("caption", ""),
           "hashtags": tags or c.get("hashtags", []), "keywords": kws or c.get("keywords", [])}
    need_render = (abs(ns - c["start"]) > 0.15 or abs(ne - c["end"]) > 0.15 or new["hook"] != (c.get("hook") or "")
                   or set(new["keywords"]) != set(c.get("keywords") or []) or layout_changed)
    if need_render:
        progress(30, "Aplicando los cambios al video...")
        edits = dict(new, show_hook=bool(new["hook"]))
        if layout_changed:
            edits["layout"] = layout_new
        rerender_clip(workdir, index, edits, lambda p, m: progress(30 + p * 0.68, m))
    else:
        update_clip_meta(workdir, index, new)
    note = list(cambios)[:7]
    if layout_changed:
        note.insert(0, f"Encuadre: de «{data['layout']}» a «{layout_new}».")
    if abs(ns - c["start"]) > 0.15 or abs(ne - c["end"]) > 0.15:
        note.insert(0, f"Corte: de {c['start']:.1f}–{c['end']:.1f} s a {ns:.1f}–{ne:.1f} s ({ne - ns:.0f} s en total).")
    out = _set_clip_fields(workdir, index, {"opt_prev": prev, "opt_note": note, "opt_pending": pending[:5] or None, "optimized": True})
    # Se vuelve a revisar el clip ya arreglado: las recomendaciones de abajo se actualizan (si el problema se arregló, desaparece)
    if need_render or rv:   # Optimizar siempre vuelve a revisar con la IA, aunque la revisión automática esté apagada
        try:
            progress(96, "La IA vuelve a revisar el clip ya optimizado...")
            c2 = load_clip_for_edit(workdir, index)
            fields_ok = {f.name for f in Clip.__dataclass_fields__.values()}
            clip2 = Clip(**{k: v for k, v in c2["clip"].items() if k in fields_ok})
            tr_abs = {"language": None, "segments": _group_words(c2["words"])}
            out = _set_clip_fields(workdir, index, {"review": review_clip(clip2, workdir / "clips" / clip2.file, tr_abs, o)})
        except Cancelled:
            raise
        except Exception:   # noqa: BLE001
            pass
    progress(100, "Clip optimizado.")
    return out


def revert_optimization(workdir: Path, index: int, progress: ProgressFn = _noop) -> dict:
    """Vuelve el clip a como estaba antes de optimizarlo con la IA."""
    data = load_clip_for_edit(workdir, index)
    c = data["clip"]
    prev = c.get("opt_prev")
    if not prev:
        raise RuntimeError("Este clip no tiene una optimización que deshacer.")
    prev = {k: v for k, v in prev.items() if v is not None}
    prev_layout = prev.pop("layout", None)
    need_render = (prev_layout is not None and prev_layout != data["layout"]) or (abs(prev.get("start", c["start"]) - c["start"]) > 0.15 or abs(prev.get("end", c["end"]) - c["end"]) > 0.15
                   or (prev.get("hook") or "") != (c.get("hook") or "") or set(prev.get("keywords") or []) != set(c.get("keywords") or []))
    if need_render:
        edits = dict(prev, show_hook=bool(prev.get("hook")))
        if prev_layout:
            edits["layout"] = prev_layout
        rerender_clip(workdir, index, edits, progress)
    else:
        update_clip_meta(workdir, index, prev)
    out = _set_clip_fields(workdir, index, {"opt_prev": None, "opt_note": None, "opt_pending": None, "optimized": None})
    progress(100, "Optimización deshecha.")
    return out



def delete_clip(workdir: Path, index: int) -> dict:
    res_path = workdir / "result.json"
    res = json.loads(res_path.read_text(encoding="utf-8"))
    keep = []
    for x in res["clips"]:
        if int(x["index"]) == int(index):
            for name in (x.get("file"), x.get("thumb")):
                if name:
                    (workdir / "clips" / name).unlink(missing_ok=True)
            (workdir / "edit" / f"{int(index):02d}.json").unlink(missing_ok=True)
        else:
            keep.append(x)
    res["clips"] = keep
    res_path.write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    return res


# --------------------------------------------------------------------------- #
# 9. Modo en vivo: graba el directo por trozos y saca clips mientras sigue
# --------------------------------------------------------------------------- #
class TwitchChat:
    """Lee el chat público de Twitch (solo lectura) y detecta picos de actividad."""

    def __init__(self, channel: str, host: str = "irc.chat.twitch.tv", port: int = 6697):
        import collections
        self.channel, self.host, self.port = channel.lower().lstrip("#"), host, port
        self.times = collections.deque(maxlen=200000)
        self.ok = False
        self._stop = threading.Event()
        self._t = threading.Thread(target=self._run, daemon=True)
        self._t.start()

    def _run(self) -> None:
        import random
        import socket
        import ssl

        # Prefer IRC over TLS. Fall back to the legacy plaintext port only
        # when TLS cannot be reached; neither mode sends account credentials.
        endpoints = [(6697, True), (6667, False)] if self.port in (6667, 6697) else [(self.port, False)]
        while not self._stop.is_set():
            for port, use_tls in endpoints:
                raw = None
                try:
                    raw = socket.create_connection((self.host, port), timeout=15)
                    conn = ssl.create_default_context().wrap_socket(raw, server_hostname=self.host) if use_tls else raw
                    with conn as s:
                        s.sendall(f"NICK justinfan{random.randint(10000, 99999)}\r\nJOIN #{self.channel}\r\n".encode())
                        s.settimeout(5)
                        buf = b""
                        while not self._stop.is_set():
                            try:
                                data = s.recv(4096)
                            except socket.timeout:
                                continue
                            if not data:
                                break
                            buf += data
                            *lines, buf = buf.split(b"\r\n")
                            for ln in lines:
                                if ln.startswith(b"PING"):
                                    s.sendall(b"PONG" + ln[4:] + b"\r\n")
                                elif b" PRIVMSG #" in ln:
                                    self.ok = True
                                    self.times.append(time.time())
                    break
                except Exception:
                    if raw is not None:
                        try:
                            raw.close()
                        except OSError:
                            pass
            if self._stop.is_set():
                break
            self._stop.wait(5)

    def stop(self) -> None:
        self._stop.set()

    def hot_intervals(self, t0: float, t1: float, bin_s: float = 5.0) -> list:
        """Tramos (reloj real) entre t0 y t1 en los que el chat fue claramente más activo de lo normal."""
        ts = [t for t in list(self.times) if t0 - 600 <= t <= t1]
        if len(ts) < 20:
            return []
        base_t0 = min(ts[0], t0)
        nb = int((t1 - base_t0) / bin_s) + 1
        counts = np.zeros(nb)
        for t in ts:
            counts[int((t - base_t0) / bin_s)] += 1
        pos = counts[counts > 0]
        # nivel normal del chat: la mediana; con poco historial, el cuartil bajo (un pico no debe subir la base)
        med = float(np.percentile(pos, 50 if len(pos) >= 12 else 25)) if len(pos) else 0.0
        thr = max(2.2 * med, med + 4)
        out = []
        for k in np.nonzero(counts >= thr)[0]:
            a = base_t0 + k * bin_s
            if a + bin_s >= t0:
                if out and a - out[-1][1] <= bin_s:
                    out[-1][1] = a + bin_s
                else:
                    out.append([a, a + bin_s])
        return [(a, b) for a, b in out]


# --------------------------------------------------------------------------- #
# Plataformas (YouTube, Twitch, Kick, TikTok)
# --------------------------------------------------------------------------- #
PLATFORM_NAMES = {"youtube": "YouTube", "twitch": "Twitch", "kick": "Kick", "tiktok": "TikTok"}


def platform_of(url: str) -> Optional[str]:
    """'youtube' | 'twitch' | 'kick' | 'tiktok' o None si no es un enlace conocido."""
    u = (url or "").strip().lower()
    if re.search(r"(^|//|\.)(youtube\.com|youtu\.be)(/|$)", u):
        return "youtube"
    if re.search(r"(^|//|\.)twitch\.tv(/|$)", u):
        return "twitch"
    if re.search(r"(^|//|\.)kick\.com(/|$)", u):
        return "kick"
    if re.search(r"(^|//|\.)tiktok\.com(/|$)", u):
        return "tiktok"
    return None


def is_live_url(url: str) -> bool:
    """Enlaces que solo pueden ser un directo: canal de Twitch/Kick o /live de TikTok y YouTube."""
    u = (url or "").strip().lower().split("?")[0].rstrip("/")
    p = platform_of(u)
    path = re.sub(r"^(https?://)?[^/]+", "", u)
    if p == "twitch":
        return bool(re.fullmatch(r"/[a-z0-9_]+", path)) and path not in ("/directory", "/downloads", "/jobs")
    if p == "kick":
        return bool(re.fullmatch(r"/[a-z0-9_\-]+", path)) and path not in ("/categories", "/browse")
    if p == "tiktok":
        return bool(re.fullmatch(r"/@[^/]+/live", path))
    if p == "youtube":
        return bool(re.fullmatch(r"/@[^/]+/live", path))
    return False


def _tiktok_live_api(source: str) -> dict:
    """Plan B para TikTok: pregunta directamente a TikTok si el canal está en vivo y saca la URL del stream.
    Devuelve {"live": True/False/None, "url": str|None, "title": str, "error": str|None}."""
    import urllib.request, urllib.parse
    m = re.search(r"tiktok\.com/@([^/?#]+)", source)
    if not m:
        return {"live": None, "url": None, "title": "", "error": "no se pudo leer el usuario del enlace"}
    user = urllib.parse.unquote(m.group(1))
    ua = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
          "Chrome/126.0.0.0 Safari/537.36")
    api = ("https://www.tiktok.com/api-live/user/room/?aid=1988&app_language=es&app_name=tiktok_web"
           "&device_platform=web_pc&sourceType=54&uniqueId=" + urllib.parse.quote(user))
    try:
        req = urllib.request.Request(api, headers={"User-Agent": ua, "Referer": f"https://www.tiktok.com/@{user}/live",
                                                   "Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=20) as r:
            j = json.loads(r.read().decode("utf-8", "replace"))
    except Exception as e:
        return {"live": None, "url": None, "title": "", "error": str(e)[:120]}
    data = j.get("data") or {}
    status = (data.get("user") or {}).get("status")
    room = data.get("liveRoom") or {}
    title = room.get("title") or f"directo de {user}"
    sd = ((room.get("streamData") or {}).get("pull_data") or {}).get("stream_data")
    url = None
    try:
        streams = (json.loads(sd) if isinstance(sd, str) else (sd or {})).get("data") or {}
        for q in ("origin", "uhd", "hd", "sd", "ld"):
            main = (streams.get(q) or {}).get("main") or {}
            url = main.get("hls") or main.get("flv")
            if url:
                break
    except Exception:
        pass
    live = True if (status == 2 and url) else (False if status in (1, 3, 4) or (status is not None and not url) else None)
    return {"live": live, "url": url, "title": title, "error": None if data else "TikTok no devolvió datos"}


class _QuietLog:
    """Logger mudo para yt-dlp: los intentos fallidos se recogen en `errors`, no se pintan en la terminal."""
    def debug(self, m): pass
    def info(self, m): pass
    def warning(self, m): pass
    def error(self, m): pass


def _live_source(url: str, opts: Options):
    """Entradas de ffmpeg para el directo: (argumentos, título, canal de Twitch o None, mapas de pistas)."""
    if not re.match(r"^https?://", url):          # archivo local: simula un directo (pruebas)
        rate = os.environ.get("NOVOCLIP_LIVE_RATE", "1")
        return ["-readrate", rate, "-i", url], Path(url).stem, None, ["-map", "0:v:0", "-map", "0:a:0?"]
    import yt_dlp
    plat = platform_of(url) or "youtube"
    # YouTube ofrece los directos de varias formas según el "cliente": se prueban formatos y clientes
    # hasta dar con uno que tenga video y audio (juntos o por separado).
    # Primero HLS (m3u8): es lo que ffmpeg puede grabar en continuo, con el audio incluido.
    fmts = ["b[protocol*=m3u8][height<=1080]/bv*[protocol*=m3u8][height<=1080]+ba[protocol*=m3u8]/"
            "b[protocol*=m3u8]/bv*[protocol*=m3u8]+ba[protocol*=m3u8]",
            "bv*[height<=1080][vcodec^=avc1]+ba[acodec^=mp4a]/b[height<=1080][vcodec^=avc1]/"
            "bv*[height<=1080]+ba/b[height<=1080]/bv*+ba/b", None]
    clients = [None, ["ios"], ["tv", "web_safari"], ["mweb"], ["android_vr"], ["web_embedded"]]
    if plat != "youtube":       # Twitch / Kick / TikTok: sin clientes de YouTube; Kick y TikTok piden "navegador"
        clients = ["chrome", None]    # primero simulando un navegador (si no, TikTok/Kick dicen "no está en directo")
    info, errors = None, []
    for fm in fmts:
        for cl in clients:
            o = {"quiet": True, "no_warnings": True, "noplaylist": True, "logger": _QuietLog()}
            if fm:
                o["format"] = fm
            if cl and plat == "youtube":
                o["extractor_args"] = {"youtube": {"player_client": cl}}
            elif cl:
                try:
                    from yt_dlp.networking.impersonate import ImpersonateTarget
                    o["impersonate"] = ImpersonateTarget.from_str(cl)
                except Exception:
                    continue
            o.update(_cookie_opts_now(opts))
            try:
                check_cancel()
                with yt_dlp.YoutubeDL(o) as y:
                    cand = y.extract_info(url, download=False)
                if cand and (cand.get("url") or cand.get("requested_formats")):
                    info = cand
                    break
            except Cancelled:
                raise
            except Exception as e:
                errors.append(re.sub(r"\x1b\[[0-9;]*m", "", str(e))[:140])
        if info:
            break
    if not info and plat == "tiktok":
        tk = _tiktok_live_api(url)
        if tk["live"] and tk["url"]:                 # yt-dlp no lo vio, pero TikTok dice que sí está en vivo
            hdr = "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0 Safari/537.36\r\nReferer: https://www.tiktok.com/\r\n"
            args = ["-headers", hdr, "-reconnect", "1", "-reconnect_streamed", "1", "-reconnect_delay_max", "10", "-i", tk["url"]]
            return args, tk["title"], None, ["-map", "0:v:0", "-map", "0:a:0?"]
        if tk["live"] is False:
            raise RuntimeError("TikTok responde que ese canal no está en directo (desde este equipo). Si sí lo está, abre el directo en "
                               "tu navegador con la sesión iniciada y en 'Cookies' elige ese navegador; si sigue igual, mándame este mensaje.")
        errors.append("plan B de TikTok: " + str(tk.get("error")))
    if not info and plat != "youtube":
        det = "\n  ".join(errors[-3:])
        nombre = PLATFORM_NAMES.get(plat, plat)
        if re.search(r"offline|not live|no está en directo|is not currently live|not currently live", det, re.I):
            raise RuntimeError(f"Ese canal de {nombre} no está en directo ahora mismo. Prueba cuando esté en vivo.")
        raise RuntimeError(
            f"No se pudo abrir el directo de {nombre}.\n"
            "  1) Comprueba que el canal está en vivo ahora mismo.\n"
            "  2) Actualiza el descargador:  .venv\\Scripts\\pip install -U \"yt-dlp[default,curl-cffi]\"\n"
            f"\nDetalle:\n  {det}")
    if not info:
        raise RuntimeError(
            "No se pudo abrir el directo.\n"
            "  1) Instala Deno (YouTube lo exige):  winget install DenoLand.Deno  y reinicia la app.\n"
            "  2) Actualiza el descargador:  .venv\\Scripts\\pip install -U \"yt-dlp[default]\"\n"
            "  3) En 'Cookies de YouTube' elige tu navegador.\n\nDetalle:\n  " + "\n  ".join(errors[-3:]))
    if info.get("is_live") is False or (plat == "youtube" and not info.get("is_live")):
        raise RuntimeError("Ese enlace no está en directo ahora mismo. Para un video ya terminado, "
                           "desmarca 'Directo' y genera los clips de la forma normal.")

    def inp(fmt: dict) -> list:
        hdr = fmt.get("http_headers") or info.get("http_headers") or {}
        a = ["-headers", "".join(f"{k}: {v}\r\n" for k, v in hdr.items())] if hdr else []
        return a + ["-reconnect", "1", "-reconnect_streamed", "1", "-reconnect_delay_max", "10", "-i", fmt["url"]]

    parts = info.get("requested_formats") or [info]
    if len(parts) >= 2:                           # video y audio llegan por separado
        vid = next((x for x in parts if x.get("vcodec") not in (None, "none")), parts[0])
        aud = next((x for x in parts if x is not vid), parts[-1])
        args, maps = inp(vid) + inp(aud), ["-map", "0:v:0", "-map", "1:a:0"]
    else:
        args, maps = inp(parts[0]), ["-map", "0:v:0", "-map", "0:a:0?"]
    m = re.search(r"twitch\.tv/([A-Za-z0-9_]+)", url)
    return args, info.get("title") or "directo", (m.group(1) if m else None), maps


LIVE_SRC_MARGIN = 15.0   # segundos de video guardados antes y después de cada clip de un directo (para poder editarlo)


def _live_keep_source(workdir: Path, chunk: Path, c: Clip, t0_abs: float, chunk_dur: float) -> None:
    """Guarda un trozo del video alrededor del clip y pasa sus palabras al tiempo del directo,
    así el clip se puede editar / optimizar con IA después aunque el directo ya no esté grabándose."""
    try:
        a = max(0.0, c.start - LIVE_SRC_MARGIN)
        b = min(float(chunk_dur), c.end + LIVE_SRC_MARGIN)
        d = workdir / "live_src"
        d.mkdir(exist_ok=True)
        out = d / f"{c.index:02d}.mp4"
        run(["ffmpeg", "-y", "-v", "error", "-ss", f"{a:.3f}", "-to", f"{b:.3f}", "-i", str(chunk),
             "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-c:a", "aac", "-b:a", "160k",
             "-movflags", "+faststart", str(out)])
        (d / f"{c.index:02d}.json").write_text(json.dumps({"off": round(t0_abs + a, 3), "dur": round(b - a, 3)}))
        wf = workdir / "edit" / f"{c.index:02d}.json"
        if wf.exists():
            words = json.loads(wf.read_text(encoding="utf-8"))
            for w in words:
                w["s"] = round(w["s"] + t0_abs, 3)
                w["e"] = round(w["e"] + t0_abs, 3)
            wf.write_text(json.dumps(words, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass   # sin el trozo el clip se ve igual; solo no se podrá volver a editar


def _keep_clip_source(workdir: Path, c: Clip, part: Path, off: float, meta: dict) -> None:
    """Guarda el trozo de video del clip (ya con su margen) en clip_src/ y borra el original temporal."""
    try:
        d = workdir / "clip_src"
        d.mkdir(exist_ok=True)
        dest = d / f"{c.index:02d}{part.suffix.lower() or '.mkv'}"
        shutil.move(str(part), str(dest))
        (d / f"{c.index:02d}.json").write_text(json.dumps({"off": round(off, 3), "dur": round(float(meta["duration"]), 3),
                                                           "file": dest.name}))
    except Exception:
        try:
            part.unlink(missing_ok=True)
        except OSError:
            pass   # en Windows el archivo puede seguir en uso; no debe tapar el error de render


def _live_src(workdir: Path, index: int) -> Optional[tuple]:
    """(video, desfase, duración) del trozo guardado de un clip (directo en live_src/, video normal en clip_src/), o None."""
    for folder in ("live_src", "clip_src"):
        j = workdir / folder / f"{int(index):02d}.json"
        try:
            m = json.loads(j.read_text())
            f = workdir / folder / m.get("file", f"{int(index):02d}.mp4")
            if f.exists():
                return f, float(m["off"]), float(m["dur"])
        except Exception:
            continue
    return None


def process_live(source: str, workdir: Path, opts: Options, progress: ProgressFn = _noop,
                 on_update: Optional[Callable[[dict], None]] = None) -> dict:
    """Graba un directo en trozos y, cada `live_window` segundos, analiza lo nuevo y saca los clips buenos.
    Termina cuando acaba el directo o cuando se cancela (los clips ya hechos se conservan)."""
    from dataclasses import replace
    global _AI_PROVIDER
    _AI_PROVIDER = norm_provider(opts.ai_provider)
    opts = resolve_auto(opts)
    _report = progress

    def progress(pct: float, msg: str) -> None:  # noqa: F811
        check_cancel()
        _report(pct, msg)

    workdir.mkdir(parents=True, exist_ok=True)
    segdir, outdir = workdir / "live", workdir / "clips"
    segdir.mkdir(exist_ok=True)
    outdir.mkdir(exist_ok=True)
    seg = max(5, int(opts.live_segment))
    per = max(1, int(round(opts.live_window / seg)))

    progress(1, "Conectando con el directo...")
    args, title, twitch, maps = _live_source(source, opts)
    chat = None
    if twitch and opts.live_chat:
        try:
            chat = TwitchChat(twitch)
        except Exception:
            chat = None
    result = {"title": title, "live": True, "clips": [], "source": {}, "scene": {}}

    def save() -> None:
        try:   # conservar lo que el usuario cambió desde fuera (editar, gancho, Optimizar con IA) mientras seguía el directo
            disk = json.loads((workdir / "result.json").read_text(encoding="utf-8"))
            by_idx = {int(x["index"]): x for x in disk.get("clips", [])}
            for k, x in enumerate(result["clips"]):
                d = by_idx.get(int(x["index"]))
                if d and (d.get("edited") or d.get("meta_edited") or d.get("optimized") or d.get("rev")):
                    result["clips"][k] = d
        except Exception:
            pass
        (workdir / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        if on_update:
            on_update(result)

    rec_starts: dict = {}   # número del primer trozo de cada grabación -> hora real de inicio

    def start_rec(n0: int):
        cmd = (["ffmpeg", "-y", "-v", "error"] + args +
               maps + ["-c", "copy", "-f", "segment", "-segment_time", str(seg), "-segment_format", "matroska",
                       "-reset_timestamps", "1", "-segment_start_number", str(n0), str(segdir / "seg_%06d.mkv")])
        rec_starts[n0] = time.time()
        return _sp_popen(cmd, stdout=subprocess.DEVNULL, stderr=open(workdir / "recorder.log", "ab"))

    def wall_of(idx: int) -> float:
        n0 = max(k for k in rec_starts if k <= idx)
        return rec_starts[n0] + (idx - n0) * seg

    def num(f: Path) -> int:
        return int(f.stem.split("_")[1])

    rec = start_rec(0)
    next_seg, chunk_n, restarts, last_end_abs, counter = 0, 0, 0, -1e9, 0
    keep_prev: Optional[Path] = None
    scene = None
    t_begin = time.time()
    dry, last_note = 0, ""      # tramos seguidos sin clip y resumen del último análisis
    try:
        while True:
            check_cancel()
            files = sorted(segdir.glob("seg_*.mkv"), key=num)
            alive = rec.poll() is None
            complete = files if not alive else files[:-1]
            pending = [f for f in complete if num(f) >= next_seg]

            if len(pending) >= per or (not alive and pending):
                batch = pending[:per]
                parts = ([keep_prev] if keep_prev and keep_prev.exists() else []) + batch
                t0_abs = num(parts[0]) * seg
                cdir = workdir / f"chunk_{chunk_n:04d}"
                cdir.mkdir(exist_ok=True)
                lst = cdir / "list.txt"
                lst.write_text("".join(f"file '{str(f.resolve()).replace(chr(92), '/')}'\n" for f in parts), encoding="utf-8")
                chunk = cdir / "chunk.mp4"
                tag = f"🔴 Tramo {chunk_n + 1} ({_fmt_clock(t0_abs)}–{_fmt_clock(t0_abs + len(parts) * seg)})"
                progress(5, f"{tag}: preparando...")
                run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy",
                     "-movflags", "+faststart", str(chunk)])
                (cdir / "chunk.json").write_text(json.dumps({"t0": t0_abs, "parts": [f.name for f in parts]}))
                meta = probe(chunk)
                result["source"] = meta
                if not meta["has_audio"]:
                    raise RuntimeError(
                        "El directo se está grabando SIN audio, así que no se puede transcribir.\n"
                        "  1) Instala Deno (YouTube lo exige para dar todos los formatos):  winget install DenoLand.Deno\n"
                        "  2) Actualiza el descargador:  .venv\\Scripts\\pip install -U \"yt-dlp[default]\"\n"
                        "  3) Reinicia la app y vuelve a probar (o prueba con un directo de Twitch).")

                def sub(pct: float, msg: str, tag=tag) -> None:
                    progress(pct, f"{tag}: {msg}")

                tr = transcribe(chunk, cdir, opts, sub)
                if chat is not None and chat.ok:   # picos del chat -> tramos calientes en el tiempo del trozo
                    w0 = wall_of(num(parts[0]))
                    hot = [(max(0.0, a - w0 - 20), b - w0 + 5)
                           for a, b in chat.hot_intervals(w0, w0 + len(parts) * seg)]
                    tr["hot"] = [h for h in hot if h[1] > 0]
                clips = []
                if tr.get("segments"):
                    o = replace(opts, num_clips=max(1, opts.live_clips_per_window))
                    clips = select_clips(chunk, tr, o, title, sub)
                    if ai_backend() and opts.use_ai:
                        # si pasan tramos sin ningún clip, el listón baja 8 puntos por tramo (mínimo 40)
                        thr = max(40, opts.live_min_score - 8 * dry)
                        best = max((c.score for c in clips), default=0)
                        last_note = (f" · último análisis: mejor candidato {best}/100 (mínimo {thr})" if clips
                                     else " · último análisis: la IA no encontró ningún momento")
                        clips = [c for c in clips if c.score >= thr]
                    else:
                        clips = clips[:1]
                    clips = [c for c in clips if t0_abs + c.start >= last_end_abs - 1.0]   # no repetir el solape
                if clips and scene is None and opts.layout == "auto" and opts.use_ai and ai_backend():
                    scene = classify_video(chunk, workdir, opts, meta["duration"])
                    result["scene"] = scene or {}
                for c in sorted(clips, key=lambda c: c.start):
                    counter += 1
                    c.index = counter
                    c = render_clip(chunk, c, tr, opts, outdir, meta, sub, 45, 95, scene=scene)
                    _live_keep_source(workdir, chunk, c, t0_abs, meta["duration"])
                    if opts.review and ai_backend():
                        sub(96, f"Clip {c.index}: la IA está revisando el resultado...")
                        try:
                            c.review = review_clip(c, outdir / c.file, tr, opts)
                        except Exception as e:
                            c.review = {"error": str(e)[:200]}
                    last_end_abs = max(last_end_abs, t0_abs + c.end)
                    d = dict(asdict(c), duration=round(c.out_duration or c.duration, 2))
                    d["start"], d["end"] = round(t0_abs + c.start, 2), round(t0_abs + c.end, 2)   # tiempo del directo
                    result["clips"].append(d)
                    save()
                dry = 0 if clips else dry + 1
                if not clips:
                    sub(97, "nada lo bastante bueno en este tramo; sigo mirando.")
                # limpiar: se conserva el último trozo como solape con el siguiente tramo
                next_seg = num(batch[-1]) + 1
                for f in files:
                    if num(f) < num(batch[-1]):
                        f.unlink(missing_ok=True)
                keep_prev = batch[-1]
                shutil.rmtree(cdir, ignore_errors=True)
                chunk_n += 1
                continue

            if not alive:
                if re.match(r"^https?://", source) and restarts < 5:
                    restarts += 1
                    progress(3, "La señal se cortó; reconectando...")
                    time.sleep(5)
                    try:
                        args, _, _, maps = _live_source(source, opts)
                        rec = start_rec((num(files[-1]) + 1) if files else 0)
                        continue
                    except Cancelled:
                        raise
                    except Exception:
                        pass
                if chunk_n == 0 and not files:   # nunca llegó a grabar nada: decir por qué
                    try:
                        tail = (workdir / "recorder.log").read_text(encoding="utf-8", errors="replace").strip()[-500:]
                    except Exception:
                        tail = ""
                    raise RuntimeError("No se pudo grabar el directo (la señal no llegó).\n" + tail)
                break
            restarts = 0 if len(pending) else restarts
            have = len(pending) * seg
            wait = max(0, per * seg - have)
            chat_txt = " · chat de Twitch conectado" if (chat is not None and chat.ok) else ""
            progress(min(99, 100 * have / (per * seg)),
                     f"🔴 En directo ({_fmt_clock(time.time() - t_begin)}) · {len(result['clips'])} clips · "
                     f"próximo análisis en ~{int(wait)} s{chat_txt}{last_note}")
            time.sleep(1.5)
    finally:
        if chat is not None:
            chat.stop()
        if rec.poll() is None:
            _kill_tree(rec)
        _unregister(rec)
        try:
            (workdir / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass
    _report(100, f"El directo terminó. {len(result['clips'])} clips generados.")
    return result


def _fmt_clock(t: float) -> str:
    t = int(max(0, t))
    return f"{t // 3600}:{t % 3600 // 60:02d}:{t % 60:02d}" if t >= 3600 else f"{t // 60}:{t % 60:02d}"


# --------------------------------------------------------------------------- #
# Diagnóstico: comprueba que todo lo necesario está instalado y funciona
# --------------------------------------------------------------------------- #
def diagnostics(jobs_dir: Optional[Path] = None) -> list:
    """Lista de comprobaciones [{id, name, status: ok|warn|bad, detail, fix}] para la pantalla de Ajustes."""
    import socket
    import concurrent.futures as cf
    out: list = []

    def add(id_, name, status, detail, fix=""):
        out.append({"id": id_, "name": name, "status": status, "detail": detail, "fix": fix})

    def cmd(args: list, timeout: int = 15) -> str:
        try:
            r = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
            return (r.stdout or "") + (r.stderr or "")
        except Exception as e:   # noqa: BLE001
            return f"__error__ {e}"

    # ffmpeg
    ff = shutil.which("ffmpeg")
    if not ff:
        add("ffmpeg", "FFmpeg", "bad", "No está instalado: sin él no se pueden crear los clips.", "winget install Gyan.FFmpeg  (y reinicia la app)")
    else:
        ver = (cmd(["ffmpeg", "-version"]).splitlines() or ["?"])[0][:60]
        enc = cmd(["ffmpeg", "-hide_banner", "-encoders"])
        flt = cmd(["ffmpeg", "-hide_banner", "-filters"])
        miss = [n for n, ok in (("libx264", "libx264" in enc), ("subtítulos (libass)", " ass " in flt or "subtitles" in flt)) if not ok]
        if miss:
            add("ffmpeg", "FFmpeg", "bad", f"{ver}. Le falta: {', '.join(miss)}.", "Instala la versión completa (gyan.dev 'full').")
        else:
            add("ffmpeg", "FFmpeg", "ok", ver)
        gpu = [n for n in ("h264_nvenc", "h264_amf", "h264_qsv") if n in enc]
        add("encoder", "Codificador por GPU", "ok" if gpu else "warn",
            ", ".join(gpu) if gpu else "No hay codificador por GPU disponible: se usa el procesador (más lento).",
            "" if gpu else "Instala los últimos drivers de tu tarjeta gráfica.")
    if not shutil.which("ffprobe"):
        add("ffprobe", "FFprobe", "bad", "No se encuentra ffprobe (viene con FFmpeg).", "Reinstala FFmpeg completo.")

    # yt-dlp y el motor de JavaScript que pide YouTube
    try:
        import yt_dlp
        add("ytdlp", "yt-dlp (descargas)", "ok", f"versión {yt_dlp.version.__version__}")
    except Exception:   # noqa: BLE001
        add("ytdlp", "yt-dlp (descargas)", "bad", "No está instalado.", ".venv\\Scripts\\pip install -U \"yt-dlp[default,curl-cffi]\"")
    js = shutil.which("deno") or shutil.which("node")
    add("js", "Motor de YouTube (Deno)", "ok" if js else "warn",
        js or "No se encontró Deno ni Node: YouTube puede fallar al descargar o abrir directos.", "" if js else "winget install DenoLand.Deno  (y reinicia la app)")
    try:
        import curl_cffi  # noqa: F401
        add("curlcffi", "Kick y TikTok (curl-cffi)", "ok", "instalado")
    except Exception:   # noqa: BLE001
        add("curlcffi", "Kick y TikTok (curl-cffi)", "warn", "No está instalado: Kick y TikTok pueden bloquear la descarga.", ".venv\\Scripts\\pip install -U curl-cffi")

    # transcripción
    try:
        import faster_whisper  # noqa: F401
        add("whisper", "Transcripción (faster-whisper)", "ok", "instalado")
    except Exception:   # noqa: BLE001
        add("whisper", "Transcripción (faster-whisper)", "bad", "No está instalado.", ".venv\\Scripts\\pip install -r requirements.txt")
    wc = whispercpp_exe()
    add("whispercpp", "Transcripción con GPU AMD (Vulkan)", "ok" if wc else "warn",
        wc or "No está compilado: se transcribe con el procesador (más lento).", "" if wc else "Ejecuta compilar_whisper_vulkan.bat")
    try:
        add("opencv", "Visión (OpenCV)", "ok", f"versión {cv2.__version__}")
    except Exception as e:   # noqa: BLE001
        add("opencv", "Visión (OpenCV)", "bad", str(e)[:80], "pip install \"opencv-python-headless<5\"")

    # IA
    b = ai_backend()
    add("ai", "Inteligencia artificial", "ok" if b else "warn", backend_name(b) if b else "Sin IA: se usa el método básico para elegir clips.",
        "" if b else "Pega tu clave de Gemini o Claude en Ajustes → IA.")

    # disco, música y fuentes
    try:
        free = shutil.disk_usage(str(jobs_dir or ROOT)).free / 1e9
        add("disk", "Espacio en disco", "ok" if free > 10 else ("warn" if free > 3 else "bad"), f"{free:.0f} GB libres",
            "" if free > 10 else "Libera espacio: los videos en 4K pesan mucho.")
    except Exception:   # noqa: BLE001
        pass
    songs = [p for p in MUSIC_DIR.glob("*") if p.suffix.lower() in (".mp3", ".m4a", ".wav", ".ogg")] if MUSIC_DIR.exists() else []
    add("music", "Música de fondo", "ok" if songs else "warn", f"{len(songs)} canciones en music/" if songs else "La carpeta music/ está vacía: la opción Música no hará nada.",
        "" if songs else "Pon canciones libres de derechos (.mp3) en la carpeta music/.")

    # conexión con cada plataforma
    def reach(host: str):
        try:
            socket.create_connection((host, 443), timeout=4).close()
            return host, True
        except Exception:   # noqa: BLE001
            return host, False

    nets = {"www.youtube.com": "YouTube", "www.twitch.tv": "Twitch", "kick.com": "Kick", "www.tiktok.com": "TikTok"}
    with cf.ThreadPoolExecutor(4) as ex:
        res = dict(ex.map(reach, nets))
    for host, name in nets.items():
        add("net_" + name.lower(), f"Conexión con {name}", "ok" if res[host] else "bad",
            "llega" if res[host] else "No se puede conectar.", "" if res[host] else "Revisa tu internet, VPN o antivirus.")
    return out


# --------------------------------------------------------------------------- #
# Vista previa rápida del encuadre (10 s) antes de generar todos los clips
# --------------------------------------------------------------------------- #
def preview_framing(source: str, workdir: Path, opts: Options, at: float = 0.35, seconds: float = 10.0,
                    progress: ProgressFn = _noop) -> dict:
    """Crea un clip de muestra de ~10 s con el encuadre y los efectos elegidos (sin subtítulos ni IA de selección),
    para ver cómo quedará antes de procesar el video entero. `at` = posición del video (0-1)."""
    global _AI_PROVIDER
    _AI_PROVIDER = norm_provider(opts.ai_provider)
    o = resolve_auto(replace(opts, caption_style="none", show_hook=False, music=False, review=False, loudnorm=False))
    workdir.mkdir(parents=True, exist_ok=True)
    outdir = workdir / "clips"
    outdir.mkdir(exist_ok=True)
    at = min(0.95, max(0.02, float(at)))
    is_url = bool(re.match(r"^https?://", source))
    part: Optional[Path] = None
    if is_url:
        import yt_dlp
        progress(5, "Mirando el video...")
        q = {"quiet": True, "no_warnings": True, "noplaylist": True}
        info = yt_run(q, o, lambda y: y.extract_info(source, download=False), progress)
        if info.get("is_live"):
            raise RuntimeError("La vista previa no funciona con directos. Genera los clips y edita el encuadre de cada uno.")
        dur = float(info.get("duration") or 0)
        if dur < seconds + 2:
            raise RuntimeError("No pude saber la duración de este video para sacar una muestra.")
        t0 = max(0.0, min(dur * at, dur - seconds - 2))
        progress(15, f"Descargando una muestra de {seconds:.0f} s (minuto {t0 / 60:.1f})...")
        part, _ = download(source, workdir, o, progress, section=(t0, t0 + seconds + 2), stem="muestra",
                           label="Descargando la muestra...")
        src, c_start = part, 1.0
    else:
        src = Path(source)
        dur = float(probe(src)["duration"])
        if dur < 2:
            raise RuntimeError("El video es demasiado corto para una muestra.")
        seconds = min(seconds, max(1.0, dur - 0.5))
        t0 = max(0.0, min(dur * at, dur - seconds - 0.2))
        c_start = t0
    meta = probe(src)
    clip = Clip(index=1, start=c_start, end=c_start + seconds, title="Vista previa del encuadre")
    scene = None
    if o.layout == "auto" and o.use_ai and ai_backend():
        try:
            progress(35, "La IA mira qué tipo de video es...")
            scene = classify_video(src, workdir, o, float(meta["duration"])) or None
        except Cancelled:
            raise
        except Exception:   # noqa: BLE001
            scene = None
    progress(45, "Creando la muestra...")
    c = render_clip(src, clip, {"language": None, "segments": []}, o, outdir, meta, progress, 45, 98, scene=scene)
    if part:
        part.unlink(missing_ok=True)
    progress(100, "Muestra lista.")
    return dict(asdict(c), duration=round(c.out_duration or c.duration, 2), rev=int(time.time()),
                moment=round(t0, 1), scene_type=(scene or {}).get("tipo"))


def gemini_models() -> list:
    """Modelos de Gemini que puede usar la clave guardada (los que sirven para generar texto), recomendados primero."""
    key = gemini_key()
    if not key:
        raise RuntimeError("Primero guarda tu clave de Gemini.")
    try:
        from google import genai
    except ImportError:
        raise RuntimeError("Falta la librería de Gemini: ejecuta  .venv\\Scripts\\pip install google-genai")
    try:
        client = genai.Client(api_key=key)
        out = []
        for m in client.models.list():
            acts = getattr(m, "supported_actions", None) or []
            name = (getattr(m, "name", "") or "").replace("models/", "")
            if "generateContent" not in acts or not name.startswith("gemini"):
                continue
            if any(x in name for x in GEMINI_SKIP):
                continue
            out.append({"name": name, "label": getattr(m, "display_name", "") or name,
                        "description": (getattr(m, "description", "") or "")[:140],
                        "limit": getattr(m, "input_token_limit", None)})
    except Exception as e:   # noqa: BLE001
        raise RuntimeError(f"Google no respondió ({str(e)[:160]}). Revisa que la clave sea correcta.")

    return sorted(out, key=lambda m: gemini_rank(m["name"]))
