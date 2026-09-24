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
  start "" http://127.0.0.1:3000
  py local_app\server.py
  goto :eof
)
where python >nul 2>&1
if %errorlevel%==0 (
  start "" http://127.0.0.1:3000
  python local_app\server.py
  goto :eof
)
echo Python n'est pas disponible dans PATH.
echo Si ComfyUI Portable est installe, ouvre son dossier et utilise
echo son python_embeded\python.exe pour lancer local_app\server.py.
pause
