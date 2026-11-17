"""Servidor de IA de NovoClip (la "IA incluida" de la suscripción).

Guarda TU clave de Gemini en el servidor (nunca va dentro de la app que repartes), comprueba la licencia
de cada usuario y limita cuántas peticiones de IA puede hacer al día.

Uso:
    pip install fastapi uvicorn google-genai
    set GEMINI_API_KEY=tu_clave          (Linux/Mac: export GEMINI_API_KEY=tu_clave)
    python server.py                     -> escucha en el puerto 8800

Licencias: edita licencias.json (se recarga solo en cada petición).
"""
from __future__ import annotations

import base64
import datetime as dt
import json
import os
import sqlite3
import threading
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

HERE = Path(__file__).resolve().parent
LICENSES = HERE / "licencias.json"
DB = HERE / "uso.sqlite3"
MODEL = os.environ.get("GEMINI_MODEL", "gemini-flash-latest")
MAX_IMAGES, MAX_PROMPT = 12, 400_000

app = FastAPI(title="NovoClip IA")
_lock = threading.Lock()


def _db():
    con = sqlite3.connect(DB)
    con.execute("CREATE TABLE IF NOT EXISTS uso (licencia TEXT, dia TEXT, n INTEGER, PRIMARY KEY (licencia, dia))")
    return con


def _license(key: str) -> dict:
    try:
        data = json.loads(LICENSES.read_text(encoding="utf-8"))
    except Exception:
        data = {}
    lic = data.get(key)
    if not lic or not lic.get("active", True):
        raise HTTPException(401, "licencia no válida")
    exp = lic.get("expires")
    if exp and dt.date.fromisoformat(exp) < dt.date.today():
        raise HTTPException(401, "licencia vencida")
    return lic


def _used_today(con, key: str) -> int:
    row = con.execute("SELECT n FROM uso WHERE licencia=? AND dia=?", (key, dt.date.today().isoformat())).fetchone()
    return row[0] if row else 0


class Img(BaseModel):
    label: str = ""
    data: str


class AIRequest(BaseModel):
    license: str
    prompt: str
    schema_: dict = Field(alias="schema")
    images: list[Img] = []


@app.get("/v1/license/{key}")
def license_status(key: str):
    try:
        lic = _license(key)
    except HTTPException:
        return {"active": False}
    with _lock, _db() as con:
        used = _used_today(con, key)
    limit = int(lic.get("daily_limit", 150))
    return {"active": True, "plan": lic.get("plan", "básico"), "remaining": max(0, limit - used), "limit": limit}


@app.post("/v1/ai")
def ai(req: AIRequest):
    lic = _license(req.license)
    if len(req.prompt) > MAX_PROMPT or len(req.images) > MAX_IMAGES:
        raise HTTPException(413, "petición demasiado grande")
    limit = int(lic.get("daily_limit", 150))
    with _lock, _db() as con:
        used = _used_today(con, req.license)
        if used >= limit:
            raise HTTPException(429, "límite diario alcanzado")
        con.execute("INSERT INTO uso VALUES (?,?,1) ON CONFLICT(licencia, dia) DO UPDATE SET n = n + 1",
                    (req.license, dt.date.today().isoformat()))
    from google import genai
    from google.genai import types
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    contents: list = [req.prompt]
    for im in req.images:
        contents += [im.label, types.Part.from_bytes(data=base64.b64decode(im.data), mime_type="image/jpeg")]
    cfg = types.GenerateContentConfig(response_mime_type="application/json", response_json_schema=req.schema_)
    try:
        resp = client.models.generate_content(model=lic.get("model") or MODEL, contents=contents, config=cfg)
    except Exception as e:
        raise HTTPException(502, f"error de la IA: {str(e)[:200]}")
    return {"text": resp.text or "", "remaining": max(0, limit - used - 1)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "8800")))
