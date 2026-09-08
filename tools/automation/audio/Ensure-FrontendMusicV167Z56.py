#!/usr/bin/env python3
"""Restore the accepted Havenwild frontend harp loop as an attributed asset.

This is an asset bootstrap only. It never edits Rust source. Missing network
access is reported without failing the build so offline development remains
supported; the runtime safely runs without music when the file is absent.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import sys
import tempfile
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[3]
TARGET = ROOT / "content/audio/music/frontend/Harp.ogg"
EXPECTED_SHA256 = "8b3ea6ecdc3af69847c20684dca5a5ad4921bb4b41cc2563811f1f7ac50af489"
URLS = (
    "https://opengameart.org/sites/default/files/Harp.ogg",
    "https://raw.githubusercontent.com/LunarRust/KingOfMercury/"
    "fbdf9f4708ff0778c8eb5c94b310c031e0dfc354/Sounds/Harp.ogg",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def valid(path: Path) -> bool:
    return path.is_file() and sha256(path) == EXPECTED_SHA256


def download(url: str, destination: Path) -> None:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "Havenwild-Asset-Bootstrap/167Z56"},
    )
    with urllib.request.urlopen(request, timeout=45) as response:
        data = response.read()
    if not data.startswith(b"OggS"):
        raise ValueError("download did not contain an Ogg stream")
    destination.write_bytes(data)


def main() -> int:
    if valid(TARGET):
        print(f"Frontend music ready: {TARGET.relative_to(ROOT)}")
        return 0

    if TARGET.exists():
        print(
            "WARNING: existing frontend music does not match the accepted "
            f"Harp.ogg checksum; leaving it untouched: {TARGET.relative_to(ROOT)}"
        )
        return 0

    if os.environ.get("HAVENWILD_OFFLINE", "0") == "1":
        print("Frontend music unavailable in offline mode; runtime will continue silently")
        return 0

    TARGET.parent.mkdir(parents=True, exist_ok=True)
    failures: list[str] = []
    for url in URLS:
        temporary: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                prefix="havenwild-harp-", suffix=".ogg", delete=False
            ) as stream:
                temporary = Path(stream.name)
            download(url, temporary)
            actual = sha256(temporary)
            if actual != EXPECTED_SHA256:
                raise ValueError(
                    f"checksum mismatch: expected {EXPECTED_SHA256}, received {actual}"
                )
            temporary.replace(TARGET)
            print(f"Restored frontend music: {TARGET.relative_to(ROOT)}")
            return 0
        except (OSError, ValueError, urllib.error.URLError) as error:
            failures.append(f"{url}: {error}")
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)

    print("WARNING: frontend music could not be restored; runtime will continue silently")
    for failure in failures:
        print(f"  - {failure}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
