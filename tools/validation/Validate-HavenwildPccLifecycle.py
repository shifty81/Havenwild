#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

REQUIRED = [
    "tools/control/HavenwildPccHost.ps1",
    "tools/control/PccRestartTicket.ps1",
    "tools/control/PccPatchLedger.ps1",
    "tools/control/PccPatchPreflight.ps1",
    "tools/control/PccQuickState.py",
    "tools/control/PccRootHandoffClassifier.ps1",
    "tools/control/PccCommandHost.ps1",
    "content/architecture/havenwild_pcc_lifecycle_contract_v3.json",
]

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ns = ap.parse_args()
    root = Path(ns.root).resolve()
    errors: list[str] = []
    for rel in REQUIRED:
        if not (root / rel).is_file():
            errors.append(f"missing lifecycle authority: {rel}")
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1
    contract = json.loads((root / REQUIRED[-1]).read_text(encoding="utf-8-sig"))
    host = (root / "tools/control/HavenwildPccHost.ps1").read_text(encoding="utf-8-sig")
    ticket = (root / "tools/control/PccRestartTicket.ps1").read_text(encoding="utf-8-sig")
    classifier = (root / "tools/control/PccRootHandoffClassifier.ps1").read_text(encoding="utf-8-sig")
    command_host = (root / "tools/control/PccCommandHost.ps1").read_text(encoding="utf-8-sig")
    if contract.get("schema") != "havenwild.pcc_lifecycle_contract.v3":
        errors.append("unexpected lifecycle contract schema")
    restart = contract.get("restart", {})
    if restart.get("maxAutomaticRestartsPerUpdate") != 1:
        errors.append("automatic restart budget must equal one")
    for token in ["Start-PccReplacement", "Consume-PccRestartTicket", "ResumeCommand"]:
        if token not in host and token not in ticket:
            errors.append(f"restart lifecycle token missing: {token}")
    for token in ["Get-PccPatchArchiveEvidence", "Get-PccBlockingPatchFailures"]:
        if token not in host:
            errors.append(f"patch lifecycle token missing from host: {token}")
    # Root intake may archive/move transports. The host must cache target metadata
    # before mutation and must not reopen the stale transport path afterward.
    if "$patchRecords" not in host or "foreach($record in $patchRecords)" not in host:
        errors.append("patch metadata snapshot authority missing from PCC host")
    post_apply = host.split("$rc=$LASTEXITCODE", 1)[1] if "$rc=$LASTEXITCODE" in host else ""
    if "Get-PccPatchTarget -Patch $p" in post_apply:
        errors.append("PCC host reopens stale patch FileInfo after mutating root intake")
    for token in ["Move-PccRootHandoffArtifacts", "artifacts\\packages\\received", "artifacts\\packages\\quarantine"]:
        if token not in classifier and token not in host:
            errors.append(f"root handoff lifecycle token missing: {token}")
    # Legacy commands must be bridged as live host output. Returning the child
    # success stream from Invoke-PccLegacyCommand causes callers that assign the
    # numeric result to buffer the entire Full Gate until completion.
    if "2>&1 |" not in command_host or "ForEach-Object { Write-Host $_ }" not in command_host:
        errors.append("PCC legacy command bridge does not stream child output live")
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1
    print("PASS Havenwild PCC lifecycle contract")
    print("- startup stays lightweight")
    print("- self-update restart is single-consumer and bounded to one")
    print("- patch archive evidence is authoritative")
    print("- post-intake ledger bookkeeping never reopens consumed transport paths")
    print("- required failed updates block certification")
    print("- non-installable source rollups are classified out of the live root before audit")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
