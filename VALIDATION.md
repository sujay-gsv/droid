# Driod 1.0 validation

Build date: 26 September 2026. Execution environment: Linux, Python 3.12.

| Check | Result |
|---|---|
| Python source compilation | Passed |
| Demo JavaScript syntax (`node --check`) | Passed |
| Core automated tests | 26 passed |
| Browser test class | Skipped: Chromium could not be downloaded in this environment |
| Office formats | DOCX paragraph, XLSX cell and PPTX slide count reopened and verified |
| File writes and undo | Verified create/read/edit, unique replacements, rename, backup and restoration |
| File boundaries | Verified traversal, absolute Windows/POSIX paths, hidden files, reserved names and symlink escape rejection |
| Approval behavior | Declined commands/restores left target files unchanged |
| Process handling | Finite command output, cancellation, timeout, background output and termination verified on Linux |
| Static preview | HTTP content served; hidden-file requests blocked |
| AI/tool integration | Simulated multi-round provider response, matching tool-call IDs, malformed arguments, output truncation handling and request payload verified |
| OpenRouter live generation | Not run: no key supplied |
| Windows UI/app integration | Not run: no Windows session or graphical display |
| Voice and desktop peripherals | Parser tested; microphone, TTS, OCR, mouse, brightness and volume not exercised on hardware |
| Market calculations | Synthetic rising, falling and flat price series verified; no live quote claims |
| Live search/Yahoo | Not run in this environment |
| Reminders and local records | Persistence, completion, due reminders, portfolio fields and timezone conversion verified |

The source includes real browser smoke tests for cart/search/demo checkout and for detecting then repairing a JavaScript error. Run `test.bat` after installing Chromium to execute them. Skipped tests do not count as passed browser validation. Dependency versions use bounded ranges rather than a lock file; rerun diagnostics/tests if installed dependency behavior changes.
