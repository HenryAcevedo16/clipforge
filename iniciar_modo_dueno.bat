@echo off
cd /d "%~dp0"
rem Modo dueño: la 'IA incluida' usa TU suscripción de Claude (Claude Code). Solo para uso personal.
set NOVOCLIP_DEV=1
where ffmpeg >nul 2>nul || (echo Instala FFmpeg: winget install Gyan.FFmpeg & pause & exit /b)
if not exist .venv (python -m venv .venv && .venv\Scripts\pip install -r requirements.txt)
.venv\Scripts\python -c "import google.genai" 2>nul || (echo Instalando la libreria de Gemini... & .venv\Scripts\pip install -q google-genai)
.venv\Scripts\python app.py
pause
