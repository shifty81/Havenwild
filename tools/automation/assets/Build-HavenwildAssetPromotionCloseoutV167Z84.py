#!/usr/bin/env python3
"""Build the Pass167Z84 cross-provider asset promotion closeout matrix.

This does not copy raw repositories into Havenwild. It verifies committed indexes,
reports whether the pinned authoring mounts are available, summarizes every
ElizaWy/Universal-LPC domain, and gates curated OpenGameArt LPC candidates.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
AUTHORITY = ROOT / "content/assets/intake/havenwild_asset_promotion_closeout_v0_1.json"
ELIZAWY_LOCK = ROOT / "content/assets/intake/lpc_source_lock_v0_1.json"
ELIZAWY_SUMMARY = ROOT / "WORKSPACE/generated/lpc/elizawy_repository_audit_v167z38_summary.json"
ELIZAWY_CATALOG_ROOT = ROOT / "WORKSPACE/generated/lpc/catalogs"
ULPC_LOCK = ROOT / "content/assets/intake/universal_lpc_generator_source_lock_v0_1.json"
ULPC_SUMMARY = ROOT / "content/assets/lpc/universal_lpc_complete_repository_summary_v0_1.json"
OGA_GAMEPLAY = ROOT / "content/assets/oga_lpc/manifests/oga_lpc_gameplay_intake_v0_2.json"
OGA_COMMERCIAL = ROOT / "content/assets/oga_lpc/manifests/oga_lpc_commercial_intake_v0_1.json"
OGA_QUEUE = ROOT / "content/assets/oga_lpc/manifests/oga_lpc_audit_queue_v0_1.json"
OBJECT_ATLAS = ROOT / "assets/generated/havenwild_lpc_objects_160x192_v2.json"
GENERATED_CHARACTER_ROOT = ROOT / "assets/generated/lpc/characters"
OUTPUT = ROOT / "WORKSPACE/generated/lpc/promotion/havenwild_asset_promotion_matrix_v167z84.json"
REPORT = ROOT / "docs/audits/generated/HAVENWILD_ASSET_PROMOTION_CLOSEOUT_V167Z84.md"


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def source_mount_state(lock: dict[str, Any]) -> dict[str, Any]:
    mount_value = lock.get("mountProjectPath") or lock.get("fullSourceProjectPath") or lock.get("projectMount")
    if not mount_value:
        raise RuntimeError("source lock has no project mount path")
    mount = ROOT / mount_value
    required = lock.get("requiredTopLevelPaths", lock.get("requiredDomainRoots", []))
    missing = [entry for entry in required if not (mount / entry).exists()]
    return {
        "path": mount_value,
        "present": mount.is_dir(),
        "isSymlink": mount.is_symlink(),
        "missingRequiredPaths": missing,
        "ready": mount.is_dir() and not missing,
    }


def elizawy_domains() -> tuple[list[dict[str, Any]], Counter[str]]:
    domains: list[dict[str, Any]] = []
    total_readiness: Counter[str] = Counter()
    for catalog_path in sorted(ELIZAWY_CATALOG_ROOT.glob("*.json")):
        catalog = load(catalog_path)
        records = catalog.get("records", [])
        readiness = Counter(record.get("readiness", "unknown") for record in records)
        roles = Counter(
            role
            for record in records
            for role in record.get("semanticRoles", [])
        )
        total_readiness.update(readiness)
        domains.append(
            {
                "domain": catalog.get("domain", catalog_path.stem),
                "recordCount": len(records),
                "readinessCounts": dict(sorted(readiness.items())),
                "semanticRoleCounts": dict(sorted(roles.items())),
                "catalog": rel(catalog_path),
                "promotionState": (
                    "catalogued"
                    if readiness.get("catalogued_requires_semantic_promotion", 0)
                    else "source_verified"
                ),
            }
        )
    return domains, total_readiness


def generated_character_counts() -> dict[str, Any]:
    pngs = list(GENERATED_CHARACTER_ROOT.rglob("*.png")) if GENERATED_CHARACTER_ROOT.is_dir() else []
    layer_pngs = [path for path in pngs if "layers" in path.parts]
    role_counts: Counter[str] = Counter()
    for path in layer_pngs:
        name = path.name
        role = "other"
        for candidate in (
            "body", "headwear", "hair", "eyebrows", "facial_hair", "eyes",
            "torso", "legs", "feet", "weapon", "shield", "tool",
        ):
            if f"_{candidate}_" in name:
                role = candidate
                break
        role_counts[role] += 1
    return {
        "generatedPngFiles": len(pngs),
        "generatedLayerPngFiles": len(layer_pngs),
        "generatedRoleCounts": dict(sorted(role_counts.items())),
        "root": rel(GENERATED_CHARACTER_ROOT),
        "note": "Generated files are runtime/editor caches, not proof that every raw repository option is certified.",
    }


def object_atlas_state() -> dict[str, Any]:
    if not OBJECT_ATLAS.is_file():
        return {"present": False, "path": rel(OBJECT_ATLAS), "recordCount": 0}
    data = load(OBJECT_ATLAS)
    records = data.get("objects", data.get("entries", []))
    water_cooler = [
        record for record in records
        if "water cooler" in str(record.get("source", "")).lower()
        or "water cooler" in str(record.get("sourcePath", "")).lower()
    ]
    return {
        "present": True,
        "path": rel(OBJECT_ATLAS),
        "recordCount": len(records),
        "quarantinedWaterCoolerRecords": len(water_cooler),
        "waterCoolerRuntimeBindingAllowed": False,
    }


def oga_entries() -> dict[str, Any]:
    gameplay = load(OGA_GAMEPLAY)
    commercial = load(OGA_COMMERCIAL)
    queue = load(OGA_QUEUE)
    entries: list[dict[str, Any]] = []
    for entry in gameplay.get("entries", []):
        files = [ROOT / value for value in entry.get("local_files", [])]
        source_files = [ROOT / value for value in entry.get("files", [])]
        all_files = files + source_files
        entries.append(
            {
                "id": entry.get("id"),
                "title": entry.get("title"),
                "license": entry.get("selected_license"),
                "state": entry.get("state"),
                "roles": entry.get("roles", []),
                "declaredLocalFileCount": len(all_files),
                "availableLocalFileCount": sum(path.is_file() for path in all_files),
                "sourcePage": entry.get("source_page"),
            }
        )
    for entry in commercial.get("assets", []):
        declared = [ROOT / value for value in entry.get("files", [])]
        entries.append(
            {
                "id": entry.get("id"),
                "title": entry.get("title"),
                "license": entry.get("selected_license"),
                "state": entry.get("state"),
                "roles": entry.get("production_roles", []),
                "declaredLocalFileCount": len(declared),
                "availableLocalFileCount": sum(path.is_file() for path in declared),
                "sourcePage": entry.get("source_url"),
            }
        )
    queue_counts = Counter(item.get("state", "unknown") for item in queue.get("queue", []))
    state_counts = Counter(entry.get("state", "unknown") for entry in entries)
    return {
        "curatedEntries": entries,
        "curatedStateCounts": dict(sorted(state_counts.items())),
        "broaderAuditQueueStateCounts": dict(sorted(queue_counts.items())),
        "policy": gameplay.get("policy", {}),
    }


def build(strict: bool) -> dict[str, Any]:
    authority = load(AUTHORITY)
    elizawy_lock = load(ELIZAWY_LOCK)
    ulpc_lock = load(ULPC_LOCK)
    elizawy_summary = load(ELIZAWY_SUMMARY)
    ulpc_summary = load(ULPC_SUMMARY)
    elizawy_mount = source_mount_state(elizawy_lock)
    ulpc_mount = source_mount_state(ulpc_lock)
    domains, readiness = elizawy_domains()

    expected_elizawy_files = authority["providers"][0]["rawFilesExpected"]
    expected_ulpc_pngs = authority["providers"][1]["spritesheetPngFilesExpected"]
    if elizawy_summary.get("fileCount") != expected_elizawy_files:
        raise RuntimeError("committed ElizaWy audit summary does not match the Z84 authority")
    if ulpc_summary.get("counts", {}).get("spritesheetPngFiles") != expected_ulpc_pngs:
        raise RuntimeError("committed Universal LPC summary does not match the Z84 authority")
    if strict and not elizawy_mount["ready"]:
        raise RuntimeError("strict asset closeout requires the pinned ElizaWy source mount")
    if strict and not ulpc_mount["ready"]:
        raise RuntimeError("strict asset closeout requires the pinned Universal LPC source mount")

    blockers = []
    if not elizawy_mount["ready"]:
        blockers.append("ElizaWy raw source mount is unavailable; committed full catalogs remain usable for planning only.")
    if not ulpc_mount["ready"]:
        blockers.append("Universal LPC raw source mount is unavailable; complete committed index remains usable for planning only.")
    if readiness.get("catalogued_requires_semantic_promotion", 0):
        blockers.append("ElizaWy records remain catalogued rather than blanket runtime-promoted; semantic promotion must proceed by role.")

    return {
        "schema": "havenwild.asset_promotion_matrix.v167z84",
        "pass": "Pass167Z84",
        "strictCertified": strict and elizawy_mount["ready"] and ulpc_mount["ready"],
        "authority": rel(AUTHORITY),
        "providers": {
            "elizawy": {
                "commit": elizawy_summary.get("sourceCommit"),
                "fileCount": elizawy_summary.get("fileCount"),
                "imageCount": elizawy_summary.get("kindCounts", {}).get("image"),
                "sourceRevisionVerifiedInCommittedAudit": elizawy_summary.get("sourceRevisionVerified"),
                "mount": elizawy_mount,
                "readinessCounts": elizawy_summary.get("readinessCounts", {}),
                "domains": domains,
                "completeIndex": rel(ROOT / authority["providers"][0]["completeIndex"]),
            },
            "universalLpc": {
                "commit": ulpc_summary.get("sourceCommit"),
                "counts": ulpc_summary.get("counts", {}),
                "semanticRoleCounts": ulpc_summary.get("semanticRoleCounts", {}),
                "animationCounts": ulpc_summary.get("animationCounts", {}),
                "bodyFamilyCounts": ulpc_summary.get("bodyFamilyCounts", {}),
                "toolGroups": ulpc_summary.get("toolGroups", {}),
                "mount": ulpc_mount,
                "generatedRuntimeCaches": generated_character_counts(),
                "completeIndex": rel(ROOT / authority["providers"][1]["completeIndex"]),
            },
            "openGameArtLpc": oga_entries(),
        },
        "runtimeEvidence": {
            "objectAtlas": object_atlas_state(),
            "terrainAtlasPolicy": "Existing V7 and promoted ElizaWy terrain catalogs remain separate style lanes; source pixels may not cross-fallback.",
        },
        "priorityLanes": authority.get("priorityLanes", []),
        "knownQuarantine": authority.get("knownQuarantine", []),
        "blockers": blockers,
        "nextPromotionPasses": [
            "Z85 structural terrain and cliff/cave promotion",
            "Z86 Willowmere, harbor, building, interior, and furniture promotion",
            "Z87 nature, farming, creatures, world objects, and effects promotion",
            "Z88 complete character creator compatibility promotion",
            "Z89 equipment and gameplay animation certification",
        ],
    }


def write_report(matrix: dict[str, Any]) -> None:
    elizawy = matrix["providers"]["elizawy"]
    ulpc = matrix["providers"]["universalLpc"]
    oga = matrix["providers"]["openGameArtLpc"]
    lines = [
        "# Havenwild Asset Promotion Closeout — Pass167Z84",
        "",
        f"- Strict certified: `{matrix['strictCertified']}`",
        f"- ElizaWy: `{elizawy['fileCount']:,}` files; mount ready: `{elizawy['mount']['ready']}`",
        f"- Universal LPC: `{ulpc['counts']['spritesheetPngFiles']:,}` spritesheet PNGs; mount ready: `{ulpc['mount']['ready']}`",
        f"- Generated character cache PNGs: `{ulpc['generatedRuntimeCaches']['generatedPngFiles']:,}`",
        f"- Curated OpenGameArt LPC entries: `{len(oga['curatedEntries'])}`",
        "",
        "## ElizaWy domain routing",
        "",
        "| Domain | Records | State |",
        "|---|---:|---|",
    ]
    for domain in elizawy["domains"]:
        lines.append(f"| {domain['domain']} | {domain['recordCount']:,} | {domain['promotionState']} |")
    lines.extend(["", "## Promotion order", ""])
    for lane in matrix["priorityLanes"]:
        lines.append(f"{lane['order']}. **{lane['id']}** — {lane['reason']}")
    lines.extend(["", "## Current blockers", ""])
    if matrix["blockers"]:
        lines.extend(f"- {blocker}" for blocker in matrix["blockers"])
    else:
        lines.append("- None. Both pinned source mounts are present and the matrix can proceed to per-role promotion.")
    lines.extend([
        "",
        "## Non-negotiable quarantine",
        "",
        "`Objects/Furniture/Water Cooler.png` is not a well and may not bind to `ObjectKind::Well`.",
        "",
        "Raw repositories remain immutable authoring dependencies. Runtime builds contain only promoted assets/generated caches with complete provenance, compatibility, and credits.",
        "",
    ])
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--strict", action="store_true", help="require both pinned source mounts")
    args = parser.parse_args()
    matrix = build(args.strict)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(matrix, indent=2) + "\n", encoding="utf-8")
    write_report(matrix)
    print(json.dumps({
        "output": rel(OUTPUT),
        "report": rel(REPORT),
        "strictCertified": matrix["strictCertified"],
        "blockers": matrix["blockers"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
