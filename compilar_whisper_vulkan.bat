@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"
title NovoClip - compilar whisper.cpp con Vulkan (GPU AMD)

echo ==================================================================
echo  Compila whisper.cpp (codigo oficial de ggml-org) con Vulkan para
echo  transcribir con tu tarjeta grafica AMD. Solo hace falta una vez.
echo  Necesita: Git, CMake, Vulkan SDK y Visual Studio Build Tools (C++).
echo  Lo que falte se instala con winget (puede pedir permiso de admin).
echo ==================================================================
echo.

set WHISPER_TAG=v1.9.5
set NEED_RESTART=0

rem ---------- 1. Herramientas ----------
where git >nul 2>nul || (
  echo [1/4] Instalando Git...
  winget install --id Git.Git -e --accept-source-agreements --accept-package-agreements
  set NEED_RESTART=1
)
where cmake >nul 2>nul || (
  echo [1/4] Instalando CMake...
  winget install --id Kitware.CMake -e --accept-source-agreements --accept-package-agreements
  set NEED_RESTART=1
)
if not defined VULKAN_SDK (
  echo [1/4] Instalando Vulkan SDK...
  winget install --id KhronosGroup.VulkanSDK -e --accept-source-agreements --accept-package-agreements
  set NEED_RESTART=1
)
set "VSWHERE=%ProgramFiles(x86)%\Microsoft Visual Studio\Installer\vswhere.exe"
set "VSPATH="
if exist "%VSWHERE%" (
  for /f "usebackq delims=" %%i in (`"%VSWHERE%" -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath`) do set "VSPATH=%%i"
)
if not defined VSPATH (
  echo [1/4] Instalando Visual Studio Build Tools con C++ ^(unos 3 GB, tarda un rato^)...
  winget install --id Microsoft.VisualStudio.2022.BuildTools -e --accept-source-agreements --accept-package-agreements --override "--wait --passive --add Microsoft.VisualStudio.Workload.VCTools --includeRecommended"
  set NEED_RESTART=1
)
if "%NEED_RESTART%"=="1" (
  echo.
  echo Se instalaron herramientas nuevas. CIERRA esta ventana y vuelve a ejecutar
  echo compilar_whisper_vulkan.bat para continuar.
  pause
  exit /b 0
)
echo [1/4] Herramientas OK  ^(Vulkan SDK: %VULKAN_SDK%^)

rem ---------- 2. Codigo fuente oficial ----------
set "WORK=%~dp0build_whisper"
if not exist "%WORK%" mkdir "%WORK%"
cd /d "%WORK%"
if not exist whisper.cpp (
  echo [2/4] Descargando whisper.cpp %WHISPER_TAG%...
  git clone --depth 1 --branch %WHISPER_TAG% https://github.com/ggml-org/whisper.cpp whisper.cpp || goto :fail
)
if not exist SPIRV-Headers (
  git clone --depth 1 https://github.com/KhronosGroup/SPIRV-Headers SPIRV-Headers || goto :fail
)
if not exist spirv\share (
  cmake -S SPIRV-Headers -B spirv-build -DCMAKE_INSTALL_PREFIX="%WORK%\spirv" -DSPIRV_HEADERS_ENABLE_TESTS=OFF || goto :fail
  cmake --install spirv-build || goto :fail
)

rem ---------- 3. Compilar ----------
echo [3/4] Compilando con Vulkan ^(10-20 minutos la primera vez^)...
cmake -S whisper.cpp -B build -G "Visual Studio 17 2022" -A x64 ^
  -DGGML_VULKAN=ON -DBUILD_SHARED_LIBS=OFF -DGGML_NATIVE=ON ^
  -DWHISPER_BUILD_TESTS=OFF -DWHISPER_BUILD_SERVER=OFF ^
  -DCMAKE_PREFIX_PATH="%WORK%\spirv" || goto :fail
cmake --build build --config Release --target whisper-cli -j || goto :fail

rem ---------- 4. Copiar a NovoClip ----------
set "DEST=%~dp0bin\whisper-vulkan"
if not exist "%DEST%" mkdir "%DEST%"
copy /y build\bin\Release\whisper-cli.exe "%DEST%\" >nul || goto :fail
for %%f in (build\bin\Release\*.dll) do copy /y "%%f" "%DEST%\" >nul
echo [4/4] Instalado en %DEST%
echo.
echo Comprobando que ve tu GPU:
"%DEST%\whisper-cli.exe" --help >nul 2>nul
vulkaninfo --summary 2>nul | findstr /i "deviceName"
echo.
echo LISTO. Abre iniciar_windows.bat: arriba a la derecha debe decir "transcripcion Vulkan".
echo Puedes borrar la carpeta build_whisper si quieres liberar espacio.
pause
exit /b 0

:fail
echo.
echo *** Algo fallo. Copia el texto de esta ventana y envialo. ***
pause
exit /b 1
