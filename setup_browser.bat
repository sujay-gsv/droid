@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" goto missing
".venv\Scripts\python.exe" -m pip install "playwright>=1.48,<2"
if errorlevel 1 goto fail
".venv\Scripts\python.exe" -m playwright install chromium
if errorlevel 1 goto fail
echo Browser checks are ready.
pause
exit /b 0
:missing
echo Run setup.bat first.
pause
exit /b 1
:fail
echo Browser setup failed. See the error above.
pause
exit /b 1
