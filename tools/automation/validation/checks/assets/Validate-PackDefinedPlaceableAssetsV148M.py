#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
def require(path: str) -> str:
    target = ROOT / path
    if not target.is_file():
        raise SystemExit(f"missing required Pass 148M file: {path}")
    return target.read_text(encoding="utf-8")


def main() -> None:
    registry = require("crates/haven_assets/src/placeable_asset_registry.rs")
    runtime = require("crates/haven_game/src/runtime_editor_shell.rs") + "\n" + require("crates/haven_game/src/runtime_editor_shell/world_builder.rs")
    runtime_assets = require("crates/haven_game/src/runtime_assets.rs")
    editor = require("apps/haven_editor_native/src/app/scene_authoring.rs")
    editor_app = require("apps/haven_editor_native/src/app/mod.rs")
    policy = json.loads(require("content/asset_packs/placeable_asset_policy_v1.json"))
    catalog = json.loads(require("content/asset_packs/havenwild_objects/published_world_assets_v1.json"))
    pack = json.loads(require("content/asset_packs/havenwild_objects/pack.json"))

    tokens = [
        "pub struct PublishedWorldAssetDefinition",
        "pub struct PublishedWorldAssetRegistry",
        "pub fn load_discovered",
        'starts_with("world_asset.catalog.")',
        'format!("{}::{}"',
        "footprint_for_legacy_object",
        "allowed_surfaces",
        "forbidden_surfaces",
        "placement_tags",
        "states",
    ]
    missing = [token for token in tokens if token not in registry]
    if missing:
        raise SystemExit("placeable registry contract missing: " + ", ".join(missing))

    if catalog.get("schema") != "havenwild.published_world_asset_catalog.v1":
        raise SystemExit("placeable catalog schema mismatch")
    entries = catalog.get("entries", [])
    categories = {entry.get("category") for entry in entries}
    if len(entries) < 6 or len(categories) < 4:
        raise SystemExit("placeable proof catalog must cover at least six entries across four categories")
    for entry in entries:
        for field in ("id", "semantic_id", "category", "footprint"):
            if field not in entry:
                raise SystemExit(f"placeable entry lacks {field}: {entry.get('id')}")
        footprint = entry["footprint"]
        for field in ("visual_size", "collision_size", "interaction_size"):
            if field not in footprint:
                raise SystemExit(f"{entry['id']} footprint lacks {field}")

    providers = [asset for asset in pack.get("assets", []) if str(asset.get("semantic_id", "")).startswith("world_asset.catalog.")]
    if not providers:
        raise SystemExit("havenwild_objects does not expose a placeable catalog provider")

    for name, text in {
        "runtime startup": runtime_assets,
        "runtime F3": runtime,
        "native editor startup": editor_app,
        "native editor placement": editor,
    }.items():
        if "PublishedWorldAssetRegistry" not in text and "PlaceableAssetRegistry" not in text and "placeable_registry" not in text:
            raise SystemExit(f"{name} is not wired to the shared placeable registry")
    if "place_custom_object(preview)" not in runtime:
        raise SystemExit("runtime F3 does not commit the pack-defined footprint")
    if "place_scene_object_with_footprint" not in editor:
        raise SystemExit("native editor does not commit the pack-defined footprint")

    rules = policy.get("rules", {})
    required_rules = {
        "discover_from_all_mounted_production_packs",
        "stable_identity_is_pack_qualified",
        "footprints_are_pack_defined",
        "anchors_are_pack_defined",
        "collision_is_pack_defined",
        "placement_surfaces_are_pack_defined",
        "states_are_pack_defined",
        "runtime_and_editor_share_registry",
        "unknown_categories_are_allowed",
    }
    if not all(rules.get(rule) for rule in required_rules):
        raise SystemExit("placeable policy is missing required generic rules")
    consumers = set(policy.get("consumers", []))
    if not {"runtime_f3", "native_editor", "content_browser", "asset_palette", "pcg"}.issubset(consumers):
        raise SystemExit("placeable policy is missing required consumers")

    print(f"Pass 148M pack-defined placeable assets valid: {len(entries)} proof entries, {len(categories)} categories")


if __name__ == "__main__":
    main()
