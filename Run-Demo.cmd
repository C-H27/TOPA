@echo off
setlocal
pushd "%~dp0" || exit /b 1
title Smart Table Finder - Live counts
set "VIDEO=studyspot-agent\videos\learning_center_2.mp4"
if not "%~1"=="" set "VIDEO=%~f1"
if not exist "%VIDEO%" (
    echo Drag learning_center_2.mp4 onto Run-Demo.cmd to start.
    goto failed
)
set "PYTHON=backend\.venv\Scripts\python.exe"
if not exist "%PYTHON%" goto need_backend
if not defined TOPA_PORT set "TOPA_PORT=8000"
set "URL=http://127.0.0.1:%TOPA_PORT%"
"%PYTHON%" -c "import sys,urllib.request; urllib.request.urlopen(sys.argv[1]+'/status',timeout=3).close()" "%URL%" >nul 2>&1
if errorlevel 1 goto need_backend
echo Live room counts appear every 10 seconds. Table CSV updates every 2.5 seconds.
echo Output folder: %CD%\studyspot-agent\output
"%PYTHON%" "studyspot-agent\main.py" --video "%VIDEO%" --backend "%URL%" --loop
if errorlevel 1 goto failed
echo Demo complete.
pause
exit /b 0

:need_backend
echo Double-click Start-Backend.cmd first and wait for "Uvicorn running".
:failed
pause
exit /b 1
