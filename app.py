"""ClipForge - servidor web. Ejecuta:  python app.py   y abre http://localhost:8000"""
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

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

import pipeline
from pipeline import Options

ROOT = Path(__file__).resolve().parent
JOBS_DIR = ROOT / "jobs"
JOBS_DIR.mkdir(exist_ok=True)

app = FastAPI(title="ClipForge")
JOBS: dict[str, dict] = {}
LOCK = threading.Semaphore(int(os.environ.get("CLIPFORGE_WORKERS", "1")))


def _worker(job_id: str, source: str, opts: Options) -> None:
    job = JOBS[job_id]

    def progress(p: float, msg: str) -> None:
        job["progress"], job["message"] = round(p, 1), msg
        if not job["log"] or job["log"][-1] != msg:
            job["log"].append(msg)
            job["log"] = job["log"][-200:]

    with LOCK:
        job["status"] = "running"
        try:
            res = pipeline.process(source, JOBS_DIR / job_id, opts, progress)
            job.update(status="done", result=res, progress=100)
        except Exception as e:
            traceback.print_exc()
            job.update(status="error", message=str(e)[:1500])


def _opts(**kw) -> Options:
    names = {f.name for f in fields(Options)}
    return Options(**{k: v for k, v in kw.items() if k in names and v is not None and v != ""})


@app.post("/api/jobs")
async def create_job(
    url: str = Form(""),
    file: Optional[UploadFile] = File(None),
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
    whisper_model: str = Form("small"),
    use_ai: bool = Form(True),
    crf: int = Form(18),
    review: bool = Form(True),
):
    if not url and not file:
        raise HTTPException(400, "Pega una URL de YouTube o sube un video.")
    if min_len >= max_len:
        raise HTTPException(400, "La duración mínima debe ser menor que la máxima.")
    job_id = uuid.uuid4().hex[:10]
    wd = JOBS_DIR / job_id
    wd.mkdir(parents=True)
    source = url.strip()
    if file and file.filename:
        dest = wd / ("upload" + Path(file.filename).suffix.lower())
        with dest.open("wb") as f:
            shutil.copyfileobj(file.file, f)
        source = str(dest)
    opts = _opts(num_clips=max(1, min(num_clips, 30)), min_len=min_len, max_len=max_len, aspect=aspect,
                 layout=layout, caption_style=caption_style, words_per_line=words_per_line, font=font,
                 show_hook=show_hook, language=language or None, whisper_model=whisper_model,
                 use_ai=use_ai, crf=crf, review=review)
    JOBS[job_id] = {"id": job_id, "status": "queued", "progress": 0, "message": "En cola...", "log": [],
                    "source": url or (file.filename if file else ""), "created": time.time(), "result": None}
    threading.Thread(target=_worker, args=(job_id, source, opts), daemon=True).start()
    return {"id": job_id}


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str):
    if job_id not in JOBS:
        raise HTTPException(404, "Trabajo no encontrado")
    return JOBS[job_id]


@app.get("/api/config")
def config():
    return {"ai": bool(os.environ.get("ANTHROPIC_API_KEY")), "styles": list(pipeline.STYLES) + ["none"],
            "aspects": list(pipeline.ASPECTS)}


@app.get("/files/{job_id}/{name}")
def get_file(job_id: str, name: str, download: int = 0):
    p = (JOBS_DIR / job_id / "clips" / name).resolve()
    if not str(p).startswith(str(JOBS_DIR.resolve())) or not p.exists():
        raise HTTPException(404)
    return FileResponse(p, filename=name if download else None)


INDEX = ROOT / "static" / "index.html"


@app.get("/", response_class=HTMLResponse)
@app.get("/index.html", response_class=HTMLResponse)
def index():
    if not INDEX.exists():
        return HTMLResponse(
            f"<h2>Falta el archivo de la interfaz</h2><p>No se encontró <code>{INDEX}</code>.</p>"
            "<p>Vuelve a descomprimir <b>todo</b> el zip (incluida la carpeta <code>static</code>) y reinicia.</p>",
            status_code=500)
    return HTMLResponse(INDEX.read_text(encoding="utf-8"))


if (ROOT / "static").exists():
    app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")


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


if __name__ == "__main__":
    import webbrowser
    import uvicorn

    wanted = int(os.environ.get("PORT", "8000"))
    port = _free_port(wanted)
    if port != wanted:
        print(f"  El puerto {wanted} está ocupado por otro programa, uso el {port}.")
    url = f"http://localhost:{port}"
    print(f"\n  ClipForge listo ->  {url}\n  (deja esta ventana abierta mientras usas la app)\n")
    if not os.environ.get("CLIPFORGE_NO_BROWSER"):
        threading.Timer(1.5, lambda: webbrowser.open(url)).start()
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")
