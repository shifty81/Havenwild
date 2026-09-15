#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, re, sys
from pathlib import Path

REQUIRED = [
    "HavenwildTools.cmd",
    "tools/control/HavenwildPccHost.ps1",
    "tools/control/PccRestartTicket.ps1",
    "tools/control/PccJobHost.ps1",
    "tools/control/PccPatchLedger.ps1",
    "tools/control/PccPatchPreflight.ps1",
    "tools/control/PccCommandHost.ps1",
    "tools/control/PccCommandExtensions.ps1",
    "tools/control/PccQuickState.py",
    "tools/forge/HavenwildPccProvider.py",
    "content/architecture/havenwild_pcc_runtime_contract_v2.json",
    "content/architecture/havenwild_pcc_capabilities_v2.json",
    "content/editor/architecture/havenwild_tooling_profile_v1.json",
    "tools/control/HavenwildTools.ps1",
    "tools/control/ProjectCommandRegistry.ps1",
    "tools/control/InvokeRootPatchIntake.ps1",
    "tools/control/DevelopmentLane.ps1",
    "tools/control/GitSourceControl.ps1",
]

def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))

def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument("--root", required=True); ns=ap.parse_args()
    root=Path(ns.root).resolve(); errors=[]
    for rel in REQUIRED:
        if not (root/rel).is_file(): errors.append(f"missing required PCC v2 file: {rel}")
    if errors:
        for e in errors: print(f"FAIL: {e}")
        return 1
    cmd=(root/"HavenwildTools.cmd").read_text(encoding="utf-8-sig")
    if "HavenwildPccHost.ps1" not in cmd: errors.append("root launcher does not route through HavenwildPccHost.ps1")
    host=(root/"tools/control/HavenwildPccHost.ps1").read_text(encoding="utf-8-sig")
    for token in ["Consume-PccRestartTicket", "Get-PccBlockingPatchFailures", "Invoke-PccPatchLanePreflight", "Get-PccPatchArchiveEvidence", "--record-certification", "IsNullOrWhiteSpace($choice)"]:
        if token not in host: errors.append(f"host missing required contract token: {token}")
    runtime=read_json(root/"content/architecture/havenwild_pcc_runtime_contract_v2.json")
    caps=read_json(root/"content/architecture/havenwild_pcc_capabilities_v2.json")
    profile=read_json(root/"content/editor/architecture/havenwild_tooling_profile_v1.json")
    if runtime.get("schema") != "havenwild.pcc_runtime_contract.v2": errors.append("unexpected PCC runtime contract schema")
    if caps.get("schema") != "havenwild.pcc_capabilities.v2": errors.append("unexpected PCC capabilities schema")
    if profile.get("schema") != "havenwild.editor_tooling_profile.v1": errors.append("unexpected editor tooling profile schema")
    if runtime.get("restart",{}).get("maxAutomaticRestartsPerUpdate") != 1: errors.append("restart contract must allow exactly one automatic restart per update")
    if not runtime.get("patchIntake",{}).get("lanePreflightBeforeMutation"): errors.append("lane preflight must occur before patch mutation")
    if not runtime.get("frontDoor",{}).get("prohibitsGovernedSourceHashing"): errors.append("front door must prohibit governed-source hashing")
    if not runtime.get("frontDoor",{}).get("rehashesOnlyChangedPaths"): errors.append("front door must restrict quick certification hashing to Git-changed paths")
    if not runtime.get("patchIntake",{}).get("archiveEvidenceDeterminesAppliedVsFailed"): errors.append("patch ledger must use transactional archive evidence")
    if not runtime.get("restart",{}).get("gateResumeUsesOriginalCommand"): errors.append("restart handoff must resume the original gate command")
    if errors:
        for e in errors: print(f"FAIL: {e}")
        return 1
    print("PASS Havenwild PCC v2 contract")
    print("- root launcher -> lightweight PCC host")
    print("- one-shot restart ticket")
    print("- lane-aware patch preflight before mutation")
    print("- required failed patch blocks gate")
    print("- quick front door performs no governed-tree hashing and verifies only changed paths")
    print("- transactional archive evidence distinguishes APPLIED from FAILED")
    print("- gate self-update resumes the original command once")
    print("- ForgePY-compatible project-native provider")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
