@echo off
cd /d "%~dp0"
echo ===== Tarjetas graficas =====
powershell -NoProfile -Command "Get-CimInstance Win32_VideoController | Select-Object Name, DriverVersion | Format-Table -AutoSize"
echo ===== FFmpeg =====
where ffmpeg
ffmpeg -hide_banner -version | findstr /i "version"
echo ===== Codificadores de GPU en tu FFmpeg =====
ffmpeg -hide_banner -encoders | findstr /i "amf nvenc qsv"
echo ===== Prueba AMD AMF =====
ffmpeg -hide_banner -v error -f lavfi -i testsrc2=s=1280x720:r=30:d=0.5 -pix_fmt nv12 -c:v h264_amf -f null - && echo AMF FUNCIONA
echo ===== Lo que detecta NovoClip =====
.venv\Scripts\python -c "import json,pipeline; print(json.dumps(pipeline.hw_info(), indent=2, ensure_ascii=False))"
echo.
echo Copia todo este texto y envialo.
pause
