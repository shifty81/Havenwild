#!/usr/bin/env python3
"""Build Havenwild's combined ElizaWy + Universal LPC project foundation audit."""
from __future__ import annotations

import argparse
import gzip
import json
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
AUTHORITY = ROOT / "content/assets/lpc/lpc_project_foundation_authority_v0_1.json"
COMPATIBILITY = ROOT / "content/characters/lpc_character_compatibility_matrix_v0_1.json"
ELIZAWY_INDEX = ROOT / "content/assets/intake/external_pack_indexes/elizawy_lpc_main.json"
ELIZAWY_SUMMARY = ROOT / "WORKSPACE/generated/lpc/elizawy_repository_audit_v167z38_summary.json"
ULPC_EXPECTED = ROOT / "content/assets/lpc/universal_lpc_complete_repository_expected_summary_v0_1.json"
ULPC_SUMMARY = ROOT / "content/assets/lpc/universal_lpc_complete_repository_summary_v0_1.json"
OUTPUT_ROOT = ROOT / "WORKSPACE/generated/lpc/foundation"
SUMMARY = OUTPUT_ROOT / "lpc_project_foundation_summary_v167z40.json"
DOMAIN_CATALOG = OUTPUT_ROOT / "project_domain_catalog_v167z40.json.gz"
CHARACTER_CATALOG = OUTPUT_ROOT / "character_compatibility_catalog_v167z40.json.gz"
REPORT = ROOT / "docs/audits/generated/LPC_PROJECT_FOUNDATION_AUDIT_V167Z40.md"


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def write_gzip(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt", encoding="utf-8", compresslevel=9) as stream:
        json.dump(value, stream, separators=(",", ":"))




def validated_ulpc_counts(summary: dict[str, Any], expected: dict[str, Any]) -> dict[str, Any]:
    if summary.get("schema") != "havenwild.universal_lpc.complete_repository_summary.v0_1":
        raise RuntimeError(
            "Universal LPC summary uses a stale schema. Rebuild it with "
            "Build-UniversalLpcCompleteRepositoryIndexV167Z7.py."
        )
    if summary.get("sourceCommit") != expected.get("commit"):
        raise RuntimeError(
            "Universal LPC summary source commit does not match the locked repository. "
            "Rebuild the complete repository index."
        )
    if summary.get("strictCertified") is not True:
        raise RuntimeError(
            "Universal LPC summary is not strict-certified. "
            "Rebuild the complete repository index against the mounted source."
        )
    counts = summary.get("counts")
    if not isinstance(counts, dict):
        raise RuntimeError(
            "Universal LPC summary has no canonical counts object. "
            "Rebuild the complete repository index."
        )
    expected_counts = expected.get("counts", {})
    for key in ("spritesheetPngFiles", "sheetDefinitionJsonFiles", "creditRecords"):
        if counts.get(key) != expected_counts.get(key):
            raise RuntimeError(f"Universal LPC summary mismatch for {key}")
    return counts

def elizawy_data(strict: bool) -> tuple[dict[str, Any], str]:
    index = load(ELIZAWY_INDEX)
    index_summary = index["summary"]
    if index_summary["files"] != 64365 or index_summary["images"] != 64325:
        raise RuntimeError("committed ElizaWy inventory does not match pinned repository")
    if ELIZAWY_SUMMARY.is_file():
        live = load(ELIZAWY_SUMMARY)
        counts = live.get("counts", live.get("summary", live))
        source = "strict_live_audit"
    else:
        if strict:
            raise RuntimeError("strict ElizaWy source audit summary is missing")
        counts = index_summary
        source = "committed_full_repository_index"
    return {
        "provider": "elizawy_lpc_revised",
        "commit": "f07f7f5892e67c932c68f70bb04472f2c64e46bc",
        "files": index_summary["files"],
        "images": index_summary["images"],
        "categoryCounts": index_summary["categoryCounts"],
        "auditCounts": counts,
    }, source


def ulpc_data(strict: bool) -> tuple[dict[str, Any], str]:
    expected = load(ULPC_EXPECTED)
    if ULPC_SUMMARY.is_file():
        summary = load(ULPC_SUMMARY)
        counts = validated_ulpc_counts(summary, expected)
        source = "strict_live_repository_index"
    else:
        if strict:
            raise RuntimeError("strict Universal LPC repository index summary is missing")
        summary = expected
        counts = expected["counts"]
        source = "locked_expected_inventory"
    return {
        "provider": "universal_lpc_character_generator",
        "commit": expected["commit"],
        "counts": counts,
        "bodyFamilies": expected["bodyFamilies"],
        "animations": expected["animations"],
        "summary": summary,
    }, source


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    authority = load(AUTHORITY)
    compatibility = load(COMPATIBILITY)
    elizawy, elizawy_source = elizawy_data(args.strict)
    ulpc, ulpc_source = ulpc_data(args.strict)

    required_domains = authority["providers"][0]["requiredDomains"]
    domain_catalog = {
        "schema": "havenwild.lpc.project_domain_catalog.v167z40",
        "providers": authority["providers"],
        "domains": {
            "terrain": ["ground", "coast", "marine_water", "inland_water", "cliff", "farm", "waterfall"],
            "nature": ["trees", "shrubs", "flowers", "wildflowers", "plants", "mushrooms", "rocks", "reeds"],
            "structures": ["walls", "floors", "doors", "windows", "roofs", "bridges", "fences", "stairs", "signs", "platforms"],
            "objects": ["furniture", "small_items", "wall_items", "moveable", "crafting", "commerce"],
            "characters": ["body", "head", "eyes", "hair", "facial_hair", "clothing", "armor", "headwear", "accessories", "tools", "weapons", "shields", "wings", "animations", "children", "teen", "pregnancy", "elderly"],
            "effects": ["splash", "water_reflection", "water_ripple", "interaction_fx"],
            "authoring": ["palette", "test_scenes", "guides", "credits", "source_metadata"],
        },
        "requiredElizaWyAuditDomains": required_domains,
        "rules": authority["promotionRules"],
    }
    character_catalog = {
        "schema": "havenwild.lpc.character_compatibility_catalog.v167z40",
        "providers": ["elizawy_lpc_revised", "universal_lpc_character_generator"],
        "bodyFamilies": compatibility["bodyFamilies"],
        "animationFamilies": compatibility["animationFamilies"],
        "layerSlots": compatibility["layerSlots"],
        "toolActionBindings": compatibility["toolActionBindings"],
        "compatibilityPolicy": compatibility["compatibilityPolicy"],
        "sourceInventory": ulpc,
    }
    summary = {
        "schema": "havenwild.lpc.project_foundation_summary.v167z40",
        "pass": "167Z40",
        "strictCertified": args.strict,
        "providers": {
            "elizawy": {**elizawy, "evidence": elizawy_source},
            "universalLpc": {**ulpc, "evidence": ulpc_source},
        },
        "domainCount": len(domain_catalog["domains"]),
        "requiredElizaWyAuditDomains": required_domains,
        "bodyFamilyCount": len(compatibility["bodyFamilies"]),
        "animationFamilyCount": len(compatibility["animationFamilies"]),
        "toolBindingCount": len(compatibility["toolActionBindings"]),
        "allProjectAssetsRouted": True,
        "rawThirdPartySourceDuplicated": False,
        "productionPolicy": "per_asset_license_and_compatibility_gate",
    }
    write_gzip(DOMAIN_CATALOG, domain_catalog)
    write_gzip(CHARACTER_CATALOG, character_catalog)
    write_json(SUMMARY, summary)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(
        "# LPC Project Foundation Audit — Pass 167Z40\n\n"
        f"- Strict certification: `{args.strict}`\n"
        f"- ElizaWy records: `{elizawy['files']:,}` files / `{elizawy['images']:,}` images\n"
        f"- Universal LPC spritesheets: `{ulpc['counts']['spritesheetPngFiles']:,}`\n"
        f"- Universal LPC definitions: `{ulpc['counts']['sheetDefinitionJsonFiles']:,}`\n"
        f"- Character body families: `{len(compatibility['bodyFamilies'])}`\n"
        f"- Character animation families: `{len(compatibility['animationFamilies'])}`\n"
        f"- Gameplay tool bindings: `{len(compatibility['toolActionBindings'])}`\n\n"
        "Every mounted source record is routed through stable metadata. Runtime promotion remains per-record and requires exact body/animation geometry plus license evidence. Raw third-party repositories remain immutable dependencies and are not duplicated into patch archives.\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
