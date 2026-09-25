@echo off
setlocal
cd /d "%~dp0"
title Build LocalVisionAI
where py >nul 2>&1
if errorlevel 1 (
  echo Python est requis pour fabriquer le .exe.
  pause
  exit /b 1
)
py -m pip install --upgrade pyinstaller pywebview
if errorlevel 1 goto FAIL
pyinstaller --noconfirm --clean --onefile --windowed --name LocalVisionAI --collect-all webview local_app\launcher.py
if errorlevel 1 goto FAIL
copy /y dist\LocalVisionAI.exe "%USERPROFILE%\Desktop\LocalVisionAI.exe" >nul
echo.
echo EXE cree sur le Bureau.
echo.
goto END
:FAIL
echo La construction a echoue.
pause
:END
