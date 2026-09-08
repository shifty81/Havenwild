#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
def require(path: str) -> str:
    target = ROOT / path
    if not target.is_file():
        raise SystemExit(f"missing required Pass 148L file: {path}")
    return target.read_text(encoding="utf-8")


def main() -> None:
    stamp = require("crates/haven_assets/src/stamp_registry.rs")
    runtime = require("crates/haven_game/src/runtime_assets.rs")
    editor = require("apps/haven_editor_native/src/app/mod.rs")
    atlas = require("apps/haven_editor_native/src/app/atlas_render.rs")
    palette = require("crates/haven_assets/src/asset_palette.rs")
    policy = json.loads(require("content/asset_packs/semantic_stamp_discovery_policy_v1.json"))
    objects = json.loads(require("content/asset_packs/havenwild_objects/pack.json"))

    required_stamp_tokens = [
        "pub fn load_discovered",
        'starts_with("stamp.catalog.")',
        'get("sheet_semantic_id")',
        "catalog_ref: Option<StableAssetRef>",
        "sheet_ref: Option<StableAssetRef>",
        'format!("{}::{}"',
        "legacy_id",
    ]
    missing = [token for token in required_stamp_tokens if token not in stamp]
    if missing:
        raise SystemExit("stamp discovery contract missing: " + ", ".join(missing))
    if "pub const STAMP_MANIFESTS" in stamp:
        raise SystemExit("static STAMP_MANIFESTS registry must not remain authoritative")

    for name, text in {
        "runtime F3": runtime,
        "native editor": editor,
        "editor texture set": atlas,
        "asset palette": palette,
    }.items():
        if "StampRegistry::load_discovered" not in text:
            raise SystemExit(f"{name} does not use discovered stamp providers")

    catalogs = [
        asset for asset in objects.get("assets", [])
        if asset.get("category") == "editor_template"
        and str(asset.get("semantic_id", "")).startswith("stamp.catalog.")
    ]
    if not catalogs:
        raise SystemExit("no semantic stamp catalog provider is declared")
    for catalog in catalogs:
        metadata = catalog.get("metadata", {})
        if not metadata.get("sheet_semantic_id"):
            raise SystemExit(f"{catalog.get('id')} lacks sheet_semantic_id")

    rules = policy.get("rules", {})
    if not rules.get("no_static_manifest_registry"):
        raise SystemExit("policy must prohibit a static stamp manifest registry")
    consumers = set(policy.get("consumers", []))
    required_consumers = {"runtime_f3", "native_editor", "asset_palette", "runtime_renderer"}
    if not required_consumers.issubset(consumers):
        raise SystemExit("policy does not cover all stamp consumers")

    print(f"Pass 148L semantic stamp discovery valid: {len(catalogs)} catalog provider(s), {len(consumers)} consumers")


if __name__ == "__main__":
    main()
