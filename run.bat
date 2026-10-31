@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo The application environment is not set up yet. Run setup.bat first.
    pause
    exit /b 1
)

".venv\Scripts\python.exe" run.py %*
set "APP_EXIT_CODE=%ERRORLEVEL%"
if not "%APP_EXIT_CODE%"=="0" (
    echo.
    echo The application stopped with exit code %APP_EXIT_CODE%.
    pause
)
exit /b %APP_EXIT_CODE%
