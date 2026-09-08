#!/usr/bin/env python3
"""Validate W56I/J integrated editor/client visual acceptance authority."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
SCENE_REL = "content/worldgen/scenes/world_asset_acceptance/w56_integrated_visual_acceptance_scene_v1.json"
PACK_REL = "content/worldgen/packs/worldgen_w56_integrated_visual_acceptance_v0_1.json"
INSTANCE_REL = "content/buildings/instances/w56_integrated_visual_acceptance_cottage_v1.json"
INSTANCE_ID = "havenwild.acceptance.w56_integrated_cottage"
SCENE_ID = "w56_integrated_visual_acceptance"
REPORT = ROOT / "content/build/w56ij_integrated_visual_acceptance_v1.json"


def load(rel: str):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def req(condition: bool, message: str):
    if not condition:
        raise AssertionError(message)


def text(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


try:
    scene = load(SCENE_REL)
    pack = load(PACK_REL)
    test_pack = load("content/worldgen/packs/worldgen_home_island_test_v0_11.json")
    instance = load(INSTANCE_REL)
    catalog = load("content/buildings/building_instance_catalog_v1.json")
    recipe = load("content/buildings/recipes/estate_starter_cottage_v1.json")
    published_data = load("content/asset_packs/havenwild_objects/published_world_assets_v1.json")
    published = {entry["id"]: entry for entry in published_data["entries"]}

    req(scene.get("sceneId") == SCENE_ID, "integrated acceptance scene identity drift")
    req(scene.get("role") == "development_acceptance", "integrated scene must remain development-only")
    req(scene.get("sceneSize") == [96, 64], "integrated scene must use one full runtime partition")
    terrain = scene["layers"]["terrain"]
    levels = scene["layers"]["structuralLevels"]
    req(len(terrain) == 64 and all(len(row) == 96 for row in terrain), "terrain dimensions drift")
    req(len(levels) == 64 and all(len(row) == 96 for row in levels), "structural level dimensions drift")
    present_levels = sorted({int(value) for row in levels for value in row})
    req(present_levels == [0, 1, 2, 3, 4], f"expected structural levels 0-4, got {present_levels}")
    for requested in (1, 2, 3, 4):
        req(sum(value == requested for row in levels for value in row) >= 80, f"Level {requested} fixture is too small")

    objects = scene.get("objects", [])
    req(len(objects) >= 20, "integrated acceptance board lost object density")
    ids = [obj.get("assetId") for obj in objects]
    unresolved = sorted({asset for asset in ids if asset not in published})
    req(not unresolved, f"integrated scene contains unpublished assets: {unresolved}")
    natural_categories = {"tree", "foliage"}
    natural_ids = [asset for asset in ids if published[asset].get("category") in natural_categories or asset.startswith("resource_boulder") or asset == "tree_fallen_log_01"]
    req(len(natural_ids) >= 16, "integrated acceptance board is too sparse")
    req(len(set(natural_ids)) >= 12, "integrated acceptance board lacks semantic nature variation")

    cave = next(obj for obj in objects if obj.get("id") == "w56_integrated_cave_mouth")
    req(cave.get("assetId") == "cave_entrance_default", "integrated cave does not use certified narrow source")
    req(cave.get("visualRect", [])[2:] == [1, 3], "cave source/host visual must remain 1x3")
    req(cave.get("collisionRect", [])[2:] == [0, 0] and not cave.get("blocksMovement", True), "open cave mouth must not block aperture")
    aperture = cave.get("interactions", [{}])[0].get("rect", [])
    req(aperture[2:] == [1, 2], "visible/interactive cave aperture must remain 1x2")

    req(instance.get("id") == INSTANCE_ID and instance.get("sceneId") == SCENE_ID, "diagnostic cottage instance identity drift")
    req(instance.get("recipeId") == "havenwild.estate.starter_cottage", "diagnostic cottage must reuse production starter recipe")
    req(instance.get("diagnosticOnly") is True, "integrated cottage must remain diagnostic-only")
    req(recipe.get("footprint") in ([10, 8], [9, 9]), "starter cottage production recipe footprint drift")
    catalog_entry = next((entry for entry in catalog.get("entries", []) if entry.get("id") == INSTANCE_ID), None)
    req(catalog_entry is not None and catalog_entry.get("path") == INSTANCE_REL, "BuildingInstance catalog missing W56 diagnostic cottage")

    req(pack.get("defaultScene") == SCENE_ID and pack.get("sceneFiles") == [SCENE_REL], "isolated W56 acceptance pack drift")
    req(pack.get("requiresLegacySceneSet") is False, "W56 acceptance pack must not require legacy scene bank")
    req(SCENE_REL in test_pack.get("sceneFiles", []), "development test pack does not expose integrated acceptance scene")
    req(SCENE_REL in test_pack.get("smokeTests", []), "integrated acceptance scene missing from development smoke tests")
    tw = test_pack.get("testWorld", {})
    req(tw.get("w56IntegratedVisualAcceptanceSceneId") == SCENE_ID, "test-world W56 scene id registration missing")

    runtime = text("crates/haven_game/src/runtime_content_authority.rs")
    entry = text("crates/haven_game/src/client_entry.rs")
    editor = text("apps/haven_editor_native/src/app/mod.rs")
    loader = text("crates/haven_core/src/worldgen_loader.rs")
    loader_structural = text("crates/haven_core/src/worldgen_loader_structural.rs")
    exporter = text("crates/haven_core/src/worldgen_exporter.rs")
    build = text("tools/build/Build.sh")
    controls = text("tools/control/HavenwildTools.ps1")
    registry = text("tools/control/ProjectCommandRegistry.ps1")
    for token in ("IntegratedVisualAcceptance", PACK_REL, SCENE_ID, "integrated_visual_acceptance_world_is_current"):
        req(token in runtime, f"runtime W56 visual acceptance hook missing: {token}")
    req("mod structural;" in loader and "parse_structural_levels(" in loader, "worldgen loader is not wired to authored structuralLevels")
    req("MAX_STRUCTURAL_LEVEL" in loader_structural and "set_structural_level" in loader_structural, "structuralLevels parser contract drift")
    req("shrub_berry" in loader and "Some(ObjectKind::Bush)" in loader, "published shrub_berry family is not mapped to runtime Bush authority")
    req('"structuralLevels": structural_levels' in exporter, "worldgen exporter does not preserve structuralLevels")
    req("structural level mismatch for" in exporter, "worldgen exporter round-trip test does not certify structuralLevels")
    for token in ("--w56-visual-acceptance", "run_w56_integrated_visual_acceptance", INSTANCE_ID):
        req(token in entry, f"client W56 visual acceptance hook missing: {token}")
    req("visual-acceptance)" in build and "--w56-visual-acceptance" in build, "Build.sh W56 visual acceptance client launch missing")
    req("visual-acceptance-editor)" in build and "haven_editor_native.exe" in build, "Build.sh W56 native-editor acceptance launch missing")
    for token in ("W56_VISUAL_ACCEPTANCE_PACK_PATH", "W56_VISUAL_ACCEPTANCE_SCENE_ID", "--w56-visual-acceptance", "load_worldgen_pack_from_path"):
        req(token in editor, f"native editor W56 acceptance hook missing: {token}")
    req("CommandId='63'" in controls and "CommandId='64'" in controls, "compact Run menu does not expose both W56 parity launches")
    req("Id='63'" in registry and "visual-acceptance" in registry, "command registry missing W56 client acceptance")
    req("Id='64'" in registry and "visual-acceptance-editor" in registry, "command registry missing W56 editor acceptance")

    report = {
        "schema": "havenwild.w56_integrated_visual_acceptance.v1",
        "pass": "167Z109W56IJ3",
        "status": "PASS",
        "scene": SCENE_REL,
        "runtimePack": PACK_REL,
        "buildingInstanceId": INSTANCE_ID,
        "structuralLevels": present_levels,
        "objectCount": len(objects),
        "naturalObjectCount": len(natural_ids),
        "uniqueNaturalAssetCount": len(set(natural_ids)),
        "caveHostTiles": [1, 3],
        "caveApertureTiles": [1, 2],
        "editorRuntimeParity": "same isolated scene pack + direct client/editor launch + shared structural resolver + stable asset refs",
        "worldgenStructuralRoundTrip": "loader parses structuralLevels + exporter preserves structuralLevels",
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("PASS W56I/J integrated visual acceptance")
    print(f"- scene: {SCENE_REL}")
    print(f"- structural levels: {present_levels}")
    print(f"- objects: {len(objects)} ({len(natural_ids)} natural / {len(set(natural_ids))} exact natural assets)")
    print("- starter cottage: production recipe through diagnostic BuildingInstance")
    print("- cave source/aperture: 1x3 / 1x2")
except Exception as exc:
    print(f"FAIL W56I/J integrated visual acceptance: {exc}", file=sys.stderr)
    sys.exit(1)
