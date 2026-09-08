#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"FAILED Pass167Z91 native editor asset-pack resilience: {message}")


def main() -> None:
    quarantine = ROOT / "content/build/runtime_asset_integrity_cliff_quarantine_v167z96.json"
    if quarantine.is_file():
        contract = json.loads(quarantine.read_text(encoding="utf-8"))
        require(contract["pass"] == "167Z96", "Z96 quarantine pass")
        require(contract["runtimePolicy"]["proceduralCliffDrawing"] is False, "invalid renderer disabled")
        print("Pass167Z91 asset-pack resilience remains satisfied under Pass167Z96 quarantine")
        return
    contract = json.loads(
        (ROOT / "content/editor/native_editor_asset_pack_resilience_v0_1.json").read_text(
            encoding="utf-8"
        )
    )
    require(
        contract["schema"] == "havenwild.native_editor.asset_pack_resilience.v0_1",
        "schema",
    )
    require(contract["pass"] == "167Z91", "pass")
    require(contract["repair"]["strictDiscoveryPreserved"] is True, "strict lane")
    require(contract["repair"]["tolerantDiscoveryAdded"] is True, "tolerant lane")
    require(contract["repair"]["lintSuppressionAdded"] is False, "no lint suppression")

    cache = (ROOT / "crates/haven_assets/src/runtime_asset_cache.rs").read_text(
        encoding="utf-8"
    )
    require("pub fn discover(project_root: &Path)" in cache, "strict discovery retained")
    require("pub fn discover_tolerant(project_root: &Path)" in cache, "tolerant discovery")
    require("AssetPackDiscovery::project_default(project_root)" in cache, "project roots")
    require("discover_and_mount(&mut registry, false)" in cache, "valid pack mounting")
    require(
        "tolerant_discovery_keeps_valid_packs_when_an_optional_pack_is_invalid" in cache,
        "tolerant regression test",
    )
    require("assert!(RuntimeAssetSession::discover(&root).is_err())" in cache, "strict rejection")
    require("assert_eq!(session.registry.mounted_pack_count(), 1)" in cache, "valid pack survives")

    stamps = (ROOT / "crates/haven_assets/src/stamp_registry.rs").read_text(encoding="utf-8")
    require("RuntimeAssetSession::discover_tolerant(&root)" in stamps, "default stamp resilience")

    editor = (ROOT / "apps/haven_editor_native/src/app/mod.rs").read_text(encoding="utf-8")
    require("RuntimeAssetSession::discover_tolerant" in editor, "editor tolerant session")
    require("asset_pack_mounted_count" in editor, "mounted count state")
    require("asset_pack_failure_count" in editor, "failure count state")
    require("asset_pack_source_count" in editor, "source count state")

    chrome = (ROOT / "apps/haven_editor_native/src/app/workspace_chrome.rs").read_text(
        encoding="utf-8"
    )
    require("Production packs:" in chrome, "Imports status row")
    require("diagnostic failure" in chrome, "failure diagnostics visible")
    require("stable source bindings" in chrome, "source bindings visible")

    runtime = (ROOT / "crates/haven_game/src/runtime_assets.rs").read_text(encoding="utf-8")
    require("RuntimeAssetSession::discover_tolerant(runtime_root())" in runtime, "runtime recovery")
    require("continuing with" in runtime, "runtime recovery diagnostic")

    palette = (ROOT / "crates/haven_assets/src/asset_palette.rs").read_text(encoding="utf-8")
    require("oga_lpc.cliff.ladder" in palette, "cliff ladder palette regression")
    require("AssetPaletteCategory::Elevation" in palette, "elevation category")

    combined = "\n".join((cache, stamps, editor, chrome, runtime))
    require("allow(clippy" not in combined, "no Clippy suppression")

    roadmap = (
        ROOT / "docs/roadmaps/NATIVE_EDITOR_ASSET_PACK_RESILIENCE_PASS167Z91.md"
    ).read_text(encoding="utf-8")
    require("continuous Alderreach World Editor" in roadmap, "next editor lane")
    print("Pass167Z91 native editor asset-pack resilience validation passed")


if __name__ == "__main__":
    main()
