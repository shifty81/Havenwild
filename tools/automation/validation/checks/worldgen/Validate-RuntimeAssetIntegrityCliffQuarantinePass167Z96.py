#!/usr/bin/env python3
from __future__ import annotations

import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8-sig")


def load(path: str):
    return json.loads(read(path))


def png_dimensions(path: Path) -> tuple[int, int]:
    data = path.read_bytes()[:24]
    assert data[:8] == b"\x89PNG\r\n\x1a\n", path
    assert data[12:16] == b"IHDR", path
    return struct.unpack(">II", data[16:24])


def require_existing_internal_sources(pack_path: str) -> dict:
    pack = load(pack_path)
    for source in pack["sources"]:
        if source["kind"] == "external_dependency":
            continue
        path = ROOT / source["path"]
        assert path.exists(), f"{pack['id']} missing source {source['id']}: {source['path']}"
    return pack


def main() -> int:
    current = ROOT / "content/worldgen/structural_cliff_autotile_authority_v0_1.json"
    if current.is_file():
        current_authority = json.loads(current.read_text(encoding="utf-8-sig"))
        if current_authority.get("pass") in {"167Z107", "167Z109C", "167Z109D", "167Z109G"} and current_authority.get("status") == "active":
            print("Historical cliff validator superseded by Pass167Z107 structural cliff autotile authority")
        return 0

    contract = load("content/build/runtime_asset_integrity_cliff_quarantine_v167z96.json")
    assert contract["pass"] == "167Z96"
    assert contract["runtimePolicy"]["proceduralCliffDrawing"] is False
    assert contract["runtimePolicy"]["proceduralCliffCollision"] == "fail_open"
    assert contract["runtimePolicy"]["structuralElevationMaterials"] == [
        "mountain_rock", "mountain_path"
    ]
    assert contract["runtimePolicy"]["explicitTraversalAttachmentsRemainSupported"] is False

    for path in contract["stableAssetRepairs"].values():
        if path == "optional_editor_only":
            continue
        assert (ROOT / path).exists(), path

    worldgen = require_existing_internal_sources(
        "content/asset_packs/havenwild_worldgen/pack.json"
    )
    sources = {row["id"]: row["path"] for row in worldgen["sources"]}
    assert sources["terrain_transition_atlas"].endswith("terrain_autotile_47_32.png")
    assert sources["worldgen_manifest"].endswith("common_base_terrain_32.json")
    assert "animated_water" not in sources
    assert "world_paint_compatibility" not in sources
    assets = {row["id"]: row for row in worldgen["assets"]}
    assert assets["shallow_water"]["source_id"] == "mapped_lpc_terrain"
    assert assets["deep_water"]["source_id"] == "mapped_lpc_terrain"

    objects = require_existing_internal_sources(
        "content/asset_packs/havenwild_objects/pack.json"
    )
    object_sources = {row["id"]: row["path"] for row in objects["sources"]}
    for source_id in ("runtime_objects", "structures", "trees", "clutter"):
        assert object_sources[source_id].endswith("havenwild_lpc_objects_160x192_v2.png")

    interface = require_existing_internal_sources(
        "content/asset_packs/havenwild_interface/pack.json"
    )
    semantics = {row["semantic_id"] for row in interface["assets"]}
    assert {
        "ui.hud.vitals.frame", "ui.hud.hotbar.frame", "ui.hud.minimap.frame"
    } <= semantics
    require_existing_internal_sources("content/asset_packs/havenwild_audio/pack.json")

    oga = require_existing_internal_sources("content/asset_packs/oga_lpc_cliffs/pack.json")
    assert oga["version"] == "0.3.0"
    assert oga["production_enabled"] is False
    assert all(not row["semantic_id"].startswith("stamp.catalog.") for row in oga["assets"])
    source_path = ROOT / oga["sources"][0]["path"]
    assert png_dimensions(source_path) == (384, 288)

    recipe = load("content/assets/oga_lpc/manifests/oga_lpc_cliff_recipe_catalog_v0_2.json")
    assert recipe["sourceDimensions"] == [384, 288]
    assert recipe["runtimeStatus"] == "quarantined"
    assert recipe["recipes"] == []

    draw = read("crates/haven_game/src/runtime_structural_cliff_draw.rs")
    z106 = ROOT / "content/worldgen/elizawy_cliff_runtime_preview_certification_v0_1.json"
    if z106.is_file():
        preview = load("content/worldgen/elizawy_cliff_runtime_preview_certification_v0_1.json")
        assert preview["pass"] == "167Z106"
        assert preview["runtimeGate"]["collision"] == "fail_open"
        assert preview["certifiedRuntimeVisual"]["runtimeVisualEnabled"] is True
        assert "draw_texture_ex" in draw
        assert "SOUTH_FACE_SOURCE" in draw
    else:
        assert "pub(super) fn draw_structural_cliffs(&self) {}" in draw
        assert "draw_texture_ex" not in draw

    bridge = read("crates/haven_world/src/terrain_cliff_bridge.rs")
    assert "TileKind::MountainRock | TileKind::MountainPath" in bridge
    assert "general_grass_never_inherits_structural_cliffs_from_geology" in bridge

    movement = read("crates/haven_game/src/runtime_surface_streaming.rs")
    assert "Z96 fail-open authority" in movement
    assert '"oga_lpc.cliff.ladder"' not in movement
    assert "fn structural_attachment_opens_edge" in movement
    assert "false" in movement.split("fn structural_attachment_opens_edge", 1)[1]

    runtime_assets = read("crates/haven_game/src/runtime_assets.rs")
    assert "Asset-pack diagnostic:" in runtime_assets
    assert "content/ui/hud/vitals_frame.png" in runtime_assets
    assert "world_paint_path.is_file()" in runtime_assets
    for obsolete in (
        "terrain_autotile_16_32.png",
        "havenwild_lpc_runtime_objects.png",
        "havenwild_vitals_frame_v1.png",
        "havenwild_hotbar_frame_v1.png",
        "havenwild_minimap_frame_v1.png",
        "home_island_trees_32.png",
    ):
        assert obsolete not in runtime_assets

    diagnostics = read("crates/haven_game/src/runtime_diagnostics.rs")
    assert "Pass 167Z96" in diagnostics or "Pass 167Z97" in diagnostics
    print("Pass167Z96 runtime asset integrity and cliff quarantine validated")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
