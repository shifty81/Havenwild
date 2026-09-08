#!/usr/bin/env python3
"""Compatibility entrypoint for the unified Havenwild validator."""
from __future__ import annotations
import subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
requested=sys.argv[1] if len(sys.argv)>1 else "source"
profile={"all":"source","certify":"full"}.get(requested,requested)
raise SystemExit(subprocess.run([sys.executable,str(ROOT/"tools/automation/validation/validation_runner.py"),profile],cwd=ROOT).returncode)
