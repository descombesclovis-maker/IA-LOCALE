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
  echo.
  echo Python est introuvable.
  echo Lance DIAGNOSTIC_LOCAL_AI.bat et envoie-moi son resultat.
  pause
  exit /b 1
)

echo Python : %PYTHON_CMD%
start "" /b %PYTHON_CMD% local_app\server.py
timeout /t 2 /nobreak >nul
start "" http://127.0.0.1:3000
echo.
echo Interface : http://127.0.0.1:3000
echo.
echo Ferme cette fenetre pour arreter l'interface.
pause
