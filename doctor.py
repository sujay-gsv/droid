"""Local diagnostics; intentionally does not print keys or environment values."""
import importlib.util
import os
from pathlib import Path
import shutil
import sys
from driod.desktop import vscode_exe

print("DRIOD DIAGNOSTICS")
print("Python:", sys.version.split()[0])
print("Platform:", sys.platform)
print("OpenRouter environment key:", "set (hidden)" if os.getenv("OPENROUTER_API_KEY") else "not set; enter in Settings")
for module in ["tkinter", "playwright", "ddgs", "yfinance", "matplotlib", "docx", "pptx", "openpyxl", "vosk", "sounddevice", "pyttsx3", "pyautogui", "pytesseract", "screen_brightness_control"]:
    print(f"{module:27}", "installed" if importlib.util.find_spec(module) else "not installed")
for command in ["node", "npm", "git", "gh", "powershell", "tesseract"]:
    print(f"{command:27}", "on PATH" if shutil.which(command) else "not on PATH (may be optional)")
print("VS Code:", "found" if vscode_exe() else "not found")
print("Voice model:", "found" if (Path(__file__).parent / "voice-model" / "am" / "final.mdl").exists() else "run setup_voice.bat")
print("No credentials were printed. See README.md for setup and troubleshooting.")
