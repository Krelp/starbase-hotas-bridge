@echo off
title Starbase HOTAS Bridge - Build EXE
color 0B
cls

echo.
echo  ============================================================
echo   STARBASE HOTAS BRIDGE - EXE Builder
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

:: Install PyInstaller and dependencies
echo  [..] Installing PyInstaller and dependencies...
python -m pip install pyinstaller pygame pynput PyQt6 --quiet --disable-pip-version-check
echo  [OK] Dependencies ready.

:: Make sure hotas_profiles folder exists with the default profile
echo  [..] Preparing hotas_profiles folder...
if not exist "hotas_profiles" mkdir "hotas_profiles"

:: Write the VKB Default profile if it doesn't exist
if not exist "hotas_profiles\VKB Default.json" (
    echo  [..] Writing VKB Default profile...
    python -c "import json; open('hotas_profiles/VKB Default.json','w').write(json.dumps({'name':'VKB Default','devices':{'stick':0,'throttle':2,'pedals':1},'movements':{'yaw':{'physical_axis':5,'key_left':'q','key_right':'e','deadzone':5,'speed':60,'pulse':10,'inverted':True,'control_points':[[0.114,0.139],[0.257,0.231],[0.365,0.299],[0.490,0.380],[0.632,0.489],[0.75,0.596],[0.875,0.786]]},'pitch':{'physical_axis':1,'key_left':'w','key_right':'s','deadzone':5,'speed':60,'pulse':20,'inverted':False,'control_points':[[0.131,0.209],[0.231,0.280],[0.372,0.351],[0.501,0.465],[0.633,0.571],[0.757,0.693],[0.881,0.848]]},'roll':{'physical_axis':0,'key_left':'a','key_right':'d','deadzone':5,'speed':60,'pulse':20,'inverted':False,'control_points':[[0.116,0.204],[0.235,0.299],[0.349,0.380],[0.490,0.467],[0.610,0.579],[0.738,0.707],[0.870,0.840]]},'thrust':{'physical_axis':1,'key_left':'shift','key_right':'ctrl','deadzone':5,'speed':80,'pulse':50,'inverted':False,'control_points':[[0.132,0.155],[0.241,0.209],[0.367,0.277],[0.501,0.372],[0.615,0.481],[0.75,0.596],[0.875,0.786]]},'strafe_lr':{'physical_axis':0,'key_left':'left','key_right':'right','deadzone':5,'speed':60,'pulse':20,'inverted':False,'control_points':[[0.127,0.201],[0.248,0.291],[0.384,0.413],[0.507,0.543],[0.626,0.668],[0.753,0.810],[0.870,0.908]]},'strafe_ud':{'physical_axis':5,'key_left':'down','key_right':'up','deadzone':5,'speed':60,'pulse':20,'inverted':False,'control_points':[[0.121,0.163],[0.235,0.253],[0.372,0.345],[0.510,0.448],[0.628,0.573],[0.741,0.736],[0.861,0.894]]},'pedals':{'physical_axis':99,'key_left':'q','key_right':'e','deadzone':5,'speed':50,'pulse':30,'inverted':False}}},indent=2))"
)
echo  [OK] hotas_profiles folder ready.

echo.
echo  [..] Building EXE (this takes 1-3 minutes)...
echo.

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
echo   Upload that file to your GitHub Release.
echo.
pause
