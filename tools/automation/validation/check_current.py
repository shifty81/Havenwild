#!/usr/bin/env python3
"""Stable local/CI wrapper for all current Havenwild validation profiles."""
from __future__ import annotations
import argparse, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]

def main()->int:
    parser=argparse.ArgumentParser(description="Run Havenwild validation through the v4 authority")
    parser.add_argument("profile",nargs="?",default="source")
    parser.add_argument("--continue-on-error",action="store_true")
    parser.add_argument("--list",action="store_true")
    args=parser.parse_args()
    command=[sys.executable,str(ROOT/"tools/automation/validation/validation_runner.py"),args.profile]
    if args.continue_on_error: command.append("--continue-on-error")
    if args.list: command.append("--list")
    return subprocess.run(command,cwd=ROOT).returncode
if __name__=="__main__": raise SystemExit(main())
