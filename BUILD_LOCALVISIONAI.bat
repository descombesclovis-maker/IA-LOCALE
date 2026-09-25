@echo off
setlocal
cd /d "%~dp0"
title Build LocalVisionAI

where py >nul 2>&1
if errorlevel 1 (
  echo Python 3.11+ est requis pour construire LocalVisionAI.
  pause
  exit /b 1
)

py -m pip install --upgrade pyinstaller pywebview
if errorlevel 1 goto FAIL

if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

pyinstaller --noconfirm --clean --onefile --windowed --noupx --name LocalVisionAI ^
  --collect-all webview ^
  --hidden-import local_app ^
  --hidden-import local_app.bootstrap_windows ^
  --hidden-import local_app.server ^
  --hidden-import local_app.llm ^
  --add-data "local_app\web;local_app\web" ^
  --add-data "local_app\bootstrap_windows.py;local_app" ^
  --add-data "local_app\server.py;local_app" ^
  --add-data "local_app\llm.py;local_app" ^
  --add-data "local_app\__init__.py;local_app" ^
  --add-data "workflows;workflows" ^
  local_app\launcher.py

if errorlevel 1 goto FAIL

copy /y dist\LocalVisionAI.exe "%USERPROFILE%\Desktop\LocalVisionAI.exe" >nul
if errorlevel 1 goto FAIL

echo.
echo LocalVisionAI.exe a ete cree sur le Bureau.
echo Double-clique directement sur cet EXE : aucun navigateur ne sera utilise.
echo.
pause
exit /b 0

:FAIL
echo.
echo Echec de construction. Consulte les messages ci-dessus.
pause
exit /b 1
