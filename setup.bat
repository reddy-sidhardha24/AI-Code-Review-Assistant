@echo off
setlocal
cd /d "%~dp0"

echo ============================================================
echo AI Code Review Assistant - Windows setup
echo ============================================================

where node >nul 2>nul
if errorlevel 1 (
    echo ERROR: Node.js and npm are required. Install Node.js 18 or newer, then run setup.bat again.
    goto :fail
)
where npm >nul 2>nul
if errorlevel 1 (
    echo ERROR: npm was not found. Reinstall Node.js with npm enabled, then run setup.bat again.
    goto :fail
)
node -e "if (Number(process.versions.node.split('.')[0]) < 18) process.exit(1)" >nul 2>nul
if errorlevel 1 (
    echo ERROR: Node.js 18 or newer is required.
    goto :fail
)

set "PYTHON_CMD="
where py >nul 2>nul
if not errorlevel 1 (
    py -3.11 --version >nul 2>nul
    if not errorlevel 1 set "PYTHON_CMD=py -3.11"
)
if not defined PYTHON_CMD (
    where python >nul 2>nul
    if errorlevel 1 (
        echo ERROR: Python 3.11 or a compatible Python installation was not found.
        goto :fail
    )
    set "PYTHON_CMD=python"
)
%PYTHON_CMD% -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>nul
if errorlevel 1 (
    echo ERROR: Python 3.10 or newer is required. Python 3.11 is recommended.
    goto :fail
)

if not exist ".venv\Scripts\python.exe" (
    echo Creating the Python virtual environment...
    %PYTHON_CMD% -m venv .venv
    if errorlevel 1 (
        echo ERROR: Could not create the Python virtual environment.
        goto :fail
    )
)

echo Installing backend Python requirements. This may take several minutes...
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 (
    echo ERROR: Could not upgrade pip.
    goto :fail
)
".venv\Scripts\python.exe" -m pip install -r "backend\requirements.txt"
if errorlevel 1 (
    echo ERROR: Backend dependency installation failed.
    goto :fail
)

echo Installing frontend npm dependencies...
pushd frontend
call npm ci
if errorlevel 1 (
    popd
    echo ERROR: Frontend dependency installation failed.
    goto :fail
)
popd

echo.
echo Setup complete. Start the application with run.bat.
exit /b 0

:fail
echo.
echo Setup did not complete. Fix the reported issue and run setup.bat again.
pause
exit /b 1
