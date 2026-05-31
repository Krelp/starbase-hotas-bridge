@echo off
title Starbase HOTAS Bridge - Launcher
color 0A
cls

echo.
echo  ============================================================
echo   STARBASE HOTAS BRIDGE
echo  ============================================================
echo.

:: Check if Python is already installed
python --version >nul 2>&1
if %errorlevel% == 0 (
    echo  [OK] Python found.
    goto check_deps
)

:: Try py launcher
py --version >nul 2>&1
if %errorlevel% == 0 (
    echo  [OK] Python found via py launcher.
    set PYTHON=py
    goto check_deps
)

:: Python not found - download installer
echo  [..] Python not found. Downloading Python installer...
echo.
powershell -Command "& {Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe' -OutFile '%TEMP%\python_installer.exe'}"
if %errorlevel% neq 0 (
    echo  [!!] Download failed. Please install Python 3.11+ from python.org
    echo       Make sure to check 'Add Python to PATH' during install.
    pause
    exit /b 1
)
echo  [..] Installing Python (this takes about 1 minute)...
echo       Please wait - do not close this window.
%TEMP%\python_installer.exe /quiet InstallAllUsers=0 PrependPath=1 Include_test=0
echo  [OK] Python installed.
echo.
echo  [!!] Please close this window and run launch.bat again.
pause
exit /b 0

:check_deps
if not defined PYTHON set PYTHON=python

echo  [..] Checking required packages...
echo.

%PYTHON% -c "import pygame" >nul 2>&1
if %errorlevel% neq 0 (
    echo  [..] Installing pygame...
    %PYTHON% -m pip install pygame --quiet --disable-pip-version-check
)

%PYTHON% -c "import pynput" >nul 2>&1
if %errorlevel% neq 0 (
    echo  [..] Installing pynput...
    %PYTHON% -m pip install pynput --quiet --disable-pip-version-check
)

%PYTHON% -c "import PyQt6" >nul 2>&1
if %errorlevel% neq 0 (
    echo  [..] Installing PyQt6...
    %PYTHON% -m pip install PyQt6 --quiet --disable-pip-version-check
)

echo  [OK] All packages ready.
echo.
echo  [>>] Launching Starbase HOTAS Bridge...
echo.

cd /d "%~dp0"
%PYTHON% starbase_hotas.py
if %errorlevel% neq 0 (
    echo.
    echo  [!!] The app closed with an error.
    pause
)
