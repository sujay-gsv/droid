from __future__ import annotations
import ctypes
import json
import os
from pathlib import Path
import queue
import re
import threading
import time


def wake_command(text, armed=False, word="jarvis"):
    match = re.match(r"^(?:hey\s+)?" + re.escape(word) + r"\b[\s,.:;-]*(.*)$", text.strip(), re.I)
    return match.group(1).strip() if match else (text.strip() if armed else None)


class Voice:
    def __init__(self, model_path, on_text, on_status):
        self.model_path = Path(model_path)
        self.on_text, self.on_status = on_text, on_status
        self.stop = threading.Event()
        self.speaking = threading.Event()
        self.listening = False
        self.speech = queue.Queue()
        self.mic_thread = None
        threading.Thread(target=self._speak_loop, daemon=True).start()

    def say(self, text):
        # Voice stays short; screen contains the complete answer.
        clean = re.sub(r"[`*#]", "", text)
        clean = re.sub(r"https?://\S+", "the link shown on screen", clean)
        sentences = re.split(r"(?<=[.!?])\s+", clean.strip())
        self.speech.put(" ".join(sentences[:2])[:350])

    def _speak_loop(self):
        engine = None
        if os.name == "nt":
            ctypes.windll.ole32.CoInitialize(None)
        while not self.stop.is_set():
            try:
                text = self.speech.get(timeout=.3)
            except queue.Empty:
                continue
            try:
                if engine is None:
                    import pyttsx3
                    engine = pyttsx3.init()
                    engine.setProperty("rate", 180)
                self.speaking.set()
                engine.say(text)
                engine.runAndWait()
            except Exception as exc:
                self.on_status("Speech unavailable. Run setup_voice.bat. " + str(exc)[:120])
            finally:
                self.speaking.clear()
        if os.name == "nt":
            ctypes.windll.ole32.CoUninitialize()

    def start(self):
        if self.mic_thread and self.mic_thread.is_alive():
            self.listening = True
            return
        self.listening = True
        self.mic_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.mic_thread.start()

    def pause(self):
        self.listening = False

    def _listen_loop(self):
        try:
            import sounddevice as sd
            from vosk import Model, KaldiRecognizer, SetLogLevel
            if not self.model_path.is_dir():
                raise RuntimeError("Voice model missing. Run setup_voice.bat first.")
            SetLogLevel(-1)
            model = Model(str(self.model_path))
            audio = queue.Queue(maxsize=30)
            def callback(data, frames, when, status):
                if not self.speaking.is_set():
                    try:
                        audio.put_nowait(bytes(data))
                    except queue.Full:
                        pass
            armed_until = 0
            with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype="int16", channels=1, callback=callback):
                rec = KaldiRecognizer(model, 16000)
                self.on_status("Microphone on. Say 'Jarvis' followed by your request.")
                while not self.stop.is_set() and self.listening:
                    try:
                        chunk = audio.get(timeout=.3)
                    except queue.Empty:
                        continue
                    if self.speaking.is_set():
                        rec.Reset()
                        continue
                    if rec.AcceptWaveform(chunk):
                        text = json.loads(rec.Result()).get("text", "")
                        if not text:
                            continue
                        command = wake_command(text, time.monotonic() < armed_until)
                        if command == "":
                            armed_until = time.monotonic() + 8
                            self.on_status("Listening for your request...")
                        elif command:
                            armed_until = 0
                            self.on_text(command)
        except Exception as exc:
            self.on_status("Microphone unavailable: " + str(exc))
        finally:
            self.listening = False

    def close(self):
        self.stop.set()
        self.listening = False
