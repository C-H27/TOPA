@echo off
setlocal
pushd "%~dp0" || exit /b 1

if not "%~1"=="" if /i not "%~1"=="--csv-only" goto usage
if not defined TOPA_BACKEND_URL set "TOPA_BACKEND_URL=http://127.0.0.1:8000"
set "PYTHON=.venv\Scripts\python.exe"
set "INSTALLED=.venv\installed-requirements.txt"

if exist "%PYTHON%" goto dependencies
echo Creating the detector Python environment...
where py >nul 2>&1
if errorlevel 1 goto system_python
py -3 -c "import sys; sys.exit(sys.version_info < (3, 10))"
if errorlevel 1 goto system_python
py -3 -m venv .venv
if errorlevel 1 goto failed
goto dependencies

:system_python
python -c "import sys; sys.exit(sys.version_info < (3, 10))" >nul 2>&1
if errorlevel 1 (
    echo Install Python 3.10 or newer and make sure py or python works.
    goto failed
)
python -m venv .venv
if errorlevel 1 goto failed

:dependencies
if not exist "%INSTALLED%" goto install
fc /b requirements.txt "%INSTALLED%" >nul 2>&1
if not errorlevel 1 goto run

:install
echo Installing detector dependencies. This step requires an internet connection.
"%PYTHON%" -m pip install --disable-pip-version-check -r requirements.txt
if errorlevel 1 goto failed
copy /y requirements.txt "%INSTALLED%" >nul
if errorlevel 1 goto failed

:run
if /i "%~1"=="--csv-only" goto csv_only
echo Checking the TOPA backend at %TOPA_BACKEND_URL%...
"%PYTHON%" -c "import os,urllib.request; urllib.request.urlopen(os.environ['TOPA_BACKEND_URL'].rstrip('/') + '/status', timeout=3).close()"
if errorlevel 1 (
    echo Start TOPA with Start-Backend.cmd and keep that window open.
    goto failed
)
"%PYTHON%" main.py --backend "%TOPA_BACKEND_URL%"
if errorlevel 1 goto failed
goto done

:csv_only
"%PYTHON%" main.py
if errorlevel 1 goto failed

:done
echo Detector finished. See output\room.csv and output\tables.csv.
popd
pause
exit /b 0

:usage
echo Usage: Start-Detector.cmd [--csv-only]
:failed
echo Detector startup or playback failed. See the message above.
popd
pause
exit /b 1
