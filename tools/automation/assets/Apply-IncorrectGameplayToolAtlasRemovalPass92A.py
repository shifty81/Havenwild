#!/usr/bin/env python3
"""Delete the rejected provisional gameplay-tool atlas after overlaying Pass 92A."""
from __future__ import annotations

from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
DELETE = [
    ROOT / "tools/automation/Build-LpcGameplayToolAtlas.py",
    ROOT / "tools/automation/Validate-LpcClientEditorStabilityV101.py",
    ROOT / "assets/generated/lpc/ui/havenwild_gameplay_tools_32.png",
    ROOT / "assets/generated/lpc/ui/havenwild_gameplay_tools_32.json",
]


def main() -> int:
    removed: list[str] = []
    for path in DELETE:
        if path.exists():
            path.unlink()
            removed.append(path.relative_to(ROOT).as_posix())

    ui_dir = ROOT / "assets/generated/lpc/ui"
    if ui_dir.exists() and not any(ui_dir.iterdir()):
        ui_dir.rmdir()

    print("Removed rejected gameplay tool art:")
    if removed:
        for item in removed:
            print(f"  - {item}")
    else:
        print("  - already absent")

    validator = ROOT / "tools/automation/validation/checks/editor/Validate-LpcClientEditorStabilityV102.py"
    if not validator.is_file():
        print("ERROR: Pass 92A files were not overlaid before running this cleanup.", file=sys.stderr)
        return 2
    return subprocess.run([sys.executable, str(validator)], cwd=ROOT).returncode


if __name__ == "__main__":
    raise SystemExit(main())
