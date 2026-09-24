@echo off
setlocal
cd /d "%~dp0"
title LocalVisionAI
echo ==========================================================
echo                 LocalVisionAI
echo ==========================================================
echo.
where py >nul 2>&1
if %errorlevel%==0 (
  start "" /b py local_app\server.py
  timeout /t 2 /nobreak >nul
  start "" http://127.0.0.1:3000
  echo Interface : http://127.0.0.1:3000
  echo Ferme cette fenetre pour arreter l'interface.
  pause
  exit /b
)
where python >nul 2>&1
if %errorlevel%==0 (
  start "" /b python local_app\server.py
  timeout /t 2 /nobreak >nul
  start "" http://127.0.0.1:3000
  echo Interface : http://127.0.0.1:3000
  echo Ferme cette fenetre pour arreter l'interface.
  pause
  exit /b
)
echo Python n'est pas disponible dans PATH.
echo Si ComfyUI Portable est installe, utilise son python_embeded\python.exe.
pause
