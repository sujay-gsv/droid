@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" goto missing
".venv\Scripts\python.exe" -m pip install -r requirements-voice.txt
if errorlevel 1 goto fail
".venv\Scripts\python.exe" download_voice_model.py
if errorlevel 1 goto fail
echo Voice ready. Restart Driod, enable Speak replies, and turn the Microphone ON.
echo Say Jarvis followed by your request. The microphone is off by default.
pause
exit /b 0
:missing
echo Run setup.bat first.
pause
exit /b 1
:fail
echo Voice setup failed. Typed commands still work. See the error above.
pause
exit /b 1
