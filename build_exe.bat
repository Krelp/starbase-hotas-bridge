@echo off
title Starbase HOTAS Bridge - Build EXE
color 0B
cls

echo.
echo  ============================================================
echo   STARBASE HOTAS BRIDGE - EXE Builder
echo   This builds a standalone .exe anyone can run directly.
echo  ============================================================
echo.

:: Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  [!!] Python not found. Run launch.bat first to install Python.
    pause
    exit /b 1
)
echo  [OK] Python found.

:: Install PyInstaller
echo  [..] Installing PyInstaller...
python -m pip install pyinstaller --quiet --disable-pip-version-check
echo  [OK] PyInstaller ready.

:: Install app dependencies
echo  [..] Installing app dependencies...
python -m pip install pygame pynput PyQt6 --quiet --disable-pip-version-check
echo  [OK] Dependencies ready.

echo.
echo  [..] Building EXE (this takes 1-3 minutes)...
echo.

:: Build the exe — single file, no console window, with icon if present
cd /d "%~dp0"

if exist "icon.ico" (
    python -m PyInstaller --onefile --noconsole --name "StarbaseHOTASBridge" --icon="icon.ico" --add-data "hotas_profiles;hotas_profiles" starbase_hotas.py
) else (
    python -m PyInstaller --onefile --noconsole --name "StarbaseHOTASBridge" --add-data "hotas_profiles;hotas_profiles" starbase_hotas.py
)

if %errorlevel% neq 0 (
    echo.
    echo  [!!] Build failed. See errors above.
    pause
    exit /b 1
)

echo.
echo  ============================================================
echo   BUILD COMPLETE
echo  ============================================================
echo.
echo   Your EXE is at:
echo   dist\StarbaseHOTASBridge.exe
echo.
echo   Copy that file anywhere — it runs with no Python required.
echo   Double-click it to launch. No install needed.
echo.
echo   For GitHub release: upload dist\StarbaseHOTASBridge.exe
echo   as a release asset so users can download one file.
echo.
pause
