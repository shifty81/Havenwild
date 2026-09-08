#!/usr/bin/env python3
"""Focused validation for Pass 167Z41 ULPC summary bootstrap repair."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "tools/automation/characters/Validate-UniversalLpcCompleteRepositorySummaryV167Z41.py"
EXPECTED_SOURCE = ROOT / "content/assets/lpc/universal_lpc_complete_repository_expected_summary_v0_1.json"
COMMIT = "0f898bb675a1abe16ce430e82e3bf9daed278690"


def require_text(relative: str, tokens: tuple[str, ...]) -> None:
    text = (ROOT / relative).read_text(encoding="utf-8")
    for token in tokens:
        if token not in text:
            raise AssertionError(f"{relative} is missing required token: {token}")


def run_validator(expected: Path, summary: Path, revision: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(VALIDATOR),
            "--expected",
            str(expected),
            "--summary",
            str(summary),
            "--revision",
            str(revision),
            "--skip-artifacts",
            "--quiet",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def main() -> int:
    require_text(
        "tools/build/Build.sh",
        (
            "Validate-UniversalLpcCompleteRepositorySummaryV167Z41.py",
            "universal_lpc_complete_repository_summary_v0_1.json",
            'summary_valid="1"',
            "validate complete Universal LPC repository summary",
        ),
    )
    require_text(
        "tools/build/Build.ps1",
        (
            "Validate-UniversalLpcCompleteRepositorySummaryV167Z41.py",
            "validate complete Universal LPC repository summary",
        ),
    )
    require_text(
        "tools/automation/assets/Build-LpcProjectFoundationV167Z40.py",
        (
            "validated_ulpc_counts",
            "stale schema",
            "canonical counts object",
            "strict-certified",
        ),
    )

    expected = json.loads(EXPECTED_SOURCE.read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory(prefix="havenwild-z41-") as directory:
        root = Path(directory)
        expected_path = root / "expected.json"
        summary_path = root / "summary.json"
        revision_path = root / "revision.txt"
        expected_path.write_text(json.dumps(expected), encoding="utf-8")
        revision_path.write_text(COMMIT + "\n", encoding="utf-8")

        malformed = {
            "schema": "havenwild.universal_lpc.legacy_summary.v0",
            "sourceCommit": COMMIT,
            "inventory": expected["counts"],
        }
        summary_path.write_text(json.dumps(malformed), encoding="utf-8")
        result = run_validator(expected_path, summary_path, revision_path)
        if result.returncode == 0:
            raise AssertionError("legacy summary unexpectedly passed the Z41 validator")

        canonical = {
            "schema": "havenwild.universal_lpc.complete_repository_summary.v0_1",
            "sourceCommit": COMMIT,
            "counts": {
                "spritesheetPngFiles": expected["counts"]["spritesheetPngFiles"],
                "sheetDefinitionJsonFiles": expected["counts"]["sheetDefinitionJsonFiles"],
                "paletteDefinitionJsonFiles": 0,
                "creditRecords": expected["counts"]["creditRecords"],
            },
            "strictCertified": True,
        }
        summary_path.write_text(json.dumps(canonical), encoding="utf-8")
        result = run_validator(expected_path, summary_path, revision_path)
        if result.returncode != 0:
            raise AssertionError(f"canonical summary failed Z41 validator: {result.stderr}")

    print("Pass 167Z41 Universal LPC summary bootstrap repair validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
