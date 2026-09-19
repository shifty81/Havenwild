#!/usr/bin/env python3
"""Standalone mapper -> existing Havenwild PCC provider. No second PCC authority.

The GUI must spawn this as an external background job and consume the resulting
PCC receipts; do not invoke this synchronously on the GUI/render thread.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

PROVIDER = Path("tools/forge/HavenwildPccProvider.py")
TUPLES = Path("content/terrain/havenwild_terrain_tuple_catalog_v1.json")
SPATIAL = Path("crates/haven_spatial/src/lib.rs")
OLD_AUTHORITY = Path("content/worldgen/unified_terrain_world_lane_authority_v0_1.json")
READ_ONLY = frozenset({"pcc.status", "pcc.capabilities", "pcc.patch-ledger", "pcc.vault-status", "project.status"})


class BridgeError(Exception):
    pass


def project_root(path: str) -> Path:
    root = Path(path).resolve()
    for relative in ("Cargo.toml", PROVIDER, "tools/control/ProjectCommandRegistry.ps1"):
        if not (root / relative).is_file():
            raise BridgeError(f"Cannot establish Havenwild root: {root / relative} is absent")
    return root


def provider_json(root: Path, action: str) -> dict:
    command = [sys.executable, str(root / PROVIDER), action, "--root", str(root)]
    process = subprocess.run(command, cwd=root, capture_output=True, text=True, check=False)
    if process.returncode:
        raise BridgeError(f"PCC provider {action} failed ({process.returncode}): {process.stderr.strip()}")
    try:
        output = json.loads(process.stdout)
    except json.JSONDecodeError as exc:
        raise BridgeError(f"PCC provider {action} did not return JSON: {exc}") from exc
    if not isinstance(output, dict):
        raise BridgeError("PCC provider response must be a JSON object")
    return output


def keys(root: Path) -> set[str]:
    value = provider_json(root, "commands")
    commands = value.get("commands")
    if not isinstance(commands, list) or not all(isinstance(key, str) and key for key in commands):
        raise BridgeError("PCC command registry is unavailable or malformed")
    return set(commands)


def plan(root: Path, key: str) -> dict:
    registered = keys(root)
    if key not in registered:
        raise BridgeError(f"Command is not in the live PCC registry: {key}")
    read_only = key in READ_ONLY
    return {
        "schema": "havenwild.mapper_pcc_command_plan.v1",
        "projectRoot": str(root),
        "authority": str(PROVIDER),
        "commandKey": key,
        "readOnly": read_only,
        "requiresExactConfirmation": True,
        "requiresMutationApproval": not read_only,
        "execution": "existing_pcc_provider_only",
        "status": "planned_not_executed",
    }


def tuple_report(root: Path) -> dict:
    path = root / TUPLES
    if not path.is_file():
        raise BridgeError(f"Existing tuple catalog is absent: {path}")
    catalog = json.loads(path.read_text(encoding="utf-8-sig"))
    signatures = catalog.get("signatureToTileId")
    duplicates = catalog.get("duplicates")
    if not isinstance(signatures, dict) or not isinstance(duplicates, dict):
        raise BridgeError("Existing terrain tuple catalog has no valid signature/duplicate map")
    malformed = [key for key in signatures if len(key.split(",")) != 4 or not all(part.isdigit() for part in key.split(","))]
    count = len(signatures)
    if malformed or count != catalog.get("uniqueSignatureCount") or len(duplicates) != catalog.get("duplicateSignatureCount"):
        raise BridgeError("Existing tuple catalog is internally inconsistent; run the PCC terrain tuple audit")
    spatial = (root / SPATIAL).read_text(encoding="utf-8-sig") if (root / SPATIAL).is_file() else ""
    old_policy = (root / OLD_AUTHORITY).read_text(encoding="utf-8-sig") if (root / OLD_AUTHORITY).is_file() else ""
    return {
        "schema": "havenwild.mapper_dual_grid_inventory.v1",
        "sourceCatalog": str(TUPLES),
        "catalogDeclaredTiles": catalog.get("declaredTileCount"),
        "mappedTupleEntries": catalog.get("mappedTupleCount"),
        "uniqueSignatures": count,
        "duplicateSignatures": len(duplicates),
        "terrainFamilies": len(catalog.get("terrainOrdinalToCode", {})),
        "namedDualTileAnchorPresent": "TerrainTuplePresentationOrigin" in spatial,
        "retiredLevelOneRestrictionInOlderDocument": "Level 1 is reserved" in old_policy,
        "elizawySourceExactVisualCertified": False,
        "sharedRuntimeEditorParityCertified": False,
        "status": "legacy_catalog_diagnostic_only_not_elizawy_publication",
        "note": "This inventories existing authority; it does not invent a second dual-grid resolver or approve any artwork.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("capabilities", "commands", "status", "plan", "run", "dual-grid-report"))
    parser.add_argument("--root", required=True)
    parser.add_argument("--key", help="Exact PCC registered command key for plan/run")
    parser.add_argument("--confirm-key", help="Must exactly match --key to launch a PCC command")
    parser.add_argument("--allow-mutation", action="store_true", help="Explicit approval for non-read-only command")
    args = parser.parse_args(argv)
    try:
        root = project_root(args.root)
        if args.action in ("capabilities", "commands"):
            payload = provider_json(root, args.action)
        elif args.action == "status":
            process = subprocess.run([sys.executable, str(root / PROVIDER), "status", "--root", str(root)],
                                     cwd=root, capture_output=True, text=True, check=False)
            payload = {"schema": "havenwild.mapper_pcc_status.v1", "exitCode": process.returncode,
                       "providerOutput": process.stdout, "providerError": process.stderr,
                       "certification": "use_pcc_receipt_only"}
        elif args.action == "dual-grid-report":
            payload = tuple_report(root)
        else:
            if not args.key:
                raise BridgeError("--key is required")
            payload = plan(root, args.key)
            if args.action == "run":
                if args.confirm_key != args.key:
                    raise BridgeError("PCC execution blocked: --confirm-key must match --key exactly")
                if not payload["readOnly"] and not args.allow_mutation:
                    raise BridgeError("PCC execution blocked: command requires --allow-mutation")
                print(json.dumps({**payload, "status": "delegating_to_pcc"}), flush=True)
                # Synchronous in this CLI, NEVER on the mapper UI thread. The provider
                # calls the canonical PCC host, which owns intake, ledgers, jobs and gates.
                return subprocess.call([sys.executable, str(root / PROVIDER), "command", "--root",
                                        str(root), "--key", args.key], cwd=root)
        print(json.dumps(payload, indent=2))
        return 0 if payload.get("exitCode", 0) == 0 else int(payload["exitCode"])
    except (BridgeError, OSError, ValueError) as exc:
        print(json.dumps({"schema": "havenwild.mapper_pcc_bridge_error.v1", "error": str(exc)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
