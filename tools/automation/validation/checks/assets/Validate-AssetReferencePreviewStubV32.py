#!/usr/bin/env python3
"""Validate Havenwild asset reference preview catalog wiring."""
from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
PREVIEW = ROOT / "content/assets/reference_previews/asset_reference_preview_catalog_v0_1.json"
DONOR = ROOT / "content/assets/donor_reference/donor_reference_asset_catalog_v0_1.json"
ASSET_INDEX = ROOT / "content/assets/catalog/havenwild_asset_catalog_v0_1.json"
RUST_MODEL = ROOT / "crates/haven_assets/src/asset_reference_preview.rs"
RUST_LIB = ROOT / "crates/haven_assets/src/lib.rs"
PANEL = ROOT / "crates/haven_game/src/asset_reference_browser_panel.rs"
SCHEMA = ROOT / "content/schemas/asset_reference_preview_catalog.schema.v0_1.json"
DOC = ROOT / "docs/assets/ASSET_REFERENCE_PREVIEW_STUB.md"

errors: list[str] = []

def load(path: Path):
    if not path.exists():
        errors.append(f"missing {path.relative_to(ROOT)}")
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"invalid json {path.relative_to(ROOT)}: {exc}")
        return {}

preview = load(PREVIEW)
donor = load(DONOR)
asset_index = load(ASSET_INDEX)
_ = load(SCHEMA)

if preview.get("schema") != "havenwild.asset_reference_preview_catalog.v0_1":
    errors.append("preview catalog has wrong schema")

preview_records = preview.get("records", [])
if not preview_records:
    errors.append("preview catalog has no records")

donor_source_ids = {record.get("externalSourceId") for record in donor.get("records", [])}
preview_ids = [record.get("externalSourceId") for record in preview_records]
if len(preview_ids) != len(set(preview_ids)):
    errors.append("duplicate externalSourceId in preview catalog")

missing_from_preview = sorted(source_id for source_id in donor_source_ids if source_id not in set(preview_ids))
if missing_from_preview:
    errors.append("donor sources missing preview metadata: " + ", ".join(missing_from_preview))

unknown_preview_ids = sorted(source_id for source_id in preview_ids if source_id not in donor_source_ids)
if unknown_preview_ids:
    errors.append("preview records reference unknown donor source: " + ", ".join(unknown_preview_ids))

for record in preview_records:
    sid = record.get("externalSourceId", "<missing>")
    path = record.get("safePreviewPath", "")
    if not path.startswith("WORKSPACE/generated/asset_reference_previews/"):
        errors.append(f"{sid}: safePreviewPath must stay under WORKSPACE/generated/asset_reference_previews/")
    if path.lower().endswith((".zip", ".aseprite", ".tsx", ".tmx")):
        errors.append(f"{sid}: preview path must point to a generated image/contact sheet, not raw/source file")
    policy = record.get("sourcePolicy", "")
    if "reference_only" in policy and "runtime" in record.get("editorDisplay", ""):
        errors.append(f"{sid}: reference-only source should not claim runtime preview display")

indexes = asset_index.get("indexes", [])
if not any(entry.get("id") == "asset_reference_previews" and entry.get("path") == "content/assets/reference_previews/asset_reference_preview_catalog_v0_1.json" for entry in indexes):
    errors.append("havenwild asset catalog index does not reference asset_reference_previews")

for path, needle in [
    (RUST_MODEL, "ASSET_REFERENCE_PREVIEW_CATALOG_PATH"),
    (RUST_LIB, "pub mod asset_reference_preview;"),
    (PANEL, "show_asset_reference_preview_status"),
    (PANEL, "ASSET_REFERENCE_PREVIEW_CATALOG_PATH"),
    (PANEL, "Preview"),
    (DOC, "Asset Reference Preview Stub"),
]:
    if not path.exists():
        errors.append(f"missing {path.relative_to(ROOT)}")
    elif needle not in path.read_text(encoding="utf-8"):
        errors.append(f"{path.relative_to(ROOT)} missing marker {needle!r}")

if errors:
    print("Validate-AssetReferencePreviewStubV32 FAILED")
    for error in errors:
        print(f" - {error}")
    sys.exit(1)

print(f"Validate-AssetReferencePreviewStubV32 passed: {len(preview_records)} preview metadata records")
