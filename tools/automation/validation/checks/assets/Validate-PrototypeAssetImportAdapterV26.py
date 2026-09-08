#!/usr/bin/env python3
"""Validate Havenwild no-raw-copy prototype asset import adapters.

Pass 20 validator: checks that newly audited usable packs are represented as
metadata-backed import adapters without copying raw third-party files into the
runtime repository by default.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
SOURCE_MANIFEST = ROOT / "content/assets/external_sources/external_asset_sources_v0_1.json"
IMPORT_QUEUE = ROOT / "content/assets/prototype_imports/prototype_asset_import_queue_v0_1.json"
ADAPTER_CATALOG = ROOT / "content/assets/prototype_imports/prototype_asset_import_adapters_v0_1.json"
ADAPTER_SCHEMA = ROOT / "content/schemas/prototype_asset_import_adapter.schema.v0_1.json"
DOC = ROOT / "docs/assets/PROTOTYPE_ASSET_IMPORT_ADAPTERS.md"

REQUIRED_BATCH2_SOURCES = {
    "third_party.pipoya.free_rpg_world_tileset_32_40_48",
    "third_party.henrysoftware.free_pixel_food_cc0",
    "third_party.ghostpixxells.pixel_mart_cc0",
    "third_party.fishing_free_noncommercial",
    "third_party.char_free_unverified",
    "third_party.game_endeavor.mystic_woods_free",
}

REQUIRED_ADAPTER_IDS = {
    "adapter.pipoya_world_tileset_32.v0_1",
    "adapter.free_pixel_food_icons_32.v0_1",
    "adapter.pixel_mart_icons_32.v0_1",
}

BLOCKED_BATCH2_SOURCES = {
    "third_party.fishing_free_noncommercial",
    "third_party.char_free_unverified",
    "third_party.game_endeavor.mystic_woods_free",
}

RAW_ARCHIVE_NAMES = {
    "Pipoya RPG World Tileset 48x48 40x40 32x32.zip",
    "Pipoya RPG World Tileset 48x48 40x40 32x32 for Tiled1.5.zip",
    "fishing_free.zip",
    "FreePixelFood.zip",
    "Pixel_Mart.zip",
    "char free.zip",
    "mystic_woods_free_2.2.zip",
}


def load_json(path: Path) -> dict:
    if not path.exists():
        raise AssertionError(f"Missing required file: {path.relative_to(ROOT)}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise AssertionError(f"Failed to parse {path.relative_to(ROOT)}: {exc}") from exc


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    sources_doc = load_json(SOURCE_MANIFEST)
    queue_doc = load_json(IMPORT_QUEUE)
    catalog_doc = load_json(ADAPTER_CATALOG)
    load_json(ADAPTER_SCHEMA)

    if not DOC.exists():
        errors.append("missing docs/assets/PROTOTYPE_ASSET_IMPORT_ADAPTERS.md")

    sources = {source.get("id"): source for source in sources_doc.get("sources") or []}
    missing_sources = REQUIRED_BATCH2_SOURCES - set(sources)
    if missing_sources:
        errors.append(f"missing batch2 external source records: {sorted(missing_sources)}")

    for sid in BLOCKED_BATCH2_SOURCES:
        source = sources.get(sid)
        if not source:
            continue
        if "blocked" not in source.get("commercialRuntimePolicy", ""):
            errors.append(f"{sid} must remain blocked/reference-only")
        if source.get("processedPrototypePath"):
            errors.append(f"{sid} must not have processedPrototypePath")

    queue_entries = queue_doc.get("entries") or []
    queue_sources = {entry.get("externalSourceId") for entry in queue_entries if "blocked" not in (entry.get("status") or "")}
    for required_allowed in [
        "third_party.pipoya.free_rpg_world_tileset_32_40_48",
        "third_party.henrysoftware.free_pixel_food_cc0",
        "third_party.ghostpixxells.pixel_mart_cc0",
    ]:
        if required_allowed not in queue_sources:
            errors.append(f"{required_allowed} needs a non-blocked prototype queue entry")

    if catalog_doc.get("schema") != "havenwild.prototype_asset_import_adapter_catalog.v0_1":
        errors.append(f"adapter catalog schema mismatch: {catalog_doc.get('schema')}")
    if catalog_doc.get("defaultCopyMode") != "no_raw_copy":
        errors.append("adapter catalog defaultCopyMode must be no_raw_copy")

    adapter_paths = catalog_doc.get("adapters") or []
    if len(adapter_paths) < 3:
        errors.append(f"expected at least 3 prototype import adapters, found {len(adapter_paths)}")

    adapters: list[dict] = []
    seen_paths: set[str] = set()
    for adapter_path in adapter_paths:
        if adapter_path in seen_paths:
            errors.append(f"duplicate adapter catalog path: {adapter_path}")
        seen_paths.add(adapter_path)
        if not str(adapter_path).startswith("content/assets/prototype_imports/adapters/"):
            errors.append(f"adapter path outside expected folder: {adapter_path}")
            continue
        path = ROOT / adapter_path
        if not path.exists():
            errors.append(f"adapter file missing: {adapter_path}")
            continue
        adapters.append(load_json(path))

    adapter_ids = {adapter.get("id") for adapter in adapters}
    missing_adapters = REQUIRED_ADAPTER_IDS - adapter_ids
    if missing_adapters:
        errors.append(f"missing required adapter ids: {sorted(missing_adapters)}")

    seen_adapter_ids: set[str] = set()
    output_metadata_paths: set[str] = set()
    processed_atlas_targets: set[str] = set()
    for adapter in adapters:
        aid = adapter.get("id", "<missing>")
        if aid in seen_adapter_ids:
            errors.append(f"duplicate adapter id: {aid}")
        seen_adapter_ids.add(aid)

        if adapter.get("schema") != "havenwild.prototype_asset_import_adapter.v0_1":
            errors.append(f"{aid} schema mismatch: {adapter.get('schema')}")
        sid = adapter.get("externalSourceId")
        if sid not in sources:
            errors.append(f"{aid} references missing externalSourceId {sid}")
        if sid in BLOCKED_BATCH2_SOURCES:
            errors.append(f"{aid} must not target blocked source {sid}")
        if adapter.get("sourceMode") != "user_supplied_or_quarantine":
            errors.append(f"{aid} sourceMode must be user_supplied_or_quarantine")
        if adapter.get("copyMode") not in {"no_raw_copy", "metadata_stub_only"}:
            errors.append(f"{aid} copyMode must be no_raw_copy or metadata_stub_only")

        inputs = adapter.get("sourceInputs") or []
        if not inputs:
            errors.append(f"{aid} must declare sourceInputs")
        for source_input in inputs:
            archive_name = source_input.get("archiveName")
            if not archive_name:
                errors.append(f"{aid} source input missing archiveName")
            grid = source_input.get("gridSize")
            if grid is not None and (len(grid) != 2 or grid[0] <= 0 or grid[1] <= 0):
                errors.append(f"{aid} invalid gridSize: {grid}")

        output = adapter.get("outputPlan") or {}
        metadata = output.get("metadata", "")
        processed_atlas = output.get("processedAtlas", "")
        if not metadata.startswith("content/assets/") or not metadata.endswith(".hhasset.json"):
            errors.append(f"{aid} metadata output must be content/assets/**/*.hhasset.json: {metadata}")
        else:
            output_metadata_paths.add(metadata)
            if not (ROOT / metadata).exists():
                errors.append(f"{aid} metadata stub missing: {metadata}")
        if processed_atlas:
            if not processed_atlas.startswith("assets/processed/"):
                errors.append(f"{aid} processed atlas must stay under assets/processed/: {processed_atlas}")
            processed_atlas_targets.add(processed_atlas)
            # This pass is metadata-only; the actual binary atlas should not be created yet.
            if (ROOT / processed_atlas).exists():
                errors.append(f"{aid} processed atlas unexpectedly exists during no-raw-copy pass: {processed_atlas}")

        release = adapter.get("releaseGate") or {}
        if release.get("runtimeDefault") is not False:
            errors.append(f"{aid} releaseGate.runtimeDefault must be false")
        if release.get("publicRepoRawAssetCopy") is not False:
            errors.append(f"{aid} releaseGate.publicRepoRawAssetCopy must be false")
        if release.get("requiresNoStandaloneAssetExport") is not True:
            errors.append(f"{aid} must require no standalone asset export")

    # Metadata stubs must point back to real adapters and external sources.
    for metadata in sorted(output_metadata_paths):
        doc = load_json(ROOT / metadata)
        if doc.get("schema") != "havenwild.prototype_asset.v0_1":
            errors.append(f"{metadata} schema mismatch: {doc.get('schema')}")
        if doc.get("externalSourceId") not in sources:
            errors.append(f"{metadata} references missing externalSourceId {doc.get('externalSourceId')}")
        if doc.get("adapterId") not in adapter_ids:
            errors.append(f"{metadata} references missing adapterId {doc.get('adapterId')}")
        if doc.get("runtimeDefault") is not False:
            errors.append(f"{metadata} runtimeDefault must be false")
        if "requiresNoStandaloneAssetExport" not in (doc.get("validation") or {}):
            warnings.append(f"{metadata} should explicitly validate no standalone asset export")

    # Raw archives must not be copied into assets/content as part of this pass.
    for root in [ROOT / "assets", ROOT / "content"]:
        if not root.exists():
            continue
        for path in root.rglob("*.zip"):
            if path.name in RAW_ARCHIVE_NAMES:
                errors.append(f"raw uploaded third-party archive copied into repo tree: {rel(path)}")

    # Quarantine dirs should exist but be placeholder-only in this pass.
    for sid in REQUIRED_BATCH2_SOURCES:
        source = sources.get(sid)
        if not source:
            continue
        qpath = source.get("rawQuarantinePath", "")
        if not qpath.startswith("assets/reference_quarantine/third_party/"):
            errors.append(f"{sid} invalid quarantine path: {qpath}")
            continue
        qdir = ROOT / qpath
        if not qdir.exists():
            errors.append(f"{sid} quarantine directory missing: {qpath}")
            continue
        payload = [p for p in qdir.rglob("*") if p.is_file() and p.name != ".gitkeep"]
        if payload:
            warnings.append(f"{qpath} contains payload files; verify they remain local/quarantined")

    if errors:
        print("Validate-PrototypeAssetImportAdapterV26: FAILED")
        for error in errors:
            print(f"ERROR: {error}")
        for warning in warnings:
            print(f"WARN: {warning}")
        return 1

    print("Validate-PrototypeAssetImportAdapterV26: OK")
    print(f"sources={len(sources)} queue_entries={len(queue_entries)} adapters={len(adapters)} metadata_stubs={len(output_metadata_paths)} atlas_targets={len(processed_atlas_targets)}")
    for warning in warnings:
        print(f"WARN: {warning}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
