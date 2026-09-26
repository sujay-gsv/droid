# Driod — your personal AI agent

Driod is a Windows desktop app that turns typed or spoken requests into local tool calls. It can create project files, open VS Code, run approved commands, inspect website errors, and keep working from the results. The app is named **Driod**; its voice wake word is **Jarvis**, as requested.

This is a runnable source project, not an installed Windows executable or a connection from ChatGPT to your computer. It needs Python, your own OpenRouter key, and a model with tool calling. Model quality affects how well complex requests succeed. It cannot guarantee arbitrary tasks, flawless code, or an exact recreation of a website from a short description.

## Start here — Windows

1. **Extract the ZIP.** Right-click `Driod-Windows.zip` → **Extract All** → **Extract**. Open the extracted `Driod` folder. Do not run the scripts inside the ZIP viewer.
2. **Install Python** if needed. Use Python **3.11 or 3.12**, 64-bit, from [python.org](https://www.python.org/downloads/windows/). Check **Add python.exe to PATH** during installation. The source requires Python 3.10 or later.
3. **Install VS Code** from [code.visualstudio.com](https://code.visualstudio.com/). Select **Add to PATH** during setup. Restart Driod after installing it.
4. Double-click **`setup.bat`**. It creates a virtual environment, installs the core packages and downloads Chromium for website checks. Allow time for downloads. It reports errors rather than silently continuing.
5. Double-click **`start.bat`**. The Driod window opens.
6. Click **Settings / API key**. Paste your **OpenRouter** API key into the masked field. Click **Load models**, select a tool-capable model, and click **Save settings**. You can also paste an exact model ID from OpenRouter's current catalog. A model ID is not an API key.
7. Type a request and click **Send request**, or press **Ctrl + Enter**.

API calls use your OpenRouter account and may consume credits. Driod does not include API credits. A task can make up to 40 model calls; it stops at that limit and you can ask it to continue. The output limit is adjustable in Settings. The API key is kept in memory for the app session, not saved by Driod. Alternatively, supply your own `OPENROUTER_API_KEY` environment variable.

**Try it without a key:** click **Try demo store**. This copies the included sample into a new project folder, starts a local web server, and offers to open the preview. VS Code is optional for this demo. Search, categories, the shopping bag, quantity changes, and demo checkout are implemented in the sample. It has no real payments or Amazon connection.

## Add voice

1. Close Driod, run **`setup_voice.bat`**, then reopen `start.bat`.
2. Enable **Speak replies** and click **Microphone: OFF** to switch listening on.
3. Say: **“Jarvis, open calculator.”** Pause after your sentence so recognition can finish.
4. You can also say **“Jarvis”**, pause, then give your request within eight seconds.
5. Say **“Jarvis stop”** or click **STOP current task** to request cancellation.

Voice recognition uses an official small English Vosk model and runs locally. Speech uses the system voice through pyttsx3/SAPI on Windows; voice quality depends on the installed system voices. Driod speaks up to two short sentences and shows details on screen. Audio is not sent to OpenRouter, but the recognized command text is. Microphone access is off by default. Recognition accuracy depends on your microphone, accent, noise, and model; use typed commands if needed.

The voice download is about 40 MB. To use a different compatible Vosk model, set `voice_model` in your local Driod settings JSON to its extracted folder. This build has no voiceprint authentication: anyone near an enabled microphone may submit a request. Sensitive actions still require approval in the app window.

## Add screen controls

Run **`setup_desktop.bat`**, then restart Driod. This enables screenshots, mouse clicks, keyboard shortcuts, typing, scrolling, volume-key steps, and brightness control where supported by the hardware.

OCR additionally needs the **Tesseract application**, not just its Python wrapper. Follow the Windows installation links in the [Tesseract documentation](https://tesseract-ocr.github.io/tessdoc/Installation.html). Driod checks the usual `C:\Program Files\Tesseract-OCR\tesseract.exe` location, then your PATH. Without Tesseract, screenshots still work but OCR reports an error.

Every screen action displays a confirmation. OCR tells you before captured text is sent to the AI provider. Screenshots are saved locally under your project’s `reports` folder; the app does not automatically upload the image to the model. The model can use OCR text for screen reading, but this build has no general screenshot-vision loop. Desktop typing supports ASCII; file writing supports Unicode. Some protected/elevated windows reject automation. Keep Driod running as a normal user.

**Emergency stop for mouse/keyboard:** move your pointer into a corner of the primary screen to activate PyAutoGUI’s fail-safe. Use Driod’s Stop button as well.

## What is included

| Area | Implemented behavior | Practical limits |
|---|---|---|
| Files | Create directories/files, read and replace text, rename, import assets, list backups, restore | File tools stay inside the selected project; text files up to 250 KB; imports up to 25 MB |
| Desktop apps | Open VS Code, Notepad, Calculator, Explorer; list windows; request window close | Windows integration; closing asks first; save dialogs remain for you to answer |
| Development | Open project/file in VS Code; approved PowerShell commands for installs, builds, tests and git; process logs; fix from errors | Language toolchains, Node, Git and GitHub CLI must be installed when needed; no guarantee every bug can be fixed |
| Websites | Static localhost preview, temporary Chromium checks, CSS-selector interactions, browser errors, screenshots | Browser install required; external network requests are blocked in checks by default unless explicitly approved |
| Voice | Local English speech recognition, Jarvis wake word, system TTS | Optional packages/model; no always-running Windows service |
| Research | Web/news search and public HTML/text extraction with source URLs | Sites may block access; no paywall or sign-in bypass; downloaded PDF extraction is not built in |
| Finance | Latest available 1-minute quote when available; daily history chart; SMA20/50, EMA20, Wilder RSI14, MACD; volume and available fundamentals | Yahoo data can be delayed/unavailable; no guaranteed real-time exchange feed; unavailable fields are not invented |
| Portfolio | Persist ticker, quantity, per-unit cost basis and price thresholds | No broker account or trading integration; compare values through analysis requests |
| Alerts | Reminders and one-shot price threshold notifications | App must stay open; prices checked roughly every 5 minutes when idle; overdue reminders appear on the next launch |
| Productivity | Local to-dos, DOCX documents, XLSX tables, PPTX slides, `.eml` email drafts, `.ics` calendar files | Basic document layouts; no email sending or external calendar sync; open drafts/import calendar files yourself |

News sentiment, comparisons and explanations come from the selected model using actual retrieved sources. They are not separate trained sentiment or trading systems. All financial summaries must include **“Not financial advice”**, with timestamps and data-delay context.

## Useful requests

- “Create an Amazon-style shopping website named MyStore with product search, categories and a working cart. Open it in VS Code, check desktop and mobile layouts, fix errors and show the result. Make checkout a clearly labelled demo.”
- “Inspect my project, run its existing tests, fix the first failing test and run it again.”
- “Create `notes/today.txt` and write these notes into it: …”
- “Find backups of `MyStore/index.html` and restore the previous version.”
- “Open Notepad.” / “List my open windows, then close the Calculator window.”
- “Take a screenshot.” / “Read the screen using OCR.”
- “Research the latest Python documentation for pathlib and show the source links.”
- “Analyze RELIANCE.NS and TCS.NS over six months. Compare SMA, RSI and MACD, show the data timestamps and save charts.”
- “Track 3 shares of AAPL bought at 180 per share and alert when the latest available price rises above 220.”
- “Remind me in 20 minutes to check my build.”
- “Make a to-do: review the shopping cart.”
- “Create `reports/meeting-notes.docx` from these notes: …”
- “Create an email draft to person@example.com about the project. Save it as `drafts/project.eml`.”
- “Create a calendar file for a meeting on 28 September 2026, 3–4 pm India time. Save it as `events/review.ics`.”

## How website building works

Driod sends your request and the tool definitions to your model. The model asks for file writes and other tool calls; Python executes the allowed actions and returns the real results. A typical task creates the files, opens VS Code, starts a preview, checks JavaScript/HTTP errors and interactions, edits failures, checks again, and opens the result. Actual tool results appear in **Activity / errors**. Your selected model must follow the workflow; use a capable coding model and specific acceptance criteria.

The browser checker supports `click`, `fill`, `press`, `assert_text`, and `assert_count` steps. Each check starts a fresh temporary browser session, so put dependent interactions in one check. Screenshot files appear in **Project files**; double-click a PNG to view it. Static previews stay running until Driod exits or you switch projects. For React/Vite or a backend, the agent uses approved `start_process` commands and checks their logs. Those processes run locally.

Driod changes files directly, which VS Code displays. It does not need to pretend to type every character into the editor. Save your manual editor changes before asking Driod to edit the same file; unsaved editor buffers are not visible to file tools.

## Confirmations, privacy and storage

- New project files and routine reversible edits run without repeated prompts. Existing text files must first be read; a changed hash prevents overwriting external edits. Overwritten/renamed files get backup copies.
- Shell commands, process termination, window closing, file restoration, desktop actions, opening web pages and browser checks show confirmations. All shell commands are reviewed, including git pushes/merges, package installation and deletion commands. Declining an action returns a denial to the agent.
- **Approved commands are not sandboxed.** They run as your Windows user and can affect files/network beyond the project directory. Inspect the command and referenced scripts before approving. Driod does not silently grant administrator privileges.
- File tools block paths outside your chosen project and hide dotfiles and common secret filenames. To work elsewhere, choose another project folder or use Import files. Do not choose your entire home folder or import secrets.
- Your prompts, requested file contents, tool output, search requests, and approved OCR text may be sent to OpenRouter and the selected provider. Local speech recognition does not send audio there.
- Driod does not save your API key in settings. Known API keys and common credential patterns are redacted from logs and responses; do not paste secrets into commands, project files or chat. Redaction is not a comprehensive data-loss prevention system.
- The default project directory is `%USERPROFILE%\DriodProjects`. Driod’s settings, command/session history, local reminders, holdings, process logs and backups are in `%USERPROFILE%\.driod`. History records tool requests, executed commands, timestamps and result summaries. These local logs can contain other personal task content.
- Stop prevents further tool actions and terminates the active finite command where possible. An in-flight network/API request may take up to its timeout to return. Stop does not undo completed edits or remove already-started background servers. Exiting confirms and stops Driod-started processes/previews. To undo an edit, ask for file backups and restore one.
- No email, social posting, external calendar booking or spending occurs automatically. Email/calendar output is a local draft/file. If you use shell commands or desktop clicks for an external action, review and explicitly confirm the exact action.

## Troubleshooting

| Problem | What to do |
|---|---|
| Nothing opens | Extract the ZIP first. Run `setup.bat`, then `start.bat`; read any terminal error. Run `doctor.bat`. |
| Python not found | Install Python 3.11/3.12 with Add to PATH, reopen the folder and retry. |
| Invalid API key / 401 | Use an OpenRouter key in Settings, not a key from another service. Do not share the key in chat. |
| Insufficient credits / 402 | Check your OpenRouter balance and model spending limits. |
| Model not found / no tool support | Click Load models and select another model from the current tool-capable list. |
| Context or output limit error | Start a New chat, ask for smaller files/tasks, or adjust Max output tokens to the model’s supported range. Your files remain saved. |
| VS Code not found | Install stable VS Code with Add to PATH; restart Driod. Portable/Insiders installations may need a custom command after approval. |
| Chromium missing | Run `setup_browser.bat`. If downloads fail, check your network/proxy and retry later. |
| Preview appears but test fails | Inspect Activity. A failing HTTP request, console error, assertion or blocked external resource makes a check fail. Ask Driod to fix that specific issue. |
| `No module named …` | Run the relevant setup script: core, voice, or desktop. Restart Driod. |
| Voice does not hear Jarvis | Confirm Windows microphone permission/default input, run voice setup, reduce noise and pause after speaking. Typed commands remain available. |
| No spoken reply | Enable Speak replies, run voice setup and check your default audio device. |
| OCR says Tesseract not found | Install the Tesseract application as described above. |
| Brightness fails | Some monitors/drivers do not expose brightness controls. Use your monitor controls. |
| Stock data fails | Verify the ticker/exchange suffix and retry later. Driod must report unavailable data, not invent it. |

## Tests and validation

Run `test.bat`, or:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

**Validated in the build environment:** 26 tests passed, including path boundaries, overwrite conflicts, backups/restoration, declined-action side effects, command execution/timeouts/cancellation, managed processes, HTTP preview serving, a simulated multi-step model/tool loop, malformed JSON recovery, Chat Completions request format, secret redaction, indicator calculations, wake-word parsing, persistent to-dos/reminders/portfolio entries, timezone conversion, email drafts and Office file round-trips. Python compilation and JavaScript syntax checks passed.

**Not validated here:** a real OpenRouter generation (no user key supplied), Windows desktop/PowerShell/VS Code integration, actual microphone/TTS/hardware, GUI rendering, live Yahoo/search requests, or real Chromium interaction. The Chromium download failed in this environment, so the browser test class was explicitly skipped. The included two browser tests cover search/cart/demo checkout, mobile loading, and detection/repair of a JavaScript error when Chromium is available on your machine. A simulated model loop is not evidence that a particular remote model will complete every task.

This release should be tried in a small project folder before using it for important work. See `VALIDATION.md` for the precise build check summary.

## Project map

- `main.py`: launch the desktop app.
- `driod/gui.py`: chat, settings, file picker, approvals, notifications.
- `driod/agent.py`: tool-calling loop, behavior prompt and audit log.
- `driod/provider.py`: OpenRouter Chat Completions integration. It sends conversation messages directly and does not use `previous_response_id`.
- `driod/workspace.py`: bounded file access, conflict detection and backups.
- `driod/tools.py`: approved commands, process management and website tools.
- `driod/browser_worker.py`: isolated Playwright checks.
- `driod/desktop.py`: Windows app/window/VS Code integration.
- `driod/voice.py`: Vosk wake-word listening and system TTS.
- `driod/extras.py`: research, screen controls, markets and productivity.
- `examples/store`: the included local shopping demo.
- `tests`: repeatable core and browser checks.

## Integration references

Verified against the vendors' documentation during development:

- [OpenRouter tool calling](https://openrouter.ai/docs/guides/features/tool-calling)
- [OpenRouter model catalog API](https://openrouter.ai/docs/api/api-reference/models/list-all-models-and-their-properties)
- [VS Code command-line interface](https://code.visualstudio.com/docs/configure/command-line)
- [Playwright Python library](https://playwright.dev/python/docs/library)
- [Vosk](https://alphacephei.com/vosk/) and [official models](https://alphacephei.com/vosk/models)
- [PyAutoGUI](https://pyautogui.readthedocs.io/en/latest/)
- [yfinance](https://ranaroussi.github.io/yfinance/)
- [DDGS package and API](https://pypi.org/project/ddgs/)

Third-party packages and voice models retain their own licenses. The included source is yours to inspect and modify.
