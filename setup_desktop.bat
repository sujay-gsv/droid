@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" goto missing
".venv\Scripts\python.exe" -m pip install -r requirements-desktop.txt
if errorlevel 1 goto fail
echo Screen controls installed. Restart Driod.
echo For OCR you also need the Tesseract application; see README.md.
echo Move your mouse to a screen corner to trigger PyAutoGUI's emergency stop.
pause
exit /b 0
:missing
echo Run setup.bat first.
pause
exit /b 1
:fail
echo Desktop setup failed. See the error above.
pause
exit /b 1
