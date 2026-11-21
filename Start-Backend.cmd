@echo off
setlocal
pushd "%~dp0" || exit /b 1

set "TOPA_BIND=127.0.0.1"
if /i "%~1"=="--lan" set "TOPA_BIND=0.0.0.0"
if not "%~1"=="" if /i not "%~1"=="--lan" goto usage
if not defined TOPA_PORT set "TOPA_PORT=8000"

set "VENV=backend\.venv"
set "PYTHON=%VENV%\Scripts\python.exe"
set "REQUIREMENTS=backend\requirements.txt"
set "INSTALLED=%VENV%\installed-requirements.txt"

if exist "%PYTHON%" goto dependencies
echo Creating the backend Python environment...
where py >nul 2>&1
if errorlevel 1 goto system_python
py -3 -c "import sys; sys.exit(sys.version_info < (3, 10))"
if errorlevel 1 goto system_python
py -3 -m venv "%VENV%"
if errorlevel 1 goto failed
goto dependencies

:system_python
python -c "import sys; sys.exit(sys.version_info < (3, 10))" >nul 2>&1
if errorlevel 1 (
    echo Install Python 3.10 or newer and make sure the py or python command works.
    goto failed
)
python -m venv "%VENV%"
if errorlevel 1 goto failed

:dependencies
if not exist "%INSTALLED%" goto install
fc /b "%REQUIREMENTS%" "%INSTALLED%" >nul 2>&1
if not errorlevel 1 goto serve

:install
echo Installing backend dependencies. This step requires an internet connection.
"%PYTHON%" -m pip install --disable-pip-version-check -r "%REQUIREMENTS%"
if errorlevel 1 goto failed
copy /y "%REQUIREMENTS%" "%INSTALLED%" >nul
if errorlevel 1 goto failed

:serve
echo.
echo Smart Table Finder backend
echo Dashboard: http://127.0.0.1:%TOPA_PORT%/
echo API docs:  http://127.0.0.1:%TOPA_PORT%/docs
echo Status:    http://127.0.0.1:%TOPA_PORT%/status
echo Detector:  POST http://127.0.0.1:%TOPA_PORT%/update
if "%TOPA_BIND%"=="0.0.0.0" echo Phone access: open the demo laptop's Wi-Fi IPv4 address on port %TOPA_PORT%.
echo Keep this window open during the demo. Press Ctrl+C to stop.
echo.
"%PYTHON%" -m uvicorn backend.app:app --host "%TOPA_BIND%" --port "%TOPA_PORT%"
if errorlevel 1 goto failed
popd
exit /b 0

:usage
echo Usage: Start-Backend.cmd [--lan]
:failed
echo Backend startup failed. See the error above.
popd
pause
exit /b 1
