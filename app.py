"""NovoClip - servidor web. Ejecuta:  python app.py   y abre http://localhost:8000"""
from __future__ import annotations

import os
import shutil
import threading
import time
import traceback
import uuid
from dataclasses import fields
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

import pipeline
from pipeline import Options

ROOT = Path(__file__).resolve().parent
JOBS_DIR = ROOT / "jobs"
JOBS_DIR.mkdir(exist_ok=True)

app = FastAPI(title="NovoClip")


@app.middleware("http")
async def _no_cache_pages(request: Request, call_next):
    """Las páginas de la app no se cachean (así una actualización se ve al recargar); los archivos
    versionados de /_next sí."""
    resp = await call_next(request)
    p = request.url.path
    if not p.startswith("/_next") and not p.startswith("/files/"):
        resp.headers["Cache-Control"] = "no-cache"
    return resp
JOBS: dict[str, dict] = {}
LOCK = threading.Semaphore(int(os.environ.get("NOVOCLIP_WORKERS", "1")))


def _worker(job_id: str, source: str, opts: Options) -> None:
    job = JOBS[job_id]

    def progress(p: float, msg: str) -> None:
        job["progress"], job["message"] = round(p, 1), msg
        if not job["log"] or job["log"][-1] != msg:
            job["log"].append(msg)
            job["log"] = job["log"][-200:]

    with LOCK:
        if job.get("cancel_requested"):
            job.update(status="cancelled", message="Generación cancelada.")
            return
        job["ident"] = pipeline.begin_job()
        job["status"] = "running"
        try:
            if job.get("live"):
                job["status"] = "live"
                job["result"] = {"title": "Directo", "clips": [], "live": True}
                res = pipeline.process_live(source, JOBS_DIR / job_id, opts, progress,
                                            on_update=lambda r: job.update(result=dict(r, clips=list(r["clips"]))))
                job.update(status="done", result=res, progress=100,
                           message=f"El directo terminó. {len(res['clips'])} clips generados.")
            else:
                res = pipeline.process(source, JOBS_DIR / job_id, opts, progress,
                                       on_update=lambda r: job.update(result=r))
                job.update(status="done", result=res, progress=100)
        except pipeline.Cancelled:
            if job.get("live"):   # detener un directo conserva los clips ya hechos
                n = len((job.get("result") or {}).get("clips", []))
                job.update(status="done", progress=100, message=f"Directo detenido. {n} clips generados.")
            else:
                job.update(status="cancelled", message="Generación cancelada.")
        except Exception as e:
            if job.get("cancel_requested"):
                job.update(status="cancelled", message="Generación cancelada.")
            else:
                traceback.print_exc()
                tb = traceback.extract_tb(e.__traceback__)
                where = f"\n[{type(e).__name__} en {Path(tb[-1].filename).name}:{tb[-1].lineno}, {tb[-1].name}]" if tb else ""
                own = next((t for t in reversed(tb) if Path(t.filename).name in ("pipeline.py", "app.py")), None)
                if own and own is not tb[-1]:
                    where += f" [desde pipeline.py:{own.lineno}, {own.name}]"
                job.update(status="error", message=str(e)[:1500] + where)
        finally:
            pipeline.end_job()
            _cleanup_partial(JOBS_DIR / job_id)


RETENTION_DAYS = float(os.environ.get("NOVOCLIP_RETENTION_DAYS", "5"))   # los proyectos se borran solos a los 5 días


def _job_age_ref(wd: Path) -> float:
    """Fecha de referencia de un proyecto: la última vez que se tocó su resultado."""
    ts = [wd.stat().st_mtime]
    for name in ("result.json", "job.json"):
        try:
            ts.append((wd / name).stat().st_mtime)
        except OSError:
            pass
    return max(ts)


