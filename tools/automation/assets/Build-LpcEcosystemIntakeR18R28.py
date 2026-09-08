#!/usr/bin/env python3
"""Build the W81R18-R28 LPC/OpenGameArt ecosystem intake snapshot.

This builder is deliberately source-rollup safe: it uses committed Havenwild
catalog/index metadata and does not require the large raw LPC source mounts.
Raw mounts are authoring dependencies; their exact files remain immutable and
are promoted separately through the existing source/audit pipeline.
"""
from __future__ import annotations

import gzip
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]

AUTHORITY = ROOT / "content/assets/lpc/lpc_ecosystem_intake_authority_r18_r28_v1.json"
DISCOVERY = ROOT / "content/assets/lpc/lpc_ecosystem_discovery_seed_r18_v1.json"
CLOSEOUT = ROOT / "content/assets/intake/havenwild_asset_promotion_closeout_v0_1.json"
ULPC_SUMMARY = ROOT / "content/assets/lpc/universal_lpc_complete_repository_summary_v0_1.json"
ULPC_COMMERCIAL = ROOT / "content/assets/lpc/universal_lpc_commercial_catalog_v0_1.json.gz"
ULPC_SHAREALIKE = ROOT / "content/assets/lpc/universal_lpc_sharealike_catalog_v0_1.json.gz"
CHARACTER_PRODUCTION = ROOT / "content/assets/lpc/lpc_character_production_catalog_v0_1.json"
GAMEPLAY_ITEM_SEEDS = ROOT / "content/assets/lpc/universal_lpc_gameplay_item_seed_catalog_v0_1.json"
OGA_QUEUE = ROOT / "content/assets/oga_lpc/manifests/oga_lpc_audit_queue_v0_1.json"
BROWSER_AUTHORITY = ROOT / "content/editor/assets/universal_asset_browser_v2_r19_v1.json"

OUTPUT = ROOT / "content/assets/lpc/lpc_ecosystem_intake_snapshot_r18_r28_v1.json"
BROWSER_OUTPUT = ROOT / "content/editor/assets/lpc_ecosystem_browser_projection_r19_v1.json"
REPORT = ROOT / "docs/audits/generated/LPC_ECOSYSTEM_INTAKE_R18_R28.md"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_gzip_json(path: Path) -> dict[str, Any]:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        return json.load(handle)


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def sorted_counter(counter: Counter[str]) -> dict[str, int]:
    return dict(sorted(counter.items(), key=lambda item: (-item[1], item[0])))


def normalize_license(value: str | None) -> str:
    if not value:
        return "UNVERIFIED"
    return value.replace(" ", "-").upper()


def tier_for_license(value: str | None) -> str:
    value = normalize_license(value)
    if value.startswith("CC0") or value.startswith("OGA-BY"):
        return "green"
    if value.startswith("CC-BY-SA"):
        return "yellow"
    if value.startswith("CC-BY"):
        return "green_conditional"
    if "GPL" in value or "NC" in value or "ND" in value or value == "UNVERIFIED":
        return "red"
    return "review"


