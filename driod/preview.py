from __future__ import annotations
import functools
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import threading
from urllib.parse import unquote, urlsplit


class Preview:
    def __init__(self, workspace, folder):
        root = workspace.path(folder)
        if not root.is_dir():
            raise ValueError("Preview folder does not exist.")
        class Handler(SimpleHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def list_directory(self, path):
                self.send_error(403, "Directory listing disabled; create index.html.")
                return None

            def send_head(self):
                p = Path(self.translate_path(self.path)).resolve()
                try:
                    workspace.path(workspace.rel(p))
                    if not p.is_relative_to(root):
                        raise ValueError("Outside preview")
                    raw_parts = unquote(urlsplit(self.path).path).replace("\\", "/").split("/")
                    if any(x.startswith(".") for x in raw_parts if x):
                        raise ValueError("Private path")
                except ValueError:
                    self.send_error(403)
                    return None
                return super().send_head()

            def end_headers(self):
                self.send_header("Cache-Control", "no-store")
                self.send_header("X-Content-Type-Options", "nosniff")
                super().end_headers()

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Handler, directory=str(root)))
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.url = f"http://127.0.0.1:{self.server.server_port}/"

    def close(self):
        self.server.shutdown()
        self.server.server_close()
