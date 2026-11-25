"""Offline delivery of the build-time rendered editorial image."""
from pathlib import Path
import os


def main():
    source = Path(__file__).resolve().parent / "entry.png"
    output = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))
    payload = source.read_bytes()
    if len(payload) > 1048576 or not payload.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError("The committed raster must be a PNG at most 1 MiB")
    output.mkdir(parents=True, exist_ok=True)
    temporary = output / ".entry.tmp"
    temporary.write_bytes(payload)
    temporary.replace(output / "entry.png")


if __name__ == "__main__":
    main()