def main() -> int:
    authority = load_json(AUTHORITY)
    discovery = load_json(DISCOVERY)
    closeout = load_json(CLOSEOUT)
    ulpc = load_json(ULPC_SUMMARY)
    commercial = load_gzip_json(ULPC_COMMERCIAL)
    sharealike = load_gzip_json(ULPC_SHAREALIKE)
    character = load_json(CHARACTER_PRODUCTION)
    gameplay_seeds = load_json(GAMEPLAY_ITEM_SEEDS)
    oga_queue = load_json(OGA_QUEUE)
    browser_authority = load_json(BROWSER_AUTHORITY)

    commercial_records = commercial.get("records", [])
    sharealike_records = sharealike.get("records", [])

    commercial_license_counts = Counter(
        record.get("selectedLicense") or "UNVERIFIED" for record in commercial_records
    )
    commercial_category_counts = Counter(
        record.get("category") or "unknown" for record in commercial_records
    )
    sharealike_category_counts = Counter(
        record.get("category") or "unknown" for record in sharealike_records
    )

    pack_domain_counts = Counter()
    pack_tier_counts = Counter()
    pack_license_counts = Counter()
    gameplay_loop_counts = Counter()
    pack_rows: list[dict[str, Any]] = []
    for pack in discovery.get("packs", []):
        domain = pack.get("domain", "unknown")
        tier = pack.get("tier", "review")
        selected = pack.get("selectedLicense")
        if selected and tier == "review":
            tier = tier_for_license(selected)
        pack_domain_counts[domain] += 1
        pack_tier_counts[tier] += 1
        pack_license_counts[selected or "UNVERIFIED"] += 1
        for loop in pack.get("loops", []):
            gameplay_loop_counts[loop] += 1
        pack_rows.append(
            {
                "id": pack.get("id"),
                "title": pack.get("title"),
                "domain": domain,
                "selectedLicense": selected,
                "tier": tier,
                "sourceUrl": pack.get("url"),
                "gameplayLoops": pack.get("loops", []),
                "status": "discovered_requires_exact_file_provenance",
            }
        )

    oga_state_counts = Counter(item.get("state", "unknown") for item in oga_queue.get("queue", []))
    oga_license_counts = Counter(item.get("license", "UNVERIFIED") for item in oga_queue.get("queue", []))

    providers = {provider["id"]: provider for provider in closeout.get("providers", [])}
    elizawy = providers.get("elizawy_lpc_revised", {})
    ulpc_provider = providers.get("universal_lpc_character_generator", {})

    tool_seed_counts = {
        entry.get("id", "unknown"): len(entry.get("sourceAssetIds", []))
        for entry in gameplay_seeds.get("tools", [])
    }

    character_channels = character.get("channelCounts", {})
    character_component_count = int(character.get("componentCount", 0))

    # Project-wide source-to-exposure gap. The huge raw providers are represented by
    # their committed authority counts; individual raw files remain outside routine rollups.
    snapshot = {
        "schema": "havenwild.lpc_ecosystem.intake_snapshot.r18_r28.v1",
        "passRange": "W81R18-W81R28",
        "baseline": authority.get("baseline", "W81R17"),
        "generatedFromCommittedMetadata": True,
        "rawSourceMountsRequired": False,
        "authority": rel(AUTHORITY),
        "discoverySeed": rel(DISCOVERY),
        "headline": {
            "elizawyRawFilesExpected": elizawy.get("rawFilesExpected", 0),
            "elizawyImagesExpected": elizawy.get("imagesExpected", 0),
            "ulpcSpritesheetPngFiles": ulpc.get("counts", {}).get("spritesheetPngFiles", 0),
            "ulpcSheetDefinitions": ulpc.get("counts", {}).get("sheetDefinitionJsonFiles", 0),
            "ulpcCreditRecords": ulpc.get("counts", {}).get("creditRecords", 0),
            "ulpcEquipmentRecords": ulpc.get("equipmentRecords", 0),
            "ulpcCommercialPreferredOrAttributionRecords": len(commercial_records),
            "ulpcShareAlikeOnlyRecords": len(sharealike_records),
            "existingElizaCharacterProductionComponents": character_component_count,
            "ogaPreviouslyQueuedPacks": len(oga_queue.get("queue", [])),
            "r18DiscoverySeedPacks": len(pack_rows),
        },
        "universalLpc": {
            "semanticRoleCounts": ulpc.get("semanticRoleCounts", {}),
            "animationCounts": ulpc.get("animationCounts", {}),
            "bodyFamilyCounts": ulpc.get("bodyFamilyCounts", {}),
            "toolGroups": ulpc.get("toolGroups", {}),
            "commercialSelectedLicenseCounts": sorted_counter(commercial_license_counts),
            "commercialCategoryCounts": sorted_counter(commercial_category_counts),
            "shareAlikeCategoryCounts": sorted_counter(sharealike_category_counts),
            "gameplayToolSeedSourceCounts": tool_seed_counts,
            "policy": "Expose approved components through semantic Character/Wardrobe categories; preserve exact ULPC definition/zPos/action/body compatibility and per-component credits.",
        },
        "elizawyLpcRevised": {
            "repository": elizawy.get("repository"),
            "commit": elizawy.get("commit"),
            "rawFilesExpected": elizawy.get("rawFilesExpected", 0),
            "imagesExpected": elizawy.get("imagesExpected", 0),
            "productionCharacterCatalog": {
                "componentCount": character_component_count,
                "channelCounts": character_channels,
            },
            "policy": "Primary world/terrain/object/structure baseline remains exact-source and immutable; semantic promotion must not flatten raw PNGs into guessed roles.",
        },
        "openGameArt": {
            "discoveryFeedCount": len(discovery.get("discoveryFeeds", [])),
            "r18PackDomainCounts": sorted_counter(pack_domain_counts),
            "r18PackTierCounts": sorted_counter(pack_tier_counts),
            "r18SelectedLicenseCounts": sorted_counter(pack_license_counts),
            "r18GameplayLoopCoverage": sorted_counter(gameplay_loop_counts),
            "existingAuditQueueStateCounts": sorted_counter(oga_state_counts),
            "existingAuditQueueLicenseCounts": sorted_counter(oga_license_counts),
            "packs": pack_rows,
            "policy": "Collection membership is discovery only. Exact files require source URL, authors, offered licenses, selected license, checksum, derivative lineage, and attribution before promotion.",
        },
        "promotionStates": authority.get("states", []),
        "licenseTiers": authority.get("licenseTiers", {}),
        "passDomains": authority.get("domainPasses", {}),
        "releaseRule": "Fail closed on blocked/unverified provenance. Runtime packages only used/promoted/generated assets plus required attribution.",
        "nextRuntimeIntegrationBoundary": "The R18-R28 additive authority does not modify W81R17 Rust/UI; current W81R17 source is required before implementing live browser/runtime bindings without regression risk.",
    }

    # Browser projection is intentionally aggregated. The live browser can virtualize
    # individual source records from the existing catalogs when the W81 UI is wired.
    category_projection: dict[str, dict[str, Any]] = {}
    ulpc_to_browser = {
        "body": "Characters/Bases",
        "head": "Characters/Head & Face",
        "eyes": "Characters/Head & Face",
        "hair": "Characters/Hair",
        "character_layer": "Characters/Other Layers",
        "clothing": "Characters/Wardrobe",
        "armor": "Characters/Armor",
        "headwear": "Characters/Headwear",
        "accessory": "Characters/Accessories",
        "tool": "Items/Tools",
        "weapon": "Items/Weapons",
        "shield": "Items/Shields",
        "wings": "Characters/Special Anatomy",
    }
    for role, count in ulpc.get("semanticRoleCounts", {}).items():
        path = ulpc_to_browser.get(role, f"Characters/{role.replace('_', ' ').title()}")
        category_projection[path] = {
            "catalogCount": count,
            "source": "Universal LPC",
            "state": "catalogued",
        }

    for domain, count in pack_domain_counts.items():
        path = f"OpenGameArt Discovery/{domain.replace('_', ' ').title()}"
        category_projection[path] = {
            "catalogCount": count,
            "source": "OpenGameArt discovery packs",
            "state": "discovered_requires_exact_file_provenance",
        }

    browser_projection = {
        "schema": "havenwild.asset_browser.lpc_ecosystem_projection.r19.v1",
        "baseline": "W81R17",
        "browserAuthority": rel(BROWSER_AUTHORITY),
        "snapshot": rel(OUTPUT),
        "presentation": {
            "primaryNavigation": "semantic_category_tree_plus_virtualized_thumbnail_grid",
            "pagination": "not_primary",
            "search": True,
            "statusBadges": True,
            "licenseBadges": True,
            "sourceVisibleBeforeRuntimeBinding": True,
        },
        "categoryProjection": dict(sorted(category_projection.items())),
        "requiredBadges": [
            "Production Ready",
            "Needs Setup",
            "ShareAlike",
            "Reference Only",
            "Blocked",
        ],
        "requiredFilters": browser_authority.get("filters", []),
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    BROWSER_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    BROWSER_OUTPUT.write_text(json.dumps(browser_projection, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    h = snapshot["headline"]
    report_lines = [
        "# Havenwild LPC Ecosystem Intake Audit — W81R18–R28",
        "",
        "This report is generated from committed Havenwild catalog/index metadata. It intentionally does not require the large raw LPC source mounts.",
        "",
        "## Headline inventory",
        "",
        f"- ElizaWy/LPC Revised expected raw files: **{h['elizawyRawFilesExpected']:,}** ({h['elizawyImagesExpected']:,} images).",
        f"- Universal LPC spritesheet PNGs: **{h['ulpcSpritesheetPngFiles']:,}**.",
        f"- Universal LPC equipment records: **{h['ulpcEquipmentRecords']:,}**.",
        f"- Universal LPC credit records: **{h['ulpcCreditRecords']:,}**.",
        f"- ULPC preferred/attribution-commercial catalog records: **{h['ulpcCommercialPreferredOrAttributionRecords']:,}**.",
        f"- ULPC ShareAlike-only selected records: **{h['ulpcShareAlikeOnlyRecords']:,}**.",
        f"- Existing exact ElizaWy Character production components: **{h['existingElizaCharacterProductionComponents']:,}**.",
        f"- Prior curated OGA audit queue: **{h['ogaPreviouslyQueuedPacks']:,} packs**.",
        f"- R18 expanded LPC/OGA discovery seed: **{h['r18DiscoverySeedPacks']:,} packs**.",
        "",
        "## Universal LPC semantic roles",
        "",
    ]
    for key, value in sorted(ulpc.get("semanticRoleCounts", {}).items(), key=lambda x: (-x[1], x[0])):
        report_lines.append(f"- {key}: {value:,}")
    report_lines += ["", "## R18 OpenGameArt discovery by domain", ""]
    for key, value in sorted(pack_domain_counts.items(), key=lambda x: (-x[1], x[0])):
        report_lines.append(f"- {key}: {value}")
    report_lines += ["", "## License/readiness policy", ""]
    report_lines += [
        "- Green: CC0 and OGA-BY.",
        "- Green-conditional: CC-BY; attribution/distribution requirements remain tracked.",
        "- Yellow: CC-BY-SA; Havenwild code/editor remain separate, while derivative art retains ShareAlike obligations.",
        "- Red: GPL-only, NC, ND, unknown/unverified; blocked from release by default.",
        "- Multi-licensed sources select the safest compatible offered license per exact source record.",
        "",
        "## R18–R28 implementation boundary",
        "",
        "The contracts, census, browser projection, gameplay-domain intake definitions, release policy, and acceptance-world specification are additive and safe to carry onto the W81R17 line. They do **not** claim that the current W81 native UI/runtime has already been rewired to expose every record. That live integration must be performed against current W81R17 source bytes to avoid reverting newer Character/terrain code.",
        "",
    ]
    REPORT.write_text("\n".join(report_lines), encoding="utf-8")

    print(f"W81R18-R28 LPC ecosystem intake snapshot: {rel(OUTPUT)}")
    print(f"Universal Asset Browser projection: {rel(BROWSER_OUTPUT)}")
    print(f"Audit report: {rel(REPORT)}")
    print(f"ULPC PNGs: {h['ulpcSpritesheetPngFiles']:,}; equipment: {h['ulpcEquipmentRecords']:,}; OGA seed packs: {h['r18DiscoverySeedPacks']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
