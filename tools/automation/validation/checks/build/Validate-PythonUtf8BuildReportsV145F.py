#!/usr/bin/env python3
"""Validate explicit UTF-8 handling for Windows build/report generation."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
def require(path: str, needles: list[str]) -> list[str]:
    text = (ROOT / path).read_text(encoding="utf-8")
    return [f"{path}: missing {needle}" for needle in needles if needle not in text]

def main() -> int:
    errors: list[str] = []
    errors += require("tools/build/Build.sh", ["export PYTHONUTF8=1", "export PYTHONIOENCODING=utf-8"])
    errors += require("tools/build/Build.ps1", ['$env:PYTHONUTF8 = "1"', '$env:PYTHONIOENCODING = "utf-8"'])
    for script in (
        "tools/automation/terrain/Build-LpcProductionTuplePromotionV136.py",
        "tools/automation/terrain/Build-LpcPathGroundPromotionV137.py",
    ):
        errors += require(script, ["encoding='utf-8'"])
    if errors:
        print("Pass 145F UTF-8 validation failed:")
        for error in errors:
            print(f"  - {error}")
        return 1
    print("Pass 145F UTF-8 build/report validation passed")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
