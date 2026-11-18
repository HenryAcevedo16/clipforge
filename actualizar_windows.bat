@echo off
cd /d "%~dp0"
echo Actualizando NovoClip desde GitHub...
where git >nul 2>nul || (echo Instala Git: winget install Git.Git & pause & exit /b)
git fetch origin main || (echo No se pudo conectar con GitHub. & pause & exit /b)
git reset --hard origin/main
if exist .venv (.venv\Scripts\pip install -q -r requirements.txt)
echo.
echo Version instalada:
git log -1 --format="%%h  %%ad  %%s" --date=format:"%%d/%%m %%H:%%M"
echo.
echo Listo. Cierra esta ventana, abre iniciar_windows.bat y pulsa Ctrl+F5 en el navegador.
pause