def purge_expired() -> int:
    """Borra los proyectos con más de RETENTION_DAYS días (los que siguen trabajando no se tocan)."""
    if RETENTION_DAYS <= 0 or not JOBS_DIR.exists():
        return 0
    limit, n = time.time() - RETENTION_DAYS * 86400, 0
    for wd in JOBS_DIR.iterdir():
        try:
            job = JOBS.get(wd.name)
            if not wd.is_dir() or (job and job["status"] in ("queued", "running", "live")):
                continue
            if _job_age_ref(wd) < limit:
                shutil.rmtree(wd, ignore_errors=True)
                JOBS.pop(wd.name, None)
                n += 1
        except Exception:
            continue
    if n:
        print(f"  Limpieza automática: {n} proyecto(s) con más de {RETENTION_DAYS:g} días borrados.")
    return n


def _purge_loop() -> None:
    while True:
        purge_expired()
        time.sleep(3600)


threading.Thread(target=_purge_loop, daemon=True).start()


def _cleanup_partial(wd: Path) -> None:
    """Borra los archivos temporales a medias (los clips terminados se quedan)."""
    clips = wd / "clips"
    if clips.exists():
        for f in clips.glob(".*"):
            try:
                f.unlink()
            except OSError:
                pass


def _opts(**kw) -> Options:
    names = {f.name for f in fields(Options)}
    return Options(**{k: v for k, v in kw.items() if k in names and v is not None and v != ""})


@app.post("/api/jobs")
async def create_job(
    url: str = Form(""),
    file: Optional[UploadFile] = File(None),
    logo: Optional[UploadFile] = File(None),
    logo_pos: str = Form("br"),
    logo_size: float = Form(16),
    logo_opacity: float = Form(80),
    num_clips: int = Form(5),
    min_len: float = Form(20),
    max_len: float = Form(60),
    aspect: str = Form("9:16"),
    layout: str = Form("auto"),
    caption_style: str = Form("viral"),
    words_per_line: int = Form(3),
    font: str = Form("Arial Black"),
    show_hook: bool = Form(True),
    language: str = Form(""),
    whisper_model: str = Form("auto"),
    use_ai: bool = Form(True),
    ai_provider: str = Form("auto"),
    smart_download: bool = Form(True),
    use_captions: bool = Form(True),
    crf: int = Form(16),
    source_quality: str = Form("max"),
    review: bool = Form(True),
    jumpcuts: bool = Form(True),
    zoom: bool = Form(True),
    progress_bar: bool = Form(True),
    color_pop: bool = Form(True),
    music: bool = Form(True),
    highlight_keywords: bool = Form(True),
    loudnorm: bool = Form(True),
    refine: bool = Form(True),
    complete_ideas: bool = Form(True),
    snap_silence: bool = Form(True),
    live: bool = Form(False),
    live_window: int = Form(180),
    device: str = Form("auto"),
    speed: str = Form("auto"),
):
    if not url and not file:
        raise HTTPException(400, "Pega un enlace (YouTube, Twitch, Kick o TikTok) o sube un video.")
    if min_len >= max_len:
        raise HTTPException(400, "La duración mínima debe ser menor que la máxima.")
    job_id = uuid.uuid4().hex[:10]
    wd = JOBS_DIR / job_id
    wd.mkdir(parents=True)
    source = url.strip()
    if file and file.filename:
        import re as _re
        stem = _re.sub(r"[^\w\- ]", "", Path(file.filename).stem, flags=_re.U).strip()[:60] or "video"
        dest = wd / (stem + Path(file.filename).suffix.lower())   # el título del proyecto sale del nombre del archivo
        with dest.open("wb") as f:
            shutil.copyfileobj(file.file, f)
        source = str(dest)
    logo_path = ""
    if logo and logo.filename:      # Kit de marca: el logo se guarda con el trabajo y se pone como marca de agua
        ext = Path(logo.filename).suffix.lower()
        if ext not in (".png", ".jpg", ".jpeg", ".webp"):
            raise HTTPException(400, "El logo tiene que ser una imagen PNG, JPG o WebP.")
        data = logo.file.read(5 * 1024 * 1024 + 1)
        if len(data) > 5 * 1024 * 1024:
            raise HTTPException(400, "El logo pesa más de 5 MB.")
        lp = wd / ("logo" + ext)
        lp.write_bytes(data)
        logo_path = str(lp)
    opts = _opts(logo_path=logo_path, logo_pos=logo_pos if logo_pos in ("tl", "tr", "bl", "br", "center") else "br",
                 logo_size=max(4.0, min(float(logo_size), 60.0)), logo_opacity=max(5.0, min(float(logo_opacity), 100.0)),
                 num_clips=max(1, min(num_clips, 30)), min_len=min_len, max_len=max_len, aspect=aspect,
                 layout=layout, caption_style=caption_style, words_per_line=words_per_line, font=font,
                 show_hook=show_hook, language=language or None, whisper_model=whisper_model,
                 use_ai=use_ai, ai_provider=ai_provider, smart_download=smart_download,
                 source_quality=source_quality if source_quality in ("max", "1080") else "max", use_captions=use_captions, crf=crf, review=review, jumpcuts=jumpcuts, zoom=zoom,
                 progress_bar=progress_bar, color_pop=color_pop, music=music, highlight_keywords=highlight_keywords,
                 loudnorm=loudnorm, refine=refine, complete_ideas=complete_ideas, snap_silence=snap_silence,
                 device=device if device in ("auto", "gpu", "cpu") else "auto",
                 speed=speed if speed in ("rapido", "normal", "calidad", "auto") else "auto",
                 live_window=max(60, min(int(live_window), 1800)))
    if not (file and file.filename) and pipeline.is_live_url(source):
        live = True                      # canal de Twitch/Kick o TikTok /live: solo puede ser un directo
    JOBS[job_id] = {"id": job_id, "status": "queued", "progress": 0, "message": "En cola...", "log": [], "live": bool(live),
                    "source": url or (file.filename if file else ""), "created": time.time(), "result": None}
    threading.Thread(target=_worker, args=(job_id, source, opts), daemon=True).start()
    return {"id": job_id}


