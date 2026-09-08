#!/usr/bin/env python3
"""Stable local/CI/root-control wrapper for current Havenwild validation."""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RUNNER = ROOT / "tools/automation/validation/validation_runner.py"


def _run(command: list[str]) -> int:
    print("RUN " + " ".join(command), flush=True)
    return subprocess.run(command, cwd=ROOT).returncode


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Havenwild validation through the v4 authority")
    parser.add_argument("profile", nargs="?", default="source")
    parser.add_argument("--continue-on-error", action="store_true")
    parser.add_argument("--list", action="store_true")
    parser.add_argument(
        "--cargo-test",
        action="store_true",
        help="Run cargo test --workspace before the selected current validation profile.",
    )
    args = parser.parse_args()

    if args.cargo_test:
        if shutil.which("cargo") is None:
            print("HWV-TOOLCHAIN-001 cargo is required for --cargo-test", file=sys.stderr)
            return 2
        code = _run(["cargo", "test", "--workspace"])
        if code:
            return code

    command = [sys.executable, str(RUNNER), args.profile]
    if args.continue_on_error:
        command.append("--continue-on-error")
    if args.list:
        command.append("--list")
    return _run(command)


if __name__ == "__main__":
    raise SystemExit(main())
