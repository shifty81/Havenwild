#!/usr/bin/env python3
"""Compatibility wrapper. Suite aliases are resolved by the v4 alias authority."""
from __future__ import annotations
import argparse, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
def main()->int:
    parser=argparse.ArgumentParser(description="Run Havenwild validation")
    parser.add_argument("suite",nargs="?",default="source")
    parser.add_argument("--list",action="store_true")
    args=parser.parse_args()
    command=[sys.executable,str(ROOT/"tools/automation/validation/validation_runner.py"),args.suite]
    if args.list: command.append("--list")
    return subprocess.run(command,cwd=ROOT).returncode
if __name__=="__main__": raise SystemExit(main())
