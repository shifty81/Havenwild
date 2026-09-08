#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
SWEEP = ROOT / "content/asset_packs/havenwild_objects/placeable_visual_sweep_v1.json"
CATALOG = ROOT / "content/asset_packs/havenwild_objects/published_world_assets_v1.json"
MANIFEST = ROOT / "assets/generated/havenwild_lpc_objects_160x192_v2.json"
ASSET_REGISTRY = ROOT / "crates/haven_assets/src/asset_registry.rs"
OBJECT_KINDS = ROOT / "crates/haven_core/src/foundation/tile_object_catalog.rs"
PROMOTER = ROOT / "tools/automation/assets/Promote-LpcRuntimeAssets.py"


def need(ok: bool, message: str) -> None:
    if not ok:
        raise SystemExit(f"FAIL W43B placeable visual sweep: {message}")


def load(path: Path):
    need(path.is_file(), f"missing {path.relative_to(ROOT)}")
    return json.loads(path.read_text(encoding="utf-8"))


sweep = load(SWEEP)
catalog = load(CATALOG)
manifest = load(MANIFEST)
registry = ASSET_REGISTRY.read_text(encoding="utf-8")
object_kinds = OBJECT_KINDS.read_text(encoding="utf-8")
promoter = PROMOTER.read_text(encoding="utf-8")

need(sweep.get("schema") == "havenwild.placeable_visual_sweep.v1", "schema mismatch")
need(sweep.get("pass") == "167Z109W43B", "pass mismatch")
entries = sweep.get("entries", [])
need(len(entries) == 26, f"expected all 26 ObjectKinds, got {len(entries)}")
by_kind = {entry.get("objectKind"): entry for entry in entries}
need(len(by_kind) == 26, "duplicate ObjectKind review rows")

expected_kinds = {
    "table", "chair", "bar", "keg", "bed", "fireplace", "greenhouse_marker",
    "tree", "bush", "boulder", "ore_node", "mushroom", "herb", "crate",
    "barrel", "well", "scarecrow", "fence", "lamp", "bench", "stump", "log",
    "sign", "door", "stairs", "cave_entrance",
}
need(set(by_kind) == expected_kinds, "ObjectKind coverage differs from active catalog")
need('ObjectKind::Crate => "Crate",' in object_kinds, "Crate still presents as Crate Stack")
need('ObjectKind::Crate => "Crate Stack",' not in object_kinds, "legacy Crate Stack label survived")

policy = sweep.get("policy", {})
for key in (
    "ordinaryPlaceablesAreSingular",
    "incorrectSemanticSubstitutionsFailClosed",
    "missingArtworkRemainsExplicit",
    "legacyObjectKindIsCompatibilityOnly",
    "crateStacksRequireExplicitAssembly",
    "certificationRequiresRuntimeVisualReview",
):
    need(policy.get(key) is True, f"policy does not lock {key}")

# Singular crate correction must be reproducible from the upstream source sheet.
crate_cache = next((o for o in manifest.get("objects", []) if o.get("id") == "crate_stack"), None)
need(crate_cache is not None, "legacy crate cache record missing")
need(crate_cache.get("sourceRect") == [0, 32, 32, 32], "crate cache is not one exact LPC crate slice")
need(crate_cache.get("sourceMode") == "lpc_exact_source_rect_native_scale_large_cell", "crate source mode is not exact-slice")
need(crate_cache.get("visualFootprintTiles") == [1, 1], "crate visual footprint is not singular 1x1")
need(crate_cache.get("collisionFootprintTiles") == [1, 1], "crate collision footprint is not 1x1")
need('"crate_stack": (0, 32, 32, 32)' in promoter, "asset rebuild will not reproduce singular crate slice")

crate_published = next((e for e in catalog.get("entries", []) if e.get("id") == "container_crate_wood_01"), None)
need(crate_published is not None, "singular crate is not published")
need(crate_published.get("legacy_object_kind") == "crate", "published crate lacks legacy adapter")
need(crate_published.get("legacy_object_kind_primary") is True, "published crate is not primary legacy adapter")
need(crate_published.get("provenance", {}).get("source_rect") == [0, 32, 32, 32], "published crate provenance differs from cache")
need(crate_published.get("footprint", {}).get("visual_size") == [1, 1], "published crate footprint is not 1x1")

# Incorrect substitutions must fail closed in the active legacy visual adapter.
quarantined = {
    "Well": "water cooler",
    "Scarecrow": "dress form",
    "Bench": "ottoman",
    "Log": "lumber",
    "Sign": "standing screen",
    "Stairs": "ladder",
    "GreenhouseMarker": "construction tape",
    "Door": "unaudited door cache",
    "Fence": "unaudited fence cache",
    "CaveEntrance": "structural connector",
}
for rust_kind, reason in quarantined.items():
    pattern = rf"ObjectKind::{re.escape(rust_kind)}\s*=>\s*return None"
    need(re.search(pattern, registry) is not None, f"{rust_kind} does not fail closed ({reason})")

need(by_kind["crate"].get("status") == "CANDIDATE", "crate is not queued for visual certification")
for code in ("well", "scarecrow", "bench", "log", "sign", "stairs"):
    need(by_kind[code].get("status") == "REJECTED", f"{code} bad substitution is not REJECTED")
need(by_kind["greenhouse_marker"].get("status") == "PLACEHOLDER", "greenhouse marker is not explicit placeholder")
for code in ("door", "fence"):
    need(by_kind[code].get("status") == "MISSING", f"{code} missing source is not explicit")
need(by_kind["cave_entrance"].get("role") == "structural_connector", "cave entrance is not deferred to connector authority")

print("PASS W43B placeable visual sweep")
print("- all 26 ObjectKinds have explicit visual/certification disposition")
print("- ordinary Crate now renders one exact LPC crate with 1x1 footprint")
print("- known semantic substitutions and source-less structure cells fail closed")
