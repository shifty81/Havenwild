#!/usr/bin/env python3
"""Compatibility wrapper for the unified current validation registry.

Legacy suite names map to the current source profile. Historical pass-specific
checks are retained under validation/checks but are not implicit build gates.
"""
from __future__ import annotations
import argparse, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]

def main()->int:
    parser=argparse.ArgumentParser(description="Run current Havenwild validation")
    parser.add_argument("suite",nargs="?",default="source")
    parser.add_argument("--list",action="store_true")
    args=parser.parse_args()
    profile={"all":"source","assets":"source","terrain-v7":"source","water":"source","character":"source","worldgen":"source","saves":"source","editor-runtime":"source","architecture":"source","licenses":"source"}.get(args.suite,args.suite)
    command=[sys.executable,str(ROOT/"tools/automation/validation/validation_runner.py"),profile]
    if args.list: command.append("--list")
    return subprocess.run(command,cwd=ROOT).returncode
if __name__=="__main__": raise SystemExit(main())
