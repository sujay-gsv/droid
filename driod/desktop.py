from __future__ import annotations
import ctypes
from ctypes import wintypes
import os
from pathlib import Path
import shutil
import subprocess
import sys


def vscode_exe():
    if os.name == "nt":
        candidates = [Path(os.getenv("LOCALAPPDATA", "")) / "Programs/Microsoft VS Code/Code.exe",
                      Path(os.getenv("ProgramFiles", "C:/Program Files")) / "Microsoft VS Code/Code.exe"]
        code = shutil.which("code")
        if code:
            candidates.insert(0, Path(code).parent.parent / "Code.exe")
        for path in candidates:
            if path.is_file():
                return str(path)
    return shutil.which("code")


def open_vscode(path, line=1):
    code = vscode_exe()
    if not code:
        raise RuntimeError("VS Code was not found. Install it and select 'Add to PATH', then restart Driod.")
    args = [code, "--reuse-window"]
    args += ["--goto", str(path) + ":" + str(max(1, int(line)))] if path.is_file() else [str(path)]
    subprocess.Popen(args, shell=False)
    return {"opened": str(path), "editor": "Visual Studio Code"}


def open_app(app, project_path):
    app = app.lower().strip()
    if app in {"vscode", "vs code", "visual studio code"}:
        return open_vscode(project_path)
    if os.name != "nt":
        if app in {"explorer", "files"}:
            subprocess.Popen(["open" if sys.platform == "darwin" else "xdg-open", str(project_path)])
            return {"opened": app}
        raise RuntimeError("Desktop app controls require Windows.")
    system = Path(os.getenv("SystemRoot", "C:/Windows"))
    commands = {"notepad": [str(system / "System32/notepad.exe")],
                "calculator": [str(system / "System32/calc.exe")],
                "explorer": [str(system / "explorer.exe"), str(project_path)]}
    if app not in commands:
        raise ValueError("Supported apps: vscode, notepad, calculator, explorer. Use open_url for the browser.")
    p = subprocess.Popen(commands[app], shell=False)
    return {"opened": app, "pid": p.pid}


def list_windows():
    if os.name != "nt":
        raise RuntimeError("Window controls require Windows.")
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    user32.IsWindowVisible.argtypes = [wintypes.HWND]
    user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
    user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    items = []
    callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    @callback_type
    def callback(hwnd, _):
        if user32.IsWindowVisible(hwnd):
            length = user32.GetWindowTextLengthW(hwnd)
            if length:
                buf = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buf, length + 1)
                pid = wintypes.DWORD()
                user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                if pid.value != os.getpid():
                    items.append({"handle": int(hwnd), "pid": pid.value, "title": buf.value})
        return True
    user32.EnumWindows.argtypes = [callback_type, wintypes.LPARAM]
    user32.EnumWindows(callback, 0)
    return {"windows": items}


def close_window(handle, expected_title):
    windows = list_windows()["windows"]
    match = next((x for x in windows if x["handle"] == int(handle) and x["title"] == expected_title), None)
    if not match:
        raise ValueError("Window changed or closed. List windows again.")
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    user32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
    if not user32.PostMessageW(int(handle), 0x0010, 0, 0):
        raise OSError("Windows rejected the close request.")
    return {"close_requested": expected_title, "note": "An unsaved-changes dialog may still need your response."}
