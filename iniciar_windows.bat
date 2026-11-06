@echo off
cd /d "%~dp0"
where ffmpeg >nul 2>nul || (echo Instala FFmpeg: winget install Gyan.FFmpeg & pause & exit /b)
if not exist .venv (python -m venv .venv && .venv\Scripts\pip install -r requirements.txt)
.venv\Scripts\python app.py
pause
