@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title LocalVisionAI - moteur local

echo.
echo ==========================================
echo          LocalVisionAI - LOCAL
echo ==========================================
echo.

where py >nul 2>&1
if not errorlevel 1 (
    set "PY=py"
    goto :python_ok
)

where python >nul 2>&1
if not errorlevel 1 (
    set "PY=python"
    goto :python_ok
)

echo [ERREUR] Python n'est pas installe.
echo Installe Python 3.11+ puis relance ce fichier.
pause
exit /b 1

:python_ok
echo [1/3] Verification de pywebview...
%PY% -m pip show pywebview >nul 2>&1
if errorlevel 1 (
    echo Installation de pywebview...
    %PY% -m pip install pywebview
    if errorlevel 1 (
        echo [ERREUR] Impossible d'installer pywebview.
        pause
        exit /b 1
    )
)

echo [2/3] Demarrage du serveur LOCAL...
echo       Aucun navigateur ne sera ouvert.
echo       ComfyUI + llama.cpp sont geres automatiquement.
echo.

%PY% local_app\launcher.py

set "ERR=%errorlevel%"
if not "%ERR%"=="0" (
    echo.
    echo [ERREUR] LocalVisionAI s'est arrete avec le code %ERR%.
    echo Journal :
    echo %LOCALAPPDATA%\LocalVisionAI\logs\startup.log
    echo.
    pause
    exit /b %ERR%
)

echo.
echo LocalVisionAI ferme.
exit /b 0