@app.post("/api/preview")
async def create_preview(
    url: str = Form(""),
    file: Optional[UploadFile] = File(None),
    layout: str = Form("auto"),
    aspect: str = Form("9:16"),
    zoom: bool = Form(True),
    jumpcuts: bool = Form(True),
    color_pop: bool = Form(True),
    progress_bar: bool = Form(True),
    use_ai: bool = Form(True),
    ai_provider: str = Form("auto"),
    source_quality: str = Form("max"),
    at: float = Form(0.35),
):
    """Muestra de ~10 s con el encuadre elegido, para verla antes de generar todos los clips."""
    if not url and not (file and file.filename):
        raise HTTPException(400, "Pega un enlace o sube un video para la vista previa.")
    for old in JOBS_DIR.glob("pv_*"):      # una sola muestra a la vez: se borran las anteriores
        shutil.rmtree(old, ignore_errors=True)
    pid = "pv_" + uuid.uuid4().hex[:8]
    wd = JOBS_DIR / pid
    wd.mkdir(parents=True)
    source = url.strip()
    if file and file.filename:
        dest = wd / ("origen" + Path(file.filename).suffix.lower())
        with dest.open("wb") as f:
            shutil.copyfileobj(file.file, f)
        source = str(dest)
    opts = _opts(layout=layout, aspect=aspect, zoom=zoom, jumpcuts=jumpcuts, color_pop=color_pop, progress_bar=progress_bar,
                 use_ai=use_ai, ai_provider=ai_provider,
                 source_quality=source_quality if source_quality in ("max", "1080") else "max")
    JOBS[pid] = {"id": pid, "status": "queued", "progress": 0, "message": "En cola...", "log": [], "result": None,
                 "source": url or (file.filename if file else ""), "created": time.time()}

    def work() -> None:
        job = JOBS[pid]

        def progress(p: float, msg: str) -> None:
            job["progress"], job["message"] = round(p, 1), msg

        with LOCK:
            if job.get("cancel_requested"):
                job.update(status="cancelled", message="Cancelado.")
                return
            job["ident"] = pipeline.begin_job()
            job["status"] = "running"
            try:
                clip = pipeline.preview_framing(source, wd, opts, at=at, progress=progress)
                job.update(status="done", progress=100, message="Muestra lista.",
                           result={"title": "Vista previa", "clips": [clip], "source": {}, "scene": {}})
            except pipeline.Cancelled:
                job.update(status="cancelled", message="Cancelado.")
            except Exception as e:
                traceback.print_exc()
                job.update(status="error", message=str(e)[:600])
            finally:
                pipeline.end_job()
                _cleanup_partial(wd)

    threading.Thread(target=work, daemon=True).start()
    return {"id": pid}


