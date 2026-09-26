from __future__ import annotations

import difflib
import hashlib
import json
import os
from pathlib import Path, PureWindowsPath
import shutil
import tempfile
import uuid
from datetime import datetime, timezone


class Workspace:
    """File tools are confined to one user-selected directory, with undo copies."""
    MAX_TEXT = 250_000
    SKIP = {"node_modules", "__pycache__", ".venv", "venv"}

    def __init__(self, root: Path, state: Path):
        self.root = root.expanduser().resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.state = state.expanduser().resolve()
        self.state.mkdir(parents=True, exist_ok=True)
        if self.state == self.root or self.state.is_relative_to(self.root):
            raise ValueError("Choose a project folder outside Driod's private settings folder.")
        self.seen: dict[str, str] = {}

    def path(self, name: str = ".") -> Path:
        if not isinstance(name, str) or not name or "\x00" in name:
            raise ValueError("Use a relative project path.")
        windows = PureWindowsPath(name)
        if Path(name).is_absolute() or windows.is_absolute() or windows.drive:
            raise ValueError("Use a relative path inside the project folder.")
        parts = name.replace("\\", "/").split("/")
        for part in parts:
            if part in ("", "."):
                continue
            if part == ".." or part.startswith(".") or ":" in part:
                raise ValueError("Parent paths, hidden files, and alternate streams are blocked.")
            if part.rstrip(" .") != part or PureWindowsPath(part).is_reserved():
                raise ValueError("This filename is not valid on Windows.")
            if part.lower() in {"credentials.json", "secrets.json", "id_rsa", "id_ed25519"}:
                raise ValueError("Secret files are not available to the agent.")
        result = self.root.joinpath(*parts).resolve()
        if not result.is_relative_to(self.root):
            raise ValueError("The path resolves outside the project folder.")
        # Protect hidden targets behind symlinks too.
        for part in result.relative_to(self.root).parts:
            if part.startswith(".") or part.lower() in {"credentials.json", "secrets.json", "id_rsa", "id_ed25519"}:
                raise ValueError("Hidden or secret file targets are blocked.")
        return result

    def rel(self, path: Path) -> str:
        return path.relative_to(self.root).as_posix()

    @staticmethod
    def digest(data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    def list_files(self, path="."):
        base = self.path(path)
        if not base.is_dir():
            raise ValueError("That directory does not exist.")
        entries = []
        for folder, dirs, files in os.walk(base, followlinks=False):
            dirs[:] = sorted(d for d in dirs if not d.startswith(".") and d not in self.SKIP
                             and not Path(folder, d).is_symlink())
            for name in sorted(dirs + files):
                p = Path(folder, name)
                try:
                    p = self.path(self.rel(p))
                except ValueError:
                    continue
                entries.append({"path": self.rel(p), "type": "folder" if p.is_dir() else "file"})
                if len(entries) >= 600:
                    return {"entries": entries, "truncated": True}
        return {"entries": entries, "truncated": False}

    def read_file(self, path):
        p = self.path(path)
        if p.stat().st_size > self.MAX_TEXT:
            raise ValueError("File is too large for this text tool (250 KB limit).")
        data = p.read_bytes()
        content = data.decode("utf-8-sig")
        if "\x00" in content:
            raise ValueError("This is a binary file. Import it as an asset instead.")
        self.seen[self.rel(p)] = self.digest(data)
        return {"path": self.rel(p), "content": content, "sha256": self.digest(data)}

    def _snapshot(self, p):
        backup_id = uuid.uuid4().hex
        folder = self.state / "backups" / backup_id
        folder.mkdir(parents=True)
        shutil.copy2(p, folder / "content")
        (folder / "meta.json").write_text(json.dumps({
            "id": backup_id, "workspace": str(self.root), "path": self.rel(p),
            "time": datetime.now(timezone.utc).isoformat()
        }), encoding="utf-8")
        return backup_id

    def write_file(self, path, content):
        if not isinstance(content, str) or len(content.encode("utf-8")) > self.MAX_TEXT:
            raise ValueError("Write UTF-8 text up to 250 KB per file.")
        p = self.path(path)
        previous = ""
        backup = None
        if p.exists():
            current = p.read_bytes()
            if self.seen.get(self.rel(p)) != self.digest(current):
                raise ValueError("Read this file first. It is new to this session or changed externally.")
            previous = current.decode("utf-8-sig")
            if previous == content:
                return {"path": self.rel(p), "changed": False}
            backup = self._snapshot(p)
        p.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=p.parent, prefix=".driod-")
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
                f.write(content)
            os.replace(tmp, p)
        finally:
            Path(tmp).unlink(missing_ok=True)
        self.seen[self.rel(p)] = self.digest(p.read_bytes())
        diff = "\n".join(difflib.unified_diff(previous.splitlines(), content.splitlines(),
                                              fromfile=path + " (before)", tofile=path, lineterm=""))
        return {"path": self.rel(p), "changed": True, "backup_id": backup,
                "bytes": p.stat().st_size, "diff": diff[:6000]}

    def replace_text(self, path, old, new):
        if not old:
            raise ValueError("The old text cannot be empty.")
        text = self.read_file(path)["content"]
        if text.count(old) != 1:
            raise ValueError("Provide old text that appears exactly once.")
        return self.write_file(path, text.replace(old, new, 1))

    def make_directory(self, path):
        p = self.path(path)
        p.mkdir(parents=True, exist_ok=True)
        return {"path": self.rel(p)}

    def rename_file(self, source, destination):
        src, dst = self.path(source), self.path(destination)
        if not src.is_file() or dst.exists():
            raise ValueError("Source must be a file and destination must not exist.")
        backup = self._snapshot(src)
        dst.parent.mkdir(parents=True, exist_ok=True)
        src.rename(dst)
        self.seen.pop(self.rel(src), None)
        self.seen[self.rel(dst)] = self.digest(dst.read_bytes())
        return {"path": self.rel(dst), "backup_id": backup}

    def list_backups(self, path):
        target = self.rel(self.path(path))
        records = []
        for p in (self.state / "backups").glob("*/meta.json"):
            try:
                meta = json.loads(p.read_text(encoding="utf-8"))
                if meta["workspace"] == str(self.root) and meta["path"] == target:
                    records.append(meta)
            except (OSError, ValueError, KeyError):
                continue
        return {"backups": sorted(records, key=lambda x: x["time"], reverse=True)[:30]}

    def restore_file(self, backup_id):
        if len(backup_id) != 32 or any(c not in "0123456789abcdef" for c in backup_id):
            raise ValueError("Invalid backup ID.")
        folder = self.state / "backups" / backup_id
        meta = json.loads((folder / "meta.json").read_text(encoding="utf-8"))
        if meta["workspace"] != str(self.root):
            raise ValueError("Backup belongs to a different workspace.")
        p = self.path(meta["path"])
        if p.exists():
            self.read_file(meta["path"])
        return self.write_file(meta["path"], (folder / "content").read_text(encoding="utf-8-sig"))

    def import_file(self, source: Path):
        """Only called by the local file chooser, never by the model."""
        if not source.is_file() or source.stat().st_size > 25 * 1024 * 1024:
            raise ValueError("Choose a file smaller than 25 MB.")
        destination = self.path("imports/" + source.name)
        if destination.exists():
            destination = destination.with_name(destination.stem + "-" + uuid.uuid4().hex[:6] + destination.suffix)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        return self.rel(destination)
