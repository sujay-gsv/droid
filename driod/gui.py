from __future__ import annotations
from datetime import datetime
import json
import os
from pathlib import Path
import queue
import shutil
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText
import webbrowser

from .agent import Agent, redact
from .extras import Extras, DISCLAIMER
from .provider import OpenRouter
from .tools import Toolbox
from .voice import Voice
from .workspace import Workspace

APP_DIR = Path(__file__).resolve().parent.parent
STATE = Path.home() / ".driod"
BG, PANEL, TEXT, MUTED, ACCENT = "#101820", "#192631", "#ecf3f6", "#9cafbd", "#71dec5"


class App:
    def __init__(self):
        STATE.mkdir(exist_ok=True)
        self.config_path = STATE / "settings.json"
        try:
            self.config = json.loads(self.config_path.read_text(encoding="utf-8"))
        except (FileNotFoundError, ValueError):
            self.config = {}
        self.key = os.environ.get("OPENROUTER_API_KEY", "")
        self.events = queue.Queue()
        self.stop = threading.Event()
        self.busy = False
        self.closing = False
        self.agent = None
        self.confirm_dialog = None
        self.confirm_result = None
        self.voice_on = False
        self.root = tk.Tk()
        self.root.title("Driod · Personal AI Agent")
        self.root.geometry("1120x780")
        self.root.minsize(820, 620)
        self.root.configure(bg=BG)
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.status = tk.StringVar(value="Ready · typed commands available")
        self.speak = tk.BooleanVar(value=self.config.get("speak", False))
        self._build_ui()
        self.setup_workspace(self.config.get("workspace", str(Path.home() / "DriodProjects")))
        model_path = Path(self.config.get("voice_model", str(APP_DIR / "voice-model")))
        self.voice = Voice(model_path, lambda text: self.emit("voice", text), lambda text: self.emit("status", text))
        self.say_screen("Driod", "At your service. I can build projects, work with files, and help run your desktop.\n\n1. Open Settings and enter your OpenRouter key and model.\n2. Type a request below, or install voice and turn on the microphone.\n3. Review actions when prompted.\n\nTry: Create an Amazon-style shopping website with search, categories and a working cart. Test it, fix errors, open it in VS Code and show the result.\n\nUse Try demo to see a working local store without an API key.")
        self.root.after(100, self.pump)
        self.root.after(2000, self.tick_reminders)
        self.root.after(15000, self.tick_prices)

    def button(self, parent, text, command, accent=False):
        return tk.Button(parent, text=text, command=command, bg=ACCENT if accent else "#263946",
                         fg=BG if accent else TEXT, relief="flat", padx=13, pady=9,
                         activebackground="#45cbae", activeforeground=BG, cursor="hand2", font=("Segoe UI", 10))

    def _build_ui(self):
        left = tk.Frame(self.root, bg=PANEL, width=220)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)
        tk.Label(left, text="D R I O D", font=("Segoe UI", 25, "bold"), fg=ACCENT, bg=PANEL).pack(anchor="w", padx=20, pady=(28, 4))
        tk.Label(left, text="YOUR PERSONAL AI AGENT", font=("Segoe UI", 8), fg=MUTED, bg=PANEL).pack(anchor="w", padx=20, pady=(0, 26))
        for label, command in [("Settings / API key", self.settings), ("Choose project folder", self.choose_workspace),
                               ("Import files", self.import_files), ("Open project in VS Code", self.open_editor),
                               ("Try demo store", self.demo), ("New chat", self.new_chat)]:
            self.button(left, label, command).pack(fill="x", padx=16, pady=4)
        self.mic_button = self.button(left, "Microphone: OFF", self.toggle_voice)
        self.mic_button.pack(fill="x", padx=16, pady=(22, 4))
        tk.Checkbutton(left, text="Speak replies", variable=self.speak, bg=PANEL, fg=TEXT, selectcolor=BG,
                       activebackground=PANEL, activeforeground=TEXT, command=self.save_config).pack(anchor="w", padx=16)
        self.button(left, "STOP current task", self.stop_task).pack(fill="x", padx=16, pady=16)
        self.folder_label = tk.Label(left, text="", wraplength=182, justify="left", bg=PANEL, fg=MUTED, font=("Segoe UI", 9))
        self.folder_label.pack(side="bottom", anchor="w", padx=18, pady=20)
        main = tk.Frame(self.root, bg=BG)
        main.pack(side="left", fill="both", expand=True, padx=20, pady=18)
        tk.Label(main, text="What shall we build?", font=("Segoe UI", 21, "bold"), fg=TEXT, bg=BG).pack(anchor="w", pady=(0, 4))
        tk.Label(main, textvariable=self.status, font=("Segoe UI", 10), fg=ACCENT, bg=BG).pack(anchor="w", pady=(0, 14))
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TNotebook", background=BG, borderwidth=0)
        style.configure("TNotebook.Tab", background=PANEL, foreground=TEXT, padding=(16, 8))
        style.map("TNotebook.Tab", background=[("selected", "#304654")])
        self.tabs = ttk.Notebook(main)
        self.tabs.pack(fill="both", expand=True)
        self.chat = ScrolledText(self.tabs, bg=BG, fg=TEXT, font=("Segoe UI", 11), wrap="word", relief="flat", padx=15, pady=16, state="disabled")
        self.activity = ScrolledText(self.tabs, bg=BG, fg=MUTED, font=("Consolas", 10), wrap="word", relief="flat", state="disabled")
        self.files = tk.Listbox(self.tabs, bg=BG, fg=TEXT, font=("Consolas", 11), relief="flat", selectbackground="#304654")
        self.files.bind("<Double-Button-1>", self.open_selected)
        self.tabs.add(self.chat, text="Conversation")
        self.tabs.add(self.activity, text="Activity / errors")
        self.tabs.add(self.files, text="Project files")
        self.input = tk.Text(main, height=4, bg=PANEL, fg=TEXT, insertbackground=ACCENT, relief="flat", padx=12, pady=12, font=("Segoe UI", 11), wrap="word")
        self.input.pack(fill="x", pady=(16, 8))
        self.input.bind("<Control-Return>", lambda e: self.submit())
        row = tk.Frame(main, bg=BG)
        row.pack(fill="x")
        tk.Label(row, text="Ctrl + Enter to send · actions appear in Activity", bg=BG, fg=MUTED, font=("Segoe UI", 9)).pack(side="left")
        self.send_button = self.button(row, "Send request  →", self.submit, True)
        self.send_button.pack(side="right")

    def setup_workspace(self, path):
        self.ws = Workspace(Path(path), STATE)
        self.toolbox = Toolbox(self.ws, self.approve, self.emit, self.stop)
        self.extras = Extras(self.toolbox)
        self.toolbox.extra = self.extras
        self.agent = None
        self.folder_label.config(text="PROJECT FOLDER\n" + str(self.ws.root))
        self.refresh_files()

    def emit(self, event, value):
        self.events.put((event, value))

    def say_screen(self, who, text):
        text = redact(str(text), [self.key])
        self.chat.configure(state="normal")
        self.chat.insert("end", f"{who}  ·  {datetime.now():%H:%M}\n{text}\n\n")
        self.chat.see("end")
        self.chat.configure(state="disabled")

    def log(self, text):
        self.activity.configure(state="normal")
        self.activity.insert("end", redact(str(text), [self.key]) + "\n\n")
        self.activity.see("end")
        self.activity.configure(state="disabled")

    def pump(self):
        try:
            for _ in range(100):
                event, value = self.events.get_nowait()
                if event in {"answer", "error", "thought_summary"}:
                    self.say_screen("Driod" if event != "error" else "Error", value)
                    if event == "answer" and self.speak.get():
                        self.voice.say(value)
                elif event == "status":
                    self.status.set(value)
                    if value.startswith("Microphone unavailable"):
                        self.voice_on = False
                        self.mic_button.config(text="Microphone: OFF")
                elif event in {"tool_start", "tool_result", "usage"}:
                    self.log(value)
                    if event == "tool_start":
                        self.status.set("Working · " + value.split(" ", 1)[0])
                elif event == "refresh":
                    self.refresh_files()
                elif event == "done":
                    self.busy = False
                    self.send_button.config(state="normal")
                    self.status.set("Ready · work saved")
                elif event == "confirm":
                    self.show_confirmation(*value)
                elif event == "callback":
                    value()
                elif event == "voice":
                    if value.lower() in {"stop", "cancel", "stop task"}:
                        self.stop_task()
                    elif not self.busy:
                        self.input.delete("1.0", "end")
                        self.input.insert("1.0", value)
                        self.submit()
                    else:
                        self.say_screen("Voice", "I heard: " + value + "\nA task is already running. Say 'Jarvis stop' to interrupt it.")
                elif event == "alert":
                    self.say_screen("Alert", value)
                    self.root.bell()
                    if self.speak.get():
                        self.voice.say(value)
        except queue.Empty:
            pass
        if not self.closing:
            self.root.after(100, self.pump)

    def approve(self, title, details):
        signal = threading.Event()
        result = {"approved": False}
        self.emit("confirm", (title, details, signal, result))
        while not signal.wait(.1):
            if self.stop.is_set() or self.closing:
                return False
        return result["approved"] and not self.stop.is_set()

    def show_confirmation(self, title, details, signal, result):
        if self.stop.is_set() or self.closing:
            signal.set()
            return
        dialog = tk.Toplevel(self.root)
        self.confirm_dialog = dialog
        dialog.title(title)
        dialog.geometry("740x480")
        dialog.configure(bg=BG)
        dialog.transient(self.root)
        dialog.grab_set()
        tk.Label(dialog, text=title, bg=BG, fg=TEXT, font=("Segoe UI", 17, "bold")).pack(anchor="w", padx=18, pady=16)
        body = ScrolledText(dialog, bg=PANEL, fg=TEXT, font=("Consolas", 10), wrap="word")
        body.pack(fill="both", expand=True, padx=18)
        body.insert("1.0", redact(details, [self.key]))
        body.configure(state="disabled")
        row = tk.Frame(dialog, bg=BG)
        row.pack(fill="x", padx=18, pady=16)
        def finish(value):
            result["approved"] = value
            signal.set()
            self.confirm_dialog = None
            self.confirm_result = None
            dialog.destroy()
        self.confirm_result = lambda: finish(False)
        self.button(row, "Approve this action", lambda: finish(True), True).pack(side="right")
        deny = self.button(row, "Decline", lambda: finish(False))
        deny.pack(side="right", padx=10)
        deny.focus_set()
        dialog.protocol("WM_DELETE_WINDOW", lambda: finish(False))
        dialog.bind("<Escape>", lambda e: finish(False))
        self.status.set("Waiting for your confirmation")

    def background(self, fn):
        def work():
            try:
                fn()
            except Exception as exc:
                self.emit("error", redact(str(exc), [self.key]))
            finally:
                self.emit("done", None)
        self.busy = True
        self.send_button.config(state="disabled")
        self.stop.clear()
        threading.Thread(target=work, daemon=True).start()

    def submit(self):
        if self.busy:
            return
        text = self.input.get("1.0", "end").strip()
        if not text:
            return
        if not self.key or not self.config.get("model"):
            self.settings()
            return
        if self.agent is None:
            self.agent = Agent(OpenRouter(self.key, self.config["model"], self.config.get("max_tokens", 12000)),
                               self.toolbox, self.emit, self.config.get("max_steps", 40))
        self.input.delete("1.0", "end")
        self.say_screen("You", text)
        if self.speak.get():
            self.voice.say("On it. I'll show the details on screen.")
        self.background(lambda: self.agent.run(text))

    def stop_task(self):
        self.stop.set()
        if self.confirm_result:
            self.confirm_result()
        self.status.set("Stopping · an API request may take up to 90 seconds to finish")

    def refresh_files(self):
        self.files.delete(0, "end")
        try:
            for item in self.ws.list_files()["entries"]:
                self.files.insert("end", item["path"] + ("/" if item["type"] == "folder" else ""))
        except Exception as exc:
            self.log(str(exc))

    def open_selected(self, event=None):
        selected = self.files.curselection()
        if selected and not self.busy:
            path = self.files.get(selected[0]).rstrip("/")
            p = self.ws.path(path)
            if p.suffix.lower() in {".png", ".jpg", ".jpeg"}:
                if os.name == "nt":
                    os.startfile(str(p))
                else:
                    webbrowser.open(p.as_uri())
            else:
                self.background(lambda: self.emit("tool_result", self.toolbox.open_in_vscode(path)))

    def open_editor(self):
        if not self.busy:
            self.background(lambda: self.emit("tool_result", self.toolbox.open_in_vscode(".")))

    def choose_workspace(self):
        if self.busy:
            messagebox.showinfo("Task running", "Stop the current task before changing projects.")
            return
        path = filedialog.askdirectory(title="Choose the folder Driod may read and edit")
        if path:
            if not messagebox.askyesno("Use this project folder?", path + "\n\nDriod may read its non-hidden files and send requested file content to your AI provider. Choose a project folder, not your whole user folder."):
                return
            self.toolbox.close()
            try:
                self.setup_workspace(path)
                self.config["workspace"] = str(self.ws.root)
                self.save_config()
            except Exception as exc:
                self.setup_workspace(str(Path.home() / "DriodProjects"))
                messagebox.showerror("Project folder", str(exc))

    def import_files(self):
        if self.busy:
            return
        paths = filedialog.askopenfilenames(title="Import files into this project; content may be sent to your AI provider when read")
        for path in paths:
            try:
                relative = self.ws.import_file(Path(path))
                self.say_screen("Imported", relative)
            except Exception as exc:
                messagebox.showerror("Import", str(exc))
        self.refresh_files()

    def new_chat(self):
        if not self.busy:
            self.agent = None
            self.say_screen("Driod", "Fresh conversation. Your files, backups and local reminders are still here.")

    def toggle_voice(self):
        self.voice_on = not self.voice_on
        if self.voice_on:
            self.voice.start()
        else:
            self.voice.pause()
            self.status.set("Microphone off")
        self.mic_button.config(text="Microphone: " + ("ON · Jarvis" if self.voice_on else "OFF"))

    def save_config(self):
        self.config["speak"] = self.speak.get()
        self.config_path.write_text(json.dumps(self.config, indent=2), encoding="utf-8")

    def settings(self):
        if self.busy:
            messagebox.showinfo("Task running", "Stop the current task before changing Settings.")
            return
        dialog = tk.Toplevel(self.root)
        dialog.title("Driod settings")
        dialog.geometry("680x540")
        dialog.configure(bg=BG)
        dialog.transient(self.root)
        fields = tk.Frame(dialog, bg=BG)
        fields.pack(fill="both", expand=True, padx=24, pady=22)
        tk.Label(fields, text="Connect your AI", fg=TEXT, bg=BG, font=("Segoe UI", 19, "bold")).pack(anchor="w")
        tk.Label(fields, text="OpenRouter API key · kept in memory for this session", fg=MUTED, bg=BG).pack(anchor="w", pady=(18, 5))
        key = tk.Entry(fields, show="•", font=("Segoe UI", 11), bg=PANEL, fg=TEXT, insertbackground=TEXT)
        key.insert(0, self.key)
        key.pack(fill="x", ipady=6)
        tk.Label(fields, text="Model ID · choose a model that supports tools", fg=MUTED, bg=BG).pack(anchor="w", pady=(18, 5))
        model = ttk.Combobox(fields, font=("Segoe UI", 11))
        model.set(self.config.get("model", ""))
        model.pack(fill="x", ipady=5)
        feedback = tk.StringVar(value="Loading models uses OpenRouter's current catalog. API usage may cost credits.")
        def load_models():
            entered_key = key.get().strip()
            if not entered_key:
                feedback.set("Enter your API key first.")
                return
            feedback.set("Loading tool-capable models...")
            def fetch():
                try:
                    names = OpenRouter(entered_key, "catalog").models()
                    def update():
                        if dialog.winfo_exists():
                            model["values"] = names
                            feedback.set(f"{len(names)} tool-capable models found. Choose one or type its ID.")
                    self.emit("callback", update)
                except Exception as exc:
                    msg = redact(str(exc), [entered_key])
                    self.emit("callback", lambda: feedback.set(msg) if dialog.winfo_exists() else None)
            threading.Thread(target=fetch, daemon=True).start()
        self.button(fields, "Load models", load_models).pack(anchor="w", pady=10)
        tk.Label(fields, textvariable=feedback, wraplength=620, justify="left", fg=MUTED, bg=BG).pack(anchor="w")
        tk.Label(fields, text="Max output tokens per call", fg=MUTED, bg=BG).pack(anchor="w", pady=(14, 3))
        tokens = tk.Entry(fields)
        tokens.insert(0, str(self.config.get("max_tokens", 12000)))
        tokens.pack(anchor="w")
        tk.Label(fields, text="Your requests, files read by tools and tool results go to OpenRouter and the chosen model provider.\nThe API key is not saved to disk by Driod. Use OPENROUTER_API_KEY for an environment-based key.\nA task can make up to 40 model calls. Stop is available at any time.", fg=MUTED, bg=BG, wraplength=620, justify="left").pack(anchor="w", pady=16)
        def save():
            try:
                count = int(tokens.get())
                if not 1000 <= count <= 32000:
                    raise ValueError()
            except ValueError:
                messagebox.showerror("Tokens", "Choose an output limit from 1000 to 32000.", parent=dialog)
                return
            self.key = key.get().strip()
            self.config["model"] = model.get().strip()
            self.config["max_tokens"] = count
            self.save_config()
            self.agent = None
            dialog.destroy()
            self.status.set("Settings saved · ready")
        self.button(fields, "Save settings", save, True).pack(anchor="e")

    def demo(self):
        if self.busy:
            return
        def run():
            target = "demo-store-" + datetime.now().strftime("%H%M%S")
            for p in (APP_DIR / "examples" / "store").glob("*"):
                self.ws.write_file(target + "/" + p.name, p.read_text(encoding="utf-8"))
            url = self.toolbox.start_preview(target)["url"]
            try:
                self.toolbox.open_in_vscode(target)
            except Exception as exc:
                self.emit("tool_result", str(exc))
            self.toolbox.open_url(url)
            self.emit("answer", f"Demo store created in {target}.\nPreview: {url}\nIt includes search, categories and a working local cart. Checkout is a demo.\nAsk me to change it after connecting your API key.")
        self.background(run)

    def tick_reminders(self):
        # Nonblocking: never freeze Tk while a tool waits for its confirmation.
        if self.extras.data_lock.acquire(blocking=False):
            try:
                for reminder in self.extras.due_reminders():
                    self.emit("alert", reminder["text"])
            except Exception as exc:
                self.log("Reminder check: " + str(exc))
            finally:
                self.extras.data_lock.release()
        if not self.closing:
            self.root.after(1000, self.tick_reminders)

    def tick_prices(self):
        if not self.busy:
            try:
                holdings = self.extras._load("portfolio")
            except Exception:
                holdings = []
            def check():
                try:
                    import yfinance as yf
                    for entry in holdings:
                        if self.closing or (entry.get("above") is None and entry.get("below") is None):
                            continue
                        stock = yf.Ticker(entry["ticker"])
                        history = stock.history(period="1d", interval="1m", timeout=15)
                        interval = "1-minute"
                        if history.empty:
                            history = stock.history(period="5d", interval="1d", timeout=15)
                            interval = "daily"
                        if history.empty:
                            continue
                        price = float(history["Close"].iloc[-1])
                        for direction in ("above", "below"):
                            threshold = entry.get(direction)
                            hit = threshold is not None and (price >= threshold if direction == "above" else price <= threshold)
                            if hit:
                                self.emit("alert", f"{entry['ticker']} latest available {interval} price {price:.2f} is {direction} {threshold}. Bar: {history.index[-1]}. {DISCLAIMER}")
                                self.emit("callback", lambda symbol=entry["ticker"], direction=direction, threshold=threshold: self.clear_threshold(symbol, direction, threshold))
                except Exception as exc:
                    self.emit("tool_result", "Price alert check unavailable: " + str(exc)[:200])
            if holdings:
                threading.Thread(target=check, daemon=True).start()
        if not self.closing:
            self.root.after(300000, self.tick_prices)

    def clear_threshold(self, ticker, direction, old_threshold):
        # Do not overwrite edits made since the background quote request started.
        if self.busy:
            self.root.after(1000, lambda: self.clear_threshold(ticker, direction, old_threshold))
            return
        holdings = self.extras._load("portfolio")
        for entry in holdings:
            if entry["ticker"] == ticker and entry.get(direction) == old_threshold:
                entry[direction] = None
        self.extras._save("portfolio", holdings)

    def close(self):
        if not messagebox.askyesno("Exit Driod?", "Stop the current task, microphone, local previews and Driod-started command processes, then exit?"):
            return
        self.closing = True
        self.stop_task()
        self.voice.close()
        self.save_config()
        # Keep Tk responsive until process cleanup finishes.
        def cleanup():
            self.toolbox.close()
            self.events.put(("callback", self.root.destroy))
        threading.Thread(target=cleanup, daemon=True).start()
        def finish():
            try:
                while True:
                    event, value = self.events.get_nowait()
                    if event == "callback":
                        value()
                        if not self.root.winfo_exists():
                            return
            except (queue.Empty, tk.TclError):
                pass
            try:
                self.root.after(100, finish)
            except tk.TclError:
                pass
        self.root.after(100, finish)

    def run(self):
        self.root.mainloop()