@app.post("/api/jobs/{job_id}/cancel")
def cancel_job(job_id: str):
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(404, "Trabajo no encontrado")
    if job["status"] in ("done", "error", "cancelled"):
        return {"status": job["status"]}
    job["cancel_requested"] = True
    job["message"] = "Cancelando..."
    if job.get("ident"):
        pipeline.cancel_thread(job["ident"])
    return {"status": "cancelling"}


def _job_from_disk(job_id: str) -> Optional[dict]:
    """Reconstruye un trabajo desde su carpeta (así los proyectos sobreviven a reiniciar la app)."""
    import json
    wd = (JOBS_DIR / job_id).resolve()
    if not str(wd).startswith(str(JOBS_DIR.resolve())) or not wd.is_dir():
        return None
    result, info = None, {}
    for name, target in (("result.json", "r"), ("job.json", "i")):
        try:
            data = json.loads((wd / name).read_text(encoding="utf-8"))
        except Exception:
            continue
        if target == "r":
            result = data
        else:
            info = data
    created = wd.stat().st_mtime
    if (wd / "job.json").exists():
        created = (wd / "job.json").stat().st_ctime
    if result is not None:
        status, msg = "done", f"{len(result.get('clips', []))} clips generados."
    else:
        status, msg = "error", "Este trabajo se interrumpió (la app se cerró mientras trabajaba)."
    return {"id": job_id, "status": status, "progress": 100 if result is not None else 0, "message": msg, "log": [],
            "live": bool(result and result.get("live")), "created": created,
            "source": (info.get("source", "") if str(info.get("source", "")).startswith("http") else Path(str(info.get("source", ""))).name),
            "result": result}


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str):
    if job_id in JOBS:
        return JOBS[job_id]
    job = _job_from_disk(job_id)
    if job is None:
        raise HTTPException(404, "Trabajo no encontrado")
    return job


@app.get("/api/projects")
def list_projects():
    """Todos los trabajos (los de ahora y los guardados en disco), del más nuevo al más viejo."""
    ids = {j for j in JOBS if "-e" not in j and not j.startswith("pv_")}
    if JOBS_DIR.exists():
        ids |= {p.name for p in JOBS_DIR.iterdir() if p.is_dir() and (p / "result.json").exists()}
    out = []
    for jid in ids:
        job = JOBS.get(jid) or _job_from_disk(jid)
        if not job:
            continue
        res = job.get("result") or {}
        state = job["status"]
        if state in ("live", "cancelled"):
            state = "running" if state == "live" else "error"
        if state == "done" and not res.get("clips"):
            state = "empty"
        exp = None
        if RETENTION_DAYS > 0 and state not in ("running", "queued"):
            try:
                exp = int((_job_age_ref(JOBS_DIR / jid) + RETENTION_DAYS * 86400) * 1000)
            except OSError:
                pass
        out.append({"jobId": jid, "addedAt": int(job["created"] * 1000), "job": job, "state": state, "expiresAt": exp})
    out.sort(key=lambda p: p["addedAt"], reverse=True)
    return out


