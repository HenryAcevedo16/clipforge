@echo off
cd /d "%~dp0"
where ffmpeg >nul 2>nul || (echo Instala FFmpeg: winget install Gyan.FFmpeg & pause & exit /b)
if not exist .venv (python -m venv .venv && .venv\Scripts\pip install -r requirements.txt)
.venv\Scripts\python -c "import google.genai" 2>nul || (echo Instalando la libreria de Gemini... & .venv\Scripts\pip install -q google-genai)
.venv\Scripts\python app.py
pause
