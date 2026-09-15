#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, subprocess, sys
from pathlib import Path

CAPABILITIES = {
    "schema": "havenwild.pcc_capabilities.v2",
    "provider": "forge.internal_pcc.v2",
    "project": "Havenwild",
    "authority": "project-native-pcc",
    "commands": {
        "status": "pcc.status",
        "fullGate": "validation.full-quality-gate",
        "fastGate": "validation.fast-quality-gate",
        "commitPushGreen": "source-control.commit-push-green",
        "laneToggle": "project.lane.toggle",
        "patchStatus": "pcc.patch-ledger",
        "capabilities": "pcc.capabilities",
        "validatePcc": "pcc.validate-v2",
    },
    "features": [
        "branch-aware-publication", "lane-aware-patch-preflight", "one-shot-restart-ticket",
        "structured-job-receipts", "quick-frontdoor-state", "failed-required-patch-gate-block",
        "registry-backed-menus", "project-local-independent-operation"
    ],
}

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("action", choices=["capabilities", "status", "command", "full-gate", "fast-gate", "lane-toggle", "patch-status"])
    ap.add_argument("--root", required=True)
    ap.add_argument("--key")
    ns = ap.parse_args()
    root = Path(ns.root).resolve()
    if ns.action == "capabilities":
        print(json.dumps(CAPABILITIES, indent=2)); return 0
    if ns.action == "status":
        return subprocess.call([sys.executable, str(root / "tools/control/PccQuickState.py"), "--root", str(root), "--pretty"])
    key = {
        "full-gate": "validation.full-quality-gate",
        "fast-gate": "validation.fast-quality-gate",
        "lane-toggle": "project.lane.toggle",
        "patch-status": "pcc.patch-ledger",
        "command": ns.key or "",
    }[ns.action]
    if not key:
        print("--key is required for action=command", file=sys.stderr); return 2
    cmd = ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(root / "tools/control/HavenwildPccHost.ps1"), "-Command", key]
    return subprocess.call(cmd, cwd=root)

if __name__ == "__main__":
    raise SystemExit(main())
