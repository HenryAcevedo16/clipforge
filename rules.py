"""Reglas de edición editables (carpeta reglas/ + reglas/mis_reglas/). Solo librería estándar.

Los archivos de reglas/ vienen con la app; los del usuario van en reglas/mis_reglas/ y se combinan encima.
Un archivo que falta o tiene errores nunca rompe nada: se saltan las líneas malas y se avisa una vez.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

DIR = Path(__file__).resolve().parent / "reglas"
_cache: dict = {}
_warned: set = set()


def _user_dir() -> Path:
    return DIR / "mis_reglas"


def _warn(path: Path, msg: str) -> None:
    try:
        key = (str(path), path.stat().st_mtime, msg)
    except OSError:
        key = (str(path), 0, msg)
    if key not in _warned:
        _warned.add(key)
        print(f"[reglas] {path.name}: {msg}")


def _lines(path: Path) -> Optional[list]:
    """Líneas útiles del archivo (sin comentarios ni vacías), o None si no existe. Caché por fecha de modificación."""
    try:
        mt = path.stat().st_mtime
    except OSError:
        return None
    hit = _cache.get(path)
    if hit and hit[0] == mt:
        return hit[1]
    try:
        raw = path.read_text(encoding="utf-8-sig")      # utf-8-sig: el Bloc de notas añade un BOM
    except (OSError, UnicodeDecodeError) as e:
        _warn(path, f"no se pudo leer ({e}); se usan los valores de la app")
        return None
    out = [ln.strip() for ln in raw.splitlines() if ln.strip() and not ln.strip().startswith("#")]
    _cache[path] = (mt, out)
    return out


def read_list(name: str) -> Optional[list]:
    """Entradas de la base + las del usuario (-x quita x). None si no hay ningún archivo."""
    base, user = _lines(DIR / name), _lines(_user_dir() / name)
    if base is None and user is None:
        return None
    items = list(base or [])
    for u in user or []:
        if u.startswith("-") and len(u) > 1:
            gone = u[1:].strip().lower()
            items = [x for x in items if x.lower() != gone]
        elif u not in items:
            items.append(u)
    return items


def read_regexes(name: str) -> Optional[list]:
    items = read_list(name)
    if items is None:
        return None
    good = []
    for x in items:
        try:
            re.compile(x)
            good.append(x)
        except re.error as e:
            _warn(DIR / name, f"expresión inválida «{x}» ({e}); se salta")
    return good


def _norm(w: str) -> str:
    return re.sub(r"[^\w]", "", w.lower(), flags=re.U)


def read_glossary() -> list:
    """[(palabras normalizadas de 'mal', 'bien')] con las más largas primero. El usuario gana si repite un 'mal'."""
    merged: dict = {}
    for path in (DIR / "glosario.txt", _user_dir() / "glosario.txt"):
        for ln in _lines(path) or []:
            if "->" not in ln:
                _warn(path, f"línea sin «->»: «{ln[:40]}»; se salta")
                continue
            src, dst = (p.strip() for p in ln.split("->", 1))
            key = tuple(_norm(w) for w in src.split() if _norm(w))
            if key and dst:
                merged[key] = dst
    return sorted(merged.items(), key=lambda kv: -len(kv[0]))


def read_templates() -> list:
    """[(tipo, plantilla)] de la base + las del usuario."""
    out = []
    for ln in read_list("ganchos.txt") or []:
        if "|" not in ln:
            _warn(DIR / "ganchos.txt", f"línea sin «|»: «{ln[:40]}»; se salta")
            continue
        tipo, tpl = (p.strip() for p in ln.split("|", 1))
        if tipo in ("pregunta", "numero", "tema") and tpl:
            out.append((tipo, tpl))
    return out


def read_highlight() -> tuple:
    """(siempre, nunca): conjuntos de palabras normalizadas de resaltado.txt (+x / -x), base y usuario."""
    always, never = set(), set()
    for path in (DIR / "resaltado.txt", _user_dir() / "resaltado.txt"):
        for ln in _lines(path) or []:
            if ln[0] in "+-" and len(ln) > 1:
                (always if ln[0] == "+" else never).add(_norm(ln[1:]))
                (never if ln[0] == "+" else always).discard(_norm(ln[1:]))
    return always, never


def read_guide(limit: int = 1500) -> str:
    """Guía para la IA: la del usuario reemplaza a la base; sin comentarios ni líneas vacías; recortada en un salto de línea."""
    for path in (_user_dir() / "guia_ia.md", DIR / "guia_ia.md"):
        lines = _lines(path)
        if lines:
            text = "\n".join(lines)
            if len(text) > limit:
                text = text[:limit].rsplit("\n", 1)[0]
            return text
    return ""
