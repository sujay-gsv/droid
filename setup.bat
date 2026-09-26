@echo off
setlocal
cd /d "%~dp0"
echo DRIOD - Windows setup
echo Install Python 3.11 or 3.12 from python.org first if needed.
if exist ".venv\Scripts\python.exe" goto install
py -3 -c "import sys; assert sys.version_info >= (3,10)" >nul 2>&1
if errorlevel 1 goto try_python
py -3 -m venv .venv
if errorlevel 1 goto fail
goto install
:try_python
python -c "import sys; assert sys.version_info >= (3,10)" >nul 2>&1
if errorlevel 1 goto missing
python -m venv .venv
if errorlevel 1 goto fail
:install
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto fail
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto fail
".venv\Scripts\python.exe" -m playwright install chromium
if errorlevel 1 goto browser_warning
echo.
echo Ready. Double-click start.bat to open Driod.
echo Optional: setup_voice.bat and setup_desktop.bat add voice and screen controls.
pause
exit /b 0
:browser_warning
echo Core installed. Browser download failed; rerun setup_browser.bat later.
pause
exit /b 0
:missing
echo Python 3.10 or newer was not found.
echo Install Python 3.11 or 3.12 from https://www.python.org/downloads/windows/
echo Select Add python.exe to PATH, then run this file again.
pause
exit /b 1
:fail
echo Setup failed. Read the error above, check your internet connection, then retry.
pause
exit /b 1
