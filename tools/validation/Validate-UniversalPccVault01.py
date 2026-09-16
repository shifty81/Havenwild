#!/usr/bin/env python3
from __future__ import annotations
import argparse
import json
import subprocess
import sys
from pathlib import Path

REQUIRED = [
    "content/architecture/universal_pcc_vault_contract_v1.json",
    "content/architecture/pcc_vault_dependencies_v1.json",
    "tools/control/PccVaultAdapter.py",
    "tools/control/PccCommandExtensions.ps1",
    "tools/control/PccCommandHost.ps1",
    "content/assets/intake/lpc_terrain_v7_source_lock_v0_1.json",
    "tools/automation/dependencies/Ensure-LpcTerrainV7Dependency.py",
]


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ns = ap.parse_args()
    root = Path(ns.root).resolve()
    errors: list[str] = []
    for rel in REQUIRED:
        if not (root / rel).is_file():
            errors.append(f"missing Universal PCC Vault file: {rel}")
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1

    contract = read_json(root / "content/architecture/universal_pcc_vault_contract_v1.json")
    project_manifest = read_json(root / "content/architecture/pcc_vault_dependencies_v1.json")
    lock = read_json(root / "content/assets/intake/lpc_terrain_v7_source_lock_v0_1.json")
    caps = read_json(root / "content/architecture/havenwild_pcc_capabilities_v2.json")
    runtime = read_json(root / "content/architecture/havenwild_pcc_runtime_contract_v2.json")

    if contract.get("schema") != "pcc.universal_vault_contract.v1":
        errors.append("unexpected universal Vault contract schema")
    if contract.get("defaultVaultRootWindows") != r"D:\Vault":
        errors.append("universal Vault contract must default to D:\\Vault on Windows")
    principles = contract.get("principles") or {}
    for key in (
        "networkIsLastResort",
        "hashVerificationRequiredBeforePromotion",
        "knownLicenseRequiredForAutomaticPromotion",
        "ambiguousOrUnlicensedContentGoesToReviewOrQuarantine",
        "promotionIsTransactional",
    ):
        if principles.get(key) is not True:
            errors.append(f"universal Vault principle must be true: {key}")
    order = contract.get("resolutionOrder") or []
    if not order or order[-2:] != ["network_acquisition", "fail_with_recovery_evidence"]:
        errors.append("network acquisition must be the final resolution attempt before failure")

    if project_manifest.get("schema") != "pcc.vault_project_dependencies.v1":
        errors.append("unexpected Havenwild Vault dependency manifest schema")
    locks = [str(item.get("lock") or "") for item in project_manifest.get("dependencies") or []]
    if "content/assets/intake/lpc_terrain_v7_source_lock_v0_1.json" not in locks:
        errors.append("Havenwild Vault manifest does not register LPC Terrains V7")

    vault = lock.get("vault") or {}
    if vault.get("rootRelativePath") != "Assets/LPC/Terrains/lpc-terrains-v7":
        errors.append("LPC Terrains V7 does not have the canonical Vault path")
    if vault.get("autoPromote") is not True:
        errors.append("LPC Terrains V7 must auto-promote only after lock verification")
    if not lock.get("licenseLabels"):
        errors.append("LPC Terrains V7 lock must preserve known license labels")
    required = (lock.get("verification") or {}).get("requiredFiles") or []
    if len(required) != 7 or any(not x.get("sha256") for x in required):
        errors.append("LPC Terrains V7 lock must retain all seven exact file hashes")

    ext = (root / "tools/control/PccCommandExtensions.ps1").read_text(encoding="utf-8-sig")
    host = (root / "tools/control/PccCommandHost.ps1").read_text(encoding="utf-8-sig")
    terrain = (root / "tools/automation/dependencies/Ensure-LpcTerrainV7Dependency.py").read_text(encoding="utf-8-sig")
    for token in ("pcc.vault-status", "pcc.vault-sync"):
        if token not in ext:
            errors.append(f"PCC extensions missing stable Vault command: {token}")
        if token not in host:
            errors.append(f"PCC command host missing Vault builtin: {token}")
    for token in ("pcc_ensure_project_source", "pcc_promote_source", "LAST RESORT"):
        if token not in terrain:
            errors.append(f"LPC Terrain V7 resolver missing Vault-first contract token: {token}")

    stable = caps.get("stableCommands") or {}
    if stable.get("vaultStatus") != "pcc.vault-status" or stable.get("vaultSync") != "pcc.vault-sync":
        errors.append("PCC capabilities do not publish stable Vault commands")
    runtime_vault = runtime.get("vault") or {}
    if runtime_vault.get("networkIsLastResort") is not True:
        errors.append("PCC runtime contract does not make network a last resort")

    self_test = subprocess.run(
        [sys.executable, str(root / "tools/control/PccVaultAdapter.py"), "self-test", "--pretty"],
        cwd=root,
        capture_output=True,
        text=True,
    )
    if self_test.returncode != 0:
        errors.append("PccVaultAdapter self-test failed: " + (self_test.stderr.strip() or self_test.stdout.strip()))

    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1
    print("PASS UNIVERSAL-PCC-VAULT-01")
    print("- project-local verified source is reusable and promotable")
    print("- D:\\Vault is the default Windows machine-wide authority")
    print("- exact hashes + known license gate automatic promotion")
    print("- Vault source/cache/archive precede network acquisition")
    print("- ambiguous or invalid Vault content is review/quarantine material")
    print("- promotion/hydration transaction self-test passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
