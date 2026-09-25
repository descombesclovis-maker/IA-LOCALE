@echo off
setlocal
cd /d "%~dp0"
title LocalVisionAI

if exist "%USERPROFILE%\Desktop\LocalVisionAI.exe" (
  start "" "%USERPROFILE%\Desktop\LocalVisionAI.exe"
  exit /b 0
)

rem Un seul point d'entrée : le launcher démarre lui-même ComfyUI + llama.cpp + l'interface native.
where py >nul 2>&1
if not errorlevel 1 (
  py local_app\launcher.py
  exit /b %errorlevel%
)
where python >nul 2>&1
if not errorlevel 1 (
  python local_app\launcher.py
  exit /b %errorlevel%
)

echo Python n'est pas disponible. Lance BUILD_LOCALVISIONAI.bat une fois pour fabriquer l'application autonome.
pause
exit /b 1