@app.delete("/api/jobs/{job_id}")
def delete_job(job_id: str):
    """Borra un proyecto y sus archivos (si todavía está trabajando, primero lo cancela)."""
    job = JOBS.get(job_id)
    if job and job["status"] in ("queued", "running", "live"):
        job["cancel_requested"] = True
        if job.get("ident"):
            pipeline.cancel_thread(job["ident"])
    wd = (JOBS_DIR / job_id).resolve()
    if not str(wd).startswith(str(JOBS_DIR.resolve())) or wd == JOBS_DIR.resolve():
        raise HTTPException(400, "Trabajo no válido")
    if wd.is_dir():
        shutil.rmtree(wd, ignore_errors=True)
    JOBS.pop(job_id, None)
    return {"ok": True}


@app.post("/api/settings")
def settings(gemini_key: str = Form(None), gemini_model: str = Form(None), ai_mode: str = Form(None),
             license_key: str = Form(None), anthropic_key: str = Form(None), ai_source: str = Form(None)):
    """Guarda la configuración de IA en config.json (solo en este equipo)."""
    changes = {}
    for k, v in (("gemini_key", gemini_key), ("gemini_model", gemini_model), ("license_key", license_key),
                 ("anthropic_key", anthropic_key)):
        if v is not None:
            changes[k] = v.strip()
    if ai_mode in ("incluida", "propia"):
        changes["ai_mode"] = ai_mode
    if ai_source in pipeline.AI_SOURCES:
        changes["ai_source"] = ai_source
    pipeline.save_config(**changes)
    return config()


@app.get("/api/config")
def config(refresh: int = 0):
    hw = pipeline.hw_info(refresh=bool(refresh))
    prof = pipeline.system_profile(refresh=bool(refresh))
    return {"ai": pipeline.ai_backend(), "ai_mode": pipeline.ai_mode(), "ai_source": pipeline.ai_source(), "ai_sources": pipeline.ai_sources_status(), "ai_name": pipeline.backend_name(pipeline.ai_backend()),
            "included": pipeline.included_status(), "license": bool(pipeline.license_key()),
            "claude": pipeline.claude_backend(), "anthropic": bool(pipeline.anthropic_key()),
            "gemini": bool(pipeline.gemini_key()), "gemini_model": pipeline.gemini_model(), "dev": pipeline.dev_mode(),
            "hw": hw, "profile": prof, "styles": list(pipeline.STYLES) + ["none"],
            "aspects": list(pipeline.ASPECTS)}


@app.get("/api/diagnostics")
def diagnostics():
    return pipeline.diagnostics(JOBS_DIR)


@app.get("/files/{job_id}/{name}")
def get_file(job_id: str, name: str, download: int = 0):
    p = (JOBS_DIR / job_id / "clips" / name).resolve()
    if not str(p).startswith(str(JOBS_DIR.resolve())) or not p.exists():
        raise HTTPException(404)
    return FileResponse(p, filename=name if download else None)


# ------------------------------- editor de cortes -------------------------------
def _job_dir(job_id: str) -> Path:
    wd = (JOBS_DIR / job_id).resolve()
    if not str(wd).startswith(str(JOBS_DIR.resolve())) or not (wd / "result.json").exists():
        raise HTTPException(404, "Trabajo no encontrado")
    return wd


def _refresh_result(job_id: str) -> dict:
    import json
    res = json.loads((_job_dir(job_id) / "result.json").read_text(encoding="utf-8"))
    if job_id in JOBS:
        JOBS[job_id]["result"] = res
    return res


@app.get("/api/jobs/{job_id}/clips/{index}")
def clip_for_edit(job_id: str, index: int):
    try:
        return pipeline.load_clip_for_edit(_job_dir(job_id), index)
    except KeyError:
        raise HTTPException(404, "Clip no encontrado")


