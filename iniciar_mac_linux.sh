#!/usr/bin/env bash
cd "$(dirname "$0")"
command -v ffmpeg >/dev/null || { echo "Instala FFmpeg (mac: brew install ffmpeg | linux: sudo apt install ffmpeg)"; exit 1; }
[ -d .venv ] || { python3 -m venv .venv && .venv/bin/pip install -r requirements.txt; }
.venv/bin/python app.py
