#!/usr/bin/env python3
from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
EXTERNAL = ROOT / "content/assets/external_sources/external_asset_sources_v0_1.json"
DONOR = ROOT / "content/assets/donor_reference/donor_reference_asset_catalog_v0_1.json"
ASSET_CATALOG = ROOT / "content/assets/catalog/havenwild_asset_catalog_v0_1.json"
PIXEL = ROOT / "content/assets/pixel_editor/pixel_editor_reference_workbench_v0_1.json"
SCHEMAS = [
    ROOT / "content/schemas/donor_reference_asset_catalog.schema.v0_1.json",
    ROOT / "content/schemas/havenwild_asset_catalog.schema.v0_1.json",
]

ERRORS: list[str] = []
WARNINGS: list[str] = []

def load(path: Path):
    if not path.exists():
        ERRORS.append(f"missing required file: {path.relative_to(ROOT)}")
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        ERRORS.append(f"failed to parse {path.relative_to(ROOT)}: {exc}")
        return {}

def main() -> int:
    external = load(EXTERNAL)
    donor = load(DONOR)
    asset_catalog = load(ASSET_CATALOG)
    pixel = load(PIXEL)
    for schema in SCHEMAS:
        if not schema.exists():
            ERRORS.append(f"missing schema: {schema.relative_to(ROOT)}")

    if donor.get("schema") != "havenwild.donor_reference_asset_catalog.v0_1":
        ERRORS.append("donor catalog has invalid schema")
    if asset_catalog.get("schema") != "havenwild.asset_catalog.v0_1":
        ERRORS.append("unified asset catalog has invalid schema")
    if pixel.get("schema") != "havenwild.pixel_editor_reference_workbench.v0_1":
        ERRORS.append("pixel editor reference workbench has invalid schema")

    sources = {s.get("id"): s for s in external.get("sources", [])}
    blocked = {
        sid for sid, source in sources.items()
        if "blocked" in str(source.get("commercialRuntimePolicy", ""))
        or "unverified" in str(source.get("licenseStatus", ""))
    }
    ids: set[str] = set()
    records = donor.get("records", [])
    if len(records) < 10:
        ERRORS.append("donor catalog should include all audited donor packs; expected at least 10 records")
    for record in records:
        rid = record.get("id")
        if not rid:
            ERRORS.append("donor record missing id")
            continue
        if rid in ids:
            ERRORS.append(f"duplicate donor record id: {rid}")
        ids.add(rid)
        source_id = record.get("externalSourceId")
        if source_id not in sources:
            ERRORS.append(f"{rid}: unknown externalSourceId {source_id}")
        if not record.get("tileGridProfiles"):
            ERRORS.append(f"{rid}: missing tileGridProfiles")
        else:
            for profile in record.get("tileGridProfiles", []):
                if not isinstance(profile, list) or len(profile) != 2:
                    ERRORS.append(f"{rid}: invalid tileGridProfile {profile}")
                    continue
                w, h = profile
                if not isinstance(w, int) or not isinstance(h, int) or w <= 0 or h <= 0 or w > 256 or h > 256:
                    ERRORS.append(f"{rid}: unsupported tileGridProfile {profile}")
        vis = record.get("editorVisibility", {})
        for key in ["standaloneEditor", "inGameEditorDevMode", "litePixelEditorPanel", "runtimeGameDefault"]:
            if not vis.get(key):
                ERRORS.append(f"{rid}: missing editorVisibility.{key}")
        if source_id in blocked:
            if vis.get("runtimeGameDefault") != "blocked":
                ERRORS.append(f"{rid}: blocked/unverified donor source must have runtimeGameDefault=blocked")
            ingest = str(record.get("prototypeIngestPolicy", ""))
            if "blocked" not in ingest and "license" not in ingest and "attribution" not in ingest:
                ERRORS.append(f"{rid}: blocked/unverified donor must keep prototypeIngestPolicy gated")
        if not record.get("families"):
            WARNINGS.append(f"{rid}: no families/tags for filtering")

    index_paths = {entry.get("path") for entry in asset_catalog.get("indexes", [])}
    required = {
        "content/assets/external_sources/external_asset_sources_v0_1.json",
        "content/assets/donor_reference/donor_reference_asset_catalog_v0_1.json",
        "content/assets/prototype_imports/prototype_asset_import_queue_v0_1.json",
        "content/assets/prototype_imports/prototype_asset_import_adapters_v0_1.json",
    }
    missing = required - index_paths
    for path in sorted(missing):
        ERRORS.append(f"unified asset catalog missing index path {path}")

    if pixel.get("catalogPath") != "content/assets/donor_reference/donor_reference_asset_catalog_v0_1.json":
        ERRORS.append("pixel editor workbench must point to donor reference catalog")
    blocked_actions = pixel.get("blockedActions", [])
    if not any("trace_restricted_asset_pixels" in action for action in blocked_actions):
        ERRORS.append("pixel editor workbench must block tracing restricted asset pixels")
    if not pixel.get("tileSetTemplates"):
        ERRORS.append("pixel editor workbench missing tileSetTemplates")

    if WARNINGS:
        print("WARNINGS:")
        for warning in WARNINGS:
            print(" -", warning)
    if ERRORS:
        print("ERRORS:")
        for error in ERRORS:
            print(" -", error)
        return 1
    print(f"Validate-DonorReferenceAssetCatalogV27: OK ({len(records)} donor records)")
    return 0

if __name__ == "__main__":
    sys.exit(main())
