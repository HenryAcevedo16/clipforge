@echo off
cd /d "%~dp0"
echo Instalando librerias de NVIDIA (CUDA 12 + cuDNN 9) para transcribir con la GPU...
echo Requiere una tarjeta NVIDIA con drivers actualizados. Descarga ~1 GB.
.venv\Scripts\pip install -U nvidia-cublas-cu12 "nvidia-cudnn-cu12>=9,<10"
echo.
echo Listo. Abre iniciar_windows.bat y elige "Procesar con: GPU" o "Automatico".
pause
