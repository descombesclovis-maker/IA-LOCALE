@echo off
setlocal
cd /d "%~dp0"
title Build LocalVisionAI
where py >nul 2>&1
if errorlevel 1 (
  echo Python est requis une seule fois pour construire l'application.
  pause
  exit /b 1
)

py -m pip install --upgrade pyinstaller pywebview
if errorlevel 1 goto FAIL

if not exist build mkdir build
if not exist dist mkdir dist

pyinstaller --noconfirm --clean --onefile --windowed --name LocalVisionAI ^
  --collect-all webview ^
  --add-data "local_app\web;local_app\web" ^
  --add-data "local_app\bootstrap_windows.py;local_app" ^
  --add-data "local_app\server.py;local_app" ^
  --add-data "local_app\llm.py;local_app" ^
  --add-data "workflows;workflows" ^
  --add-data "Text to image flux.json;." ^
  --add-data "text to image sdxl.json;." ^
  --add-data "Image to video wan.json;." ^
  --add-data "Text to Video LTX (très lourd).json;." ^
  local_app\launcher.py
if errorlevel 1 goto FAIL

copy /y dist\LocalVisionAI.exe "%USERPROFILE%\Desktop\LocalVisionAI.exe" >nul
if errorlevel 1 goto FAIL

echo.
echo ==========================================================
echo LocalVisionAI autonome construit sur le Bureau.
echo ==========================================================
echo.
echo Au premier lancement, l'application installe automatiquement :
echo - ComfyUI NVIDIA
necho - llama.cpp CUDA
necho - Qwen3 8B Q4_K_M (~5 Go)
echo.
echo Les moteurs sont ensuite relances automatiquement a chaque ouverture.
echo.
goto END

:FAIL
echo.
echo La construction a echoue. Consulte les messages ci-dessus.
pause
exit /b 1
:END
pause
