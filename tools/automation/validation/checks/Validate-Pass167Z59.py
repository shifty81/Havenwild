#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
SCRIPT = ROOT / "tools" / "control" / "PackageProject.ps1"


def require(text: str, marker: str) -> None:
    if marker not in text:
        raise SystemExit(f"missing required packaging marker: {marker}")


def main() -> int:
    text = SCRIPT.read_text(encoding="utf-8")
    if ".TrimStart('\\\\','/')" in text or '.TrimStart("\\\\","/")' in text:
        raise SystemExit("invalid two-character TrimStart separator remains")
    require(text, '.TrimStart([char[]]"\\/")')
    require(text, "assets/source/licensed")
    require(text, "FileAttributes]::ReparsePoint")
    require(text, "sourcePolicy = 'havenwild_owned_source_only'")
    require(text, '"$out.sha256"')
    require(text, "Resolve-EffectivePass")
    print("Pass 167Z59 checkpoint packaging contract validated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
