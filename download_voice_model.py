"""Download the official small English Vosk model after the user runs voice setup."""
from pathlib import Path
import shutil
import tempfile
import urllib.request
import zipfile

URL = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
ROOT = Path(__file__).resolve().parent


def main():
    destination = ROOT / "voice-model"
    if (destination / "am" / "final.mdl").is_file():
        print("Voice model is already installed.")
        return
    if destination.exists():
        raise RuntimeError("An incomplete voice-model folder exists. Rename it and retry.")
    print("Downloading the small English Vosk model (approximately 40 MB)...")
    with tempfile.TemporaryDirectory(dir=ROOT) as temp:
        temp = Path(temp)
        archive = temp / "model.zip"
        with urllib.request.urlopen(URL, timeout=90) as response, archive.open("wb") as output:
            shutil.copyfileobj(response, output)
        extract = temp / "extracted"
        extract.mkdir()
        with zipfile.ZipFile(archive) as z:
            if sum(x.file_size for x in z.infolist()) > 500_000_000:
                raise ValueError("Unexpectedly large model archive.")
            for entry in z.infolist():
                p = (extract / entry.filename).resolve()
                if not p.is_relative_to(extract.resolve()):
                    raise ValueError("Unsafe model archive path.")
            z.extractall(extract)
        source = extract / "vosk-model-small-en-us-0.15"
        if not (source / "am" / "final.mdl").is_file():
            raise RuntimeError("The downloaded model is incomplete.")
        shutil.move(str(source), str(destination))
    print("Voice model installed. Audio recognition runs locally.")


if __name__ == "__main__":
    main()
