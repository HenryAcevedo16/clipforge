@echo off
cd /d "%~dp0"
where ffmpeg >nul 2>nul || (echo Instala FFmpeg: winget install Gyan.FFmpeg & pause & exit /b)
if not exist .venv (python -m venv .venv && .venv\Scripts\pip install -r requirements.txt)
.venv\Scripts\python -c "import google.genai" 2>nul || (echo Instalando la libreria de Gemini... & .venv\Scripts\pip install -q google-genai)
where deno >nul 2>nul || where node >nul 2>nul || (echo Instalando Deno, el motor que YouTube exige para descargar... & winget install -e --id DenoLand.Deno --accept-source-agreements --accept-package-agreements & echo. & echo Si acaba de instalarse, CIERRA esta ventana y abre iniciar_windows.bat otra vez. & pause)
.venv\Scripts\python app.py
pause
