@echo off
setlocal
cd /d "%~dp0"

where node >nul 2>nul || (echo Instala Node.js 22 o superior desde https://nodejs.org/ & pause & exit /b 1)
where npm >nul 2>nul || (echo No se encontro npm. Reinstala Node.js incluyendo npm. & pause & exit /b 1)

echo.
echo [1/3] Preparando dependencias del frontend...
pushd frontend
call npm ci
if errorlevel 1 (popd & echo Error instalando dependencias. & pause & exit /b 1)

echo.
echo [2/3] Compilando NovoClip Studio...
call npm run build
if errorlevel 1 (popd & echo La compilacion fallo. No se copiaron archivos. & pause & exit /b 1)
popd

echo.
echo [3/3] Copiando la version compilada al servidor local...
if not exist web mkdir web
robocopy frontend\out web /E /R:2 /W:1
if errorlevel 8 (echo Error copiando frontend\out a web. & pause & exit /b 1)

echo.
echo NovoClip Studio actualizado. Reinicia la app y recarga con Ctrl+F5.
pause