@app.post("/api/jobs/{job_id}/clips/{index}/render")
async def clip_rerender(job_id: str, index: int, request: Request):
    wd = _job_dir(job_id)
    edits = await request.json()
    sub = f"{job_id}-e{index}-{uuid.uuid4().hex[:4]}"
    JOBS[sub] = {"id": sub, "status": "queued", "progress": 0, "message": "En cola...", "log": [], "result": None,
                 "created": time.time()}

    def work() -> None:
        job = JOBS[sub]

        def progress(p: float, msg: str) -> None:
            job["progress"], job["message"] = round(p, 1), msg

        with LOCK:
            if job.get("cancel_requested"):
                job.update(status="cancelled", message="Cancelado.")
                return
            job["ident"] = pipeline.begin_job()
            job["status"] = "running"
            try:
                pipeline.rerender_clip(wd, index, edits, progress)
                job.update(status="done", progress=100, result=_refresh_result(job_id))
            except pipeline.Cancelled:
                job.update(status="cancelled", message="Cancelado.")
            except Exception as e:
                traceback.print_exc()
                job.update(status="error", message=str(e)[:800])
            finally:
                pipeline.end_job()
                _cleanup_partial(wd)

    threading.Thread(target=work, daemon=True).start()
    return {"id": sub}


@app.delete("/api/jobs/{job_id}/clips/{index}")
def clip_delete(job_id: str, index: int):
    pipeline.delete_clip(_job_dir(job_id), index)
    return _refresh_result(job_id)


@app.get("/api/jobs/{job_id}/zip")
def get_zip(job_id: str):
    """Todos los clips del trabajo en un solo .zip (con un .txt de título, descripción y hashtags)."""
    import io
    import json
    import zipfile
    from fastapi.responses import Response

    clips = (JOBS_DIR / job_id / "clips").resolve()
    if not str(clips).startswith(str(JOBS_DIR.resolve())) or not clips.exists():
        raise HTTPException(404)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_STORED) as z:
        for f in sorted(clips.glob("*.mp4")):
            z.write(f, f.name)
        res = JOBS_DIR / job_id / "result.json"
        if res.exists():
            data = json.loads(res.read_text(encoding="utf-8"))
            txt = "\n\n".join(f"{c['file']}\n{c['title']}\n{c.get('caption', '')}\n{' '.join(c.get('hashtags', []))}"
                              for c in data.get("clips", []))
            z.writestr("textos_para_publicar.txt", txt)
    return Response(buf.getvalue(), media_type="application/zip",
                    headers={"Content-Disposition": f'attachment; filename="clips_{job_id}.zip"'})


INDEX = ROOT / "static" / "index.html"
WEB = ROOT / "web"          # diseño nuevo (NovoClip), ya compilado


@app.get("/classic", response_class=HTMLResponse)
@app.get("/classic/", response_class=HTMLResponse)
def classic():
    if not INDEX.exists():
        return HTMLResponse("<h2>Falta static/index.html</h2>", status_code=500)
    return HTMLResponse(INDEX.read_text(encoding="utf-8"))


if (ROOT / "static").exists():
    app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")

if (WEB / "index.html").exists():
    app.mount("/", StaticFiles(directory=WEB, html=True), name="web")
else:
    @app.get("/", response_class=HTMLResponse)
    @app.get("/index.html", response_class=HTMLResponse)
    def index():
        return classic()


def _free_port(start: int) -> int:
    import socket
    for port in range(start, start + 50):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    return start


class _IgnoreWinReset(__import__("logging").Filter):
    """Windows: el navegador cierra una conexión y asyncio avisa con un ConnectionResetError inofensivo."""
    def filter(self, record) -> bool:
        ei = record.exc_info
        return not (ei and isinstance(ei[1], ConnectionResetError))


if __name__ == "__main__":
    import logging
    import webbrowser

    logging.getLogger("asyncio").addFilter(_IgnoreWinReset())
    import uvicorn

    wanted = int(os.environ.get("PORT", "8000"))
    port = _free_port(wanted)
    if port != wanted:
        print(f"  El puerto {wanted} está ocupado por otro programa, uso el {port}.")
    url = f"http://localhost:{port}"
    print(f"\n  NovoClip listo ->  {url}\n  (deja esta ventana abierta mientras usas la app)\n")
    if not os.environ.get("NOVOCLIP_NO_BROWSER"):
        threading.Timer(1.5, lambda: webbrowser.open(url)).start()
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")
