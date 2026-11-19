@echo off
cd /d "%~dp0"
echo === Prueba de YouTube para NovoClip ===
set /p URL=Pega el enlace de YouTube y pulsa Enter: 
set OPCOOK=
if exist cookies.txt (set OPCOOK=--cookies cookies.txt & echo [usando cookies.txt]) else (echo [no hay cookies.txt en esta carpeta])
where deno >nul 2>nul && (echo [Deno: si]) || (echo [Deno: NO se encuentra - cierra esta ventana y abre una nueva])
echo.
.venv\Scripts\python -m yt_dlp -v %OPCOOK% -F "%URL%" > diagnostico_youtube.txt 2>&1
echo ----- Resultado (ultimas lineas) -----
powershell -NoProfile -Command "Get-Content diagnostico_youtube.txt -Tail 25"
echo.
echo Se guardo el informe completo en diagnostico_youtube.txt (NO contiene tus cookies).
echo Mandame las lineas de arriba, o ese archivo.
pause
