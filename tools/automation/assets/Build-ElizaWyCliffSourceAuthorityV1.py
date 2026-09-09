#!/usr/bin/env python3
"""Build Havenwild's ElizaWy cliff source-relationship audit.

This tool is intentionally non-runtime. It audits the immutable pinned ElizaWy
source, official upstream test scenes, current Havenwild cliff authorities, and
an optional Tiled/TSX metadata donor. It never edits third-party source art and
never promotes donor atlas pixels to Havenwild runtime authority.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

SCHEMA = "havenwild.worldgen.elizawy_cliff_source_relationship_authority.v1"
PASS_ID = "HW-CLIFF-SOURCE-01"
ELIZAWY_REPO = "https://github.com/ElizaWy/LPC"
ELIZAWY_COMMIT = "f07f7f5892e67c932c68f70bb04472f2c64e46bc"
OGA_DONOR_PAGE = (
    "https://opengameart.org/content/"
    "lpc-revised-fully-configured-4-seasons-tilesets-for-tiled-map-editor"
)
OGA_DONOR_ARCHIVE = "lpc-revised-exterior-tilesets.zip"

SOURCE_RELATIVE_CANDIDATES = (
    "Terrain/cliff_summer.png",
    "LPC-main/Terrain/cliff_summer.png",
)
TEST_SCENE_NAMES = (
    "DemoGame - 2 - Summer.png",
    "Test Landscape.png",
)
SEASONAL_CLIFF_NAMES = (
    "cliff_spring.png",
    "cliff_summer.png",
    "cliff_autumn.png",
    "cliff_winter.png",
)
CURRENT_AUTHORITY_FILES = (
    "content/worldgen/elizawy_cliff_complete_mapping_v0_1.json",
    "content/worldgen/elizawy_cliff_connected_recipe_authority_v0_1.json",
    "content/worldgen/elizawy_cliff_source_grammar_authority_v0_1.json",
    "content/worldgen/elizawy_cliff_sheet_role_catalog_v0_1.json",
    "content/worldgen/elizawy_cliff_topology_certification_v0_1.json",
    "content/worldgen/lpc_directional_cliff_ramp_authority_v0_1.json",
    "content/worldgen/structural_cliff_autotile_authority_v0_1.json",
)
CURRENT_SOURCE_FILES = (
    "crates/haven_assets/src/elizawy_cliff_provider.rs",
    "crates/haven_assets/src/lpc_cliff_ramp_provider.rs",
    "crates/haven_game/src/runtime_assets.rs",
    "crates/haven_game/src/runtime_structural_cliff_ramps.rs",
    "crates/haven_game/src/runtime_structural_cliff_draw.rs",
    "crates/haven_assets/src/asset_import_tiled.rs",
)

DONOR_QUARANTINE = (
    "assets/reference_quarantine/third_party/"
    "jaidynreiman_lpc_revised_tiled_2024"
)

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def png_dimensions(path: Path) -> list[int] | None:
    try:
        header = path.read_bytes()[:24]
        if (
            len(header) >= 24
            and header[:8] == b"\x89PNG\r\n\x1a\n"
            and header[12:16] == b"IHDR"
        ):
            return list(struct.unpack(">II", header[16:24]))
    except OSError:
        pass
    return None

def file_record(root: Path, path: Path) -> dict[str, Any]:
    try:
        rel = path.relative_to(root).as_posix()
    except ValueError:
        rel = path.as_posix()
    return {
        "path": rel,
        "exists": path.is_file(),
        "sha256": sha256(path) if path.is_file() else None,
        "bytes": path.stat().st_size if path.is_file() else None,
        "dimensions": png_dimensions(path) if path.is_file() and path.suffix.lower() == ".png" else None,
    }

def find_named(source_root: Path, name: str) -> Path | None:
    if not source_root.is_dir():
        return None
    exact = sorted(
        (p for p in source_root.rglob(name) if p.is_file()),
        key=lambda p: (len(p.parts), p.as_posix().casefold()),
    )
    return exact[0] if exact else None

def find_cliff_sheet(source_root: Path) -> Path | None:
    for candidate in SOURCE_RELATIVE_CANDIDATES:
        p = source_root / candidate
        if p.is_file():
            return p
    return find_named(source_root, "cliff_summer.png")

def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""

def count_marker(text: str, marker: str) -> int:
    return text.count(marker)

def inspect_tsx_bytes(name: str, data: bytes) -> dict[str, Any]:
    try:
        root = ET.fromstring(data)
    except ET.ParseError as exc:
        return {"path": name, "parseError": str(exc)}
    image = root.find("image")
    wangsets = root.findall("./wangsets/wangset")
    if not wangsets:
        wangsets = root.findall(".//wangset")
    tiles = root.findall("tile")
    collision_groups = 0
    animations = 0
    property_groups = 0
    classed_tiles = 0
    wang_tiles = 0
    for tile in tiles:
        if tile.find("objectgroup") is not None:
            collision_groups += 1
        if tile.find("animation") is not None:
            animations += 1
        if tile.find("properties") is not None:
            property_groups += 1
        if tile.get("class") or tile.get("type"):
            classed_tiles += 1
    for ws in wangsets:
        wang_tiles += len(ws.findall("wangtile"))
    return {
        "path": name,
        "name": root.get("name"),
        "tileWidth": int(root.get("tilewidth", "0") or 0),
        "tileHeight": int(root.get("tileheight", "0") or 0),
        "tileCount": int(root.get("tilecount", "0") or 0),
        "columns": int(root.get("columns", "0") or 0),
        "imageSource": image.get("source") if image is not None else None,
        "imageWidth": int(image.get("width", "0") or 0) if image is not None else None,
        "imageHeight": int(image.get("height", "0") or 0) if image is not None else None,
        "wangSetCount": len(wangsets),
        "wangTileAssignmentCount": wang_tiles,
        "animationTileCount": animations,
        "collisionTileCount": collision_groups,
        "propertyTileCount": property_groups,
        "classedTileCount": classed_tiles,
    }

def inspect_donor_archive(path: Path) -> dict[str, Any]:
    result: dict[str, Any] = {
        "expectedFilename": OGA_DONOR_ARCHIVE,
        "path": path.as_posix(),
        "present": path.is_file(),
        "sha256": None,
        "tsx": [],
        "tsxCount": 0,
        "status": "missing_optional_metadata_donor",
    }
    if not path.is_file():
        return result
    result["sha256"] = sha256(path)
    try:
        with zipfile.ZipFile(path) as zf:
            tsx_names = sorted(
                n for n in zf.namelist()
                if n.lower().endswith(".tsx") and not n.endswith("/")
            )
            result["tsx"] = [inspect_tsx_bytes(n, zf.read(n)) for n in tsx_names]
            result["tsxCount"] = len(tsx_names)
            result["status"] = (
                "metadata_available"
                if tsx_names
                else "archive_present_but_no_tsx"
            )
    except (OSError, zipfile.BadZipFile) as exc:
        result["status"] = "invalid_archive"
        result["error"] = str(exc)
    return result

def provider_findings(repo: Path) -> dict[str, Any]:
    provider = read_text(repo / "crates/haven_assets/src/elizawy_cliff_provider.rs")
    runtime_assets = read_text(repo / "crates/haven_game/src/runtime_assets.rs")
    ramp_provider = read_text(repo / "crates/haven_assets/src/lpc_cliff_ramp_provider.rs")
    draw = read_text(repo / "crates/haven_game/src/runtime_structural_cliff_draw.rs")
    ramps = read_text(repo / "crates/haven_game/src/runtime_structural_cliff_ramps.rs")
    tiled = read_text(repo / "crates/haven_assets/src/asset_import_tiled.rs")
    return {
        "elizawyProvider": {
            "sideEntryRampPendingPresent": "SideEntryRampPending" in provider,
            "complexTransitionStripPresent": "ComplexTransitionStrip" in provider,
            "rejectedPartialAssemblyPresent": "RejectedPartialAssembly" in provider,
            "explicitRejectedRampTestPresent":
                "rejected_complex_transition_strip_cannot_be_promoted_as_a_ramp" in provider,
        },
        "foreignRampProvider": {
            "providerFilePresent": bool(ramp_provider),
            "grassTopSourcePathPresent": "LPC_cliffs_grass.png" in ramp_provider,
            "threeByFourStampLanguagePresent":
                ("3x4" in ramp_provider or "width_cells" in ramp_provider),
        },
        "runtimeAssets": {
            "elizawyDerivedCliffSourceLoaded": "ELIZAWY_SUMMER_CLIFF_SOURCE_PATH" in runtime_assets,
            "foreignOgaCliffSourceFieldPresent": "oga_cliff_source" in runtime_assets,
            "foreignRampGrassSourceLoaded": "LPC_CLIFF_RAMP_GRASS_SOURCE_PATH" in runtime_assets,
        },
        "runtimeDraw": {
            "hwCliff02Present": "HW-CLIFF-02" in draw,
            "deferredForeignRampOverlayPresent": "deferred_ramp_overlays" in draw,
            "authoredDirectionalRampDrawPresent": "draw_authored_directional_ramp" in draw,
        },
        "runtimeRamp": {
            "lpcDirectionalRoleStillReferenced": "LpcDirectionalCliffRampRole" in ramps,
            "sixCellPatternStillEmbedded":
                ("[(1, -1), (1, 0), (0, 0), (0, 1), (-1, 1), (-1, 2)]" in ramps),
        },
        "tiledImporter": {
            "present": bool(tiled),
            "wangParsing": "parse_wang_assignments" in tiled,
            "collisionParsing": "collision_shapes" in tiled,
            "animationParsing": "AnimationClip" in tiled,
            "propertiesParsing": "parse_property_value" in tiled,
        },
    }

def build_authority(repo: Path, donor_archive: Path | None) -> dict[str, Any]:
    source_root = repo / "assets/source/licensed/lpc_revised"
    sheet = find_cliff_sheet(source_root)
    seasons = []
    for name in SEASONAL_CLIFF_NAMES:
        p = find_named(source_root, name)
        seasons.append(
            file_record(repo, p) if p
            else {"path": None, "name": name, "exists": False}
        )
    scenes = []
    for name in TEST_SCENE_NAMES:
        p = find_named(source_root, name)
        scenes.append(
            file_record(repo, p) if p
            else {"path": None, "name": name, "exists": False}
        )

    authorities = []
    for rel in CURRENT_AUTHORITY_FILES:
        p = repo / rel
        authorities.append(file_record(repo, p))

    source_files = []
    for rel in CURRENT_SOURCE_FILES:
        p = repo / rel
        source_files.append(file_record(repo, p))

    if donor_archive is None:
        donor_archive = repo / DONOR_QUARANTINE / OGA_DONOR_ARCHIVE
    donor = inspect_donor_archive(donor_archive)

    sheet_record = (
        file_record(repo, sheet)
        if sheet
        else {"path": None, "exists": False}
    )

    findings = provider_findings(repo)

    blockers = [
        {
            "id": "side_entry_ramp_not_certified",
            "severity": "blocker",
            "evidence": "ElizaWyCliffConnectedRecipeRole::SideEntryRampPending remains source-reference-only.",
            "requiredClosure": "Re-certify from original ElizaWy sheet plus demo/TSX relationship evidence; do not infer from screenshot.",
        },
        {
            "id": "complex_transition_strip_rejected",
            "severity": "blocker",
            "evidence": "The c8 transition strip is explicitly represented as rejected/source-reference evidence in the current provider/history.",
            "requiredClosure": "Audit the complete c8 assembly and its valid neighbors before any runtime promotion.",
        },
        {
            "id": "foreign_ramp_family_authority",
            "severity": "blocker",
            "evidence": "A companion LPC grass-top cliff provider and oga_cliff_source remain in the runtime asset graph.",
            "requiredClosure": "Remove as cliff/ramp visual authority only after source-native ElizaWy replacement is certified.",
        },
        {
            "id": "foreign_geometry_coupling",
            "severity": "blocker",
            "evidence": "Current directional ramp semantics still reference LpcDirectionalCliffRampRole and historical six-cell geometry designed around a 3x4 companion stamp.",
            "requiredClosure": "Derive connector footprint from certified ElizaWy assembly evidence, not the retired companion stamp.",
        },
        {
            "id": "derived_overlay_is_runtime_source",
            "severity": "review",
            "evidence": "Runtime lpc_cliff_source currently resolves ELIZAWY_SUMMER_CLIFF_SOURCE_PATH, a derived runtime overlay.",
            "requiredClosure": "Keep original pinned sheet as immutable art authority; derived overlays may only be recipe outputs with lineage.",
        },
    ]

    if not sheet:
        blockers.append({
            "id": "missing_local_cliff_source",
            "severity": "blocker",
            "evidence": "No cliff_summer.png was found below assets/source/licensed/lpc_revised.",
            "requiredClosure": "Restore the pinned ElizaWy source mount before runtime migration.",
        })
    if not all(item.get("exists") for item in scenes):
        blockers.append({
            "id": "missing_official_test_scene",
            "severity": "blocker",
            "evidence": "One or more official ElizaWy cliff test scenes are absent from the local pinned source mount.",
            "requiredClosure": "Restore DemoGame - 2 - Summer.png and Test Landscape.png.",
        })

    return {
        "schema": SCHEMA,
        "pass": PASS_ID,
        "generatedUtc": datetime.now(timezone.utc).isoformat(),
        "status": "audit_only_runtime_migration_blocked",
        "policy": {
            "runtimeRendererChangedByThisPass": False,
            "worldgenChangedByThisPass": False,
            "collisionChangedByThisPass": False,
            "originalArtAuthority": "ElizaWy/LPC pinned source",
            "metadataDonorIsArtAuthority": False,
            "derivedOverlayMayBeAuthority": False,
            "rule": (
                "Structural topology chooses a certified source-native ElizaWy "
                "assembly. No screenshot-driven synthesis, foreign cliff-family "
                "substitution, crop/stretch/mirror/rotation, or private ramp geometry."
            ),
        },
        "originalSource": {
            "repository": ELIZAWY_REPO,
            "pinnedCommit": ELIZAWY_COMMIT,
            "mount": source_root.relative_to(repo).as_posix(),
            "summerCliff": sheet_record,
            "seasonalCliffs": seasons,
            "officialTestScenes": scenes,
            "expectedCellSize": [32, 32],
            "expectedSummerGrid": [16, 14],
            "expectedSummerDimensions": [512, 448],
        },
        "configuredMetadataDonor": {
            "id": "jaidynreiman_lpc_revised_tiled_2024",
            "officialPage": OGA_DONOR_PAGE,
            "licenseEvidence": ["CC-BY 3.0", "OGA-BY 3.0"],
            "purpose": (
                "Relationship evidence only: Tiled terrain/Wang sets, tile "
                "properties, animation and collision metadata. Original ElizaWy "
                "pixels remain authoritative."
            ),
            "collisionPolicy": (
                "Donor collision is evidence only; Havenwild structural "
                "collision/traversal remains gameplay authority."
            ),
            "archive": donor,
        },
        "currentProviderFindings": findings,
        "currentAuthorityFiles": authorities,
        "currentSourceFiles": source_files,
        "provenKeep": [
            {
                "id": "straight_south",
                "source": "c2r7 -> c2r3 repeat -> c2r8",
                "evidence": "existing demo-grounded W14 authority",
            },
            {
                "id": "south_west",
                "source": "c1r7 -> c1r3 repeat -> c1r8",
                "evidence": "existing demo-grounded W14 authority",
            },
            {
                "id": "south_east",
                "source": "c3r7 -> c3r3 repeat -> c3r8",
                "evidence": "existing demo-grounded W14 authority",
            },
            {
                "id": "narrow_cave",
                "source": "c6r9-c6r11",
                "evidence": "existing source-native certified feature column",
            },
            {
                "id": "ladders",
                "source": "c11r9-c11r11 and c13r9-c13r11",
                "evidence": "existing source-native certified feature columns",
            },
        ],
        "blockedUntilEvidence": [
            "side-entry/ramp assembly",
            "c8 complete transition strip",
            "right-side terminal adjacency",
            "east-west ridge if supplied by companion cliff family",
            "any runtime visual recipe sourced from a different cliff family",
        ],
        "blockers": blockers,
        "migrationPlan": [
            "Acquire/locate the configured Tiled donor archive in governed quarantine; do not replace ElizaWy source art.",
            "Parse TSX/Wang/property/animation/collision metadata with Havenwild's existing Tiled semantics.",
            "Map donor atlas tiles back to original ElizaWy 32x32 cells/stamps using exact pixel hashes where possible.",
            "Cross-check ambiguous c8/side-entry/terminal relationships against ElizaWy official Summer demo and Test Landscape.",
            "Write a certified source-native assembly catalog with source rect, footprint, anchor, valid neighbors and evidence lineage.",
            "Only then migrate the runtime cliff resolver from hand-authored guesses to certified assembly selection.",
            "After migration proves parity, remove companion ramp visual authority and unused foreign runtime texture loading.",
        ],
    }

def markdown(authority: dict[str, Any]) -> str:
    src = authority["originalSource"]
    donor = authority["configuredMetadataDonor"]["archive"]
    blockers = authority["blockers"]
    lines = [
        "# HW-CLIFF-SOURCE-01 — ElizaWy Cliff Source Authority Audit",
        "",
        "This report is intentionally **non-runtime**. It does not change renderer, worldgen, collision, or editor behavior.",
        "",
        "## Source status",
        "",
        f"- Original art authority: `{authority['policy']['originalArtAuthority']}`",
        f"- Summer cliff source present: **{src['summerCliff'].get('exists', False)}**",
        f"- Tiled metadata donor status: **{donor.get('status')}**",
        f"- Runtime migration status: **{authority['status']}**",
        "",
        "## Why the current cliff lane is blocked",
        "",
    ]
    for item in blockers:
        lines.append(f"- **{item['id']}** ({item['severity']}): {item['evidence']}")
        lines.append(f"  - Closure: {item['requiredClosure']}")
    lines += [
        "",
        "## Keep",
        "",
    ]
    for item in authority["provenKeep"]:
        lines.append(f"- `{item['id']}` — {item['source']} — {item['evidence']}")
    lines += [
        "",
        "## Explicitly not done in this pass",
        "",
        "- No ramp renderer patch.",
        "- No six-cell replacement artwork.",
        "- No new cliff pixels.",
        "- No change to structural collision.",
        "- No promotion of the Tiled donor atlas as an art source.",
        "- No deletion of old providers until a source-native replacement is certified.",
        "",
        "## Migration sequence",
        "",
    ]
    for i, item in enumerate(authority["migrationPlan"], 1):
        lines.append(f"{i}. {item}")
    lines.append("")
    return "\n".join(lines)

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--donor-archive", type=Path)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-report", type=Path)
    parser.add_argument("--strict-source", action="store_true")
    args = parser.parse_args()

    repo = args.repo_root.resolve()
    authority = build_authority(repo, args.donor_archive)

    output_json = args.output_json or (
        repo / "artifacts/audits/elizawy_cliff_source_relationship_authority_v1.json"
    )
    output_report = args.output_report or (
        repo / "artifacts/audits/HW_CLIFF_SOURCE_01_ELIZAWY_SOURCE_AUTHORITY_RESET.md"
    )
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_report.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(authority, indent=2) + "\n", encoding="utf-8")
    output_report.write_text(markdown(authority), encoding="utf-8")

    print("HW-CLIFF-SOURCE-01")
    print(f"Authority : {output_json}")
    print(f"Report    : {output_report}")
    print(f"Status    : {authority['status']}")
    print(
        "ElizaWy source:",
        "FOUND" if authority["originalSource"]["summerCliff"].get("exists") else "MISSING",
    )
    print(
        "Tiled donor:",
        authority["configuredMetadataDonor"]["archive"].get("status"),
    )
    print("Blockers  :", len(authority["blockers"]))

    if args.strict_source:
        if not authority["originalSource"]["summerCliff"].get("exists"):
            return 2
        if not all(
            scene.get("exists")
            for scene in authority["originalSource"]["officialTestScenes"]
        ):
            return 3
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
