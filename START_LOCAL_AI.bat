@echo off
setlocal
cd /d "%~dp0"
title LocalVisionAI
echo ==========================================================
echo                 LocalVisionAI
echo ==========================================================
echo.

set "PYTHON_CMD="
where py >nul 2>&1
if %errorlevel%==0 set "PYTHON_CMD=py"
if not defined PYTHON_CMD (
  where python >nul 2>&1
  if %errorlevel%==0 set "PYTHON_CMD=python"
)
if not defined PYTHON_CMD (
  echo Recherche du Python embarque de ComfyUI...
  for /f "delims=" %%P in ('powershell -NoProfile -ExecutionPolicy Bypass -Command "$roots=@('%~dp0','%~dp0..','%USERPROFILE%\ComfyUI','D:\IA LOCAL'); $p=$null; foreach($r in $roots){if(Test-Path $r){$p=Get-ChildItem -LiteralPath $r -Filter python.exe -Recurse -ErrorAction SilentlyContinue | Where-Object { $_.FullName -match 'python_embeded' } | Select-Object -First 1 -ExpandProperty FullName; if($p){break}}}; if($p){$p}"') do set "PYTHON_CMD=%%P"
)
if not defined PYTHON_CMD (
  echo Python est introuvable.
  echo Lance DIAGNOSTIC_LOCAL_AI.bat pour voir ce qui est disponible.
  pause
  exit /b 1
)

echo Python : %PYTHON_CMD%

powershell -NoProfile -ExecutionPolicy Bypass -Command "try{Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8188/system_stats -TimeoutSec 2 ^| Out-Null; exit 0}catch{exit 1}"
if not errorlevel 1 goto COMFY_READY

echo Recherche automatique de ComfyUI...
for /f "delims=" %%C in ('powershell -NoProfile -ExecutionPolicy Bypass -Command "$roots=@('%~dp0','%~dp0..','%USERPROFILE%\ComfyUI','D:\IA LOCAL'); $p=$null; foreach($r in $roots){if(Test-Path $r){$p=Get-ChildItem -LiteralPath $r -Filter run_nvidia_gpu.bat -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty FullName; if($p){break}}}; if($p){$p}"') do set "COMFY_LAUNCHER=%%C"
if defined COMFY_LAUNCHER (
  echo ComfyUI trouve : %COMFY_LAUNCHER%
  start "" /b "%COMFY_LAUNCHER%"
  echo Attente du moteur...
  powershell -NoProfile -ExecutionPolicy Bypass -Command "$ok=$false; 1..30 ^| %%{try{Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8188/system_stats -TimeoutSec 1 ^| Out-Null; $ok=$true; break}catch{Start-Sleep -Seconds 1}}; if($ok){exit 0}else{exit 1}"
)
:COMFY_READY

start "" /b %PYTHON_CMD% local_app\server.py
timeout /t 2 /nobreak >nul
echo Lancement de LocalVisionAI natif...\nstart "" /wait "%PYTHON_CMD%" local_app\launcher.py
echo.
echo Interface : http://127.0.0.1:3000
echo.
echo Ferme cette fenetre pour arreter LocalVisionAI.
pause
