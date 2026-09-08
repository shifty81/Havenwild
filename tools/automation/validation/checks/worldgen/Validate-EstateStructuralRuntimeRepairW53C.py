#!/usr/bin/env python3
from pathlib import Path
import json, sys

ROOT = Path(__file__).resolve().parents[5]

def load(rel):
    p = ROOT / rel
    if not p.is_file():
        raise AssertionError(f"missing {rel}")
    return json.loads(p.read_text(encoding="utf-8"))

def text(rel):
    p = ROOT / rel
    if not p.is_file():
        raise AssertionError(f"missing {rel}")
    return p.read_text(encoding="utf-8")

def req(ok, message):
    if not ok:
        raise AssertionError(message)

try:
    scene = load("content/worldgen/scenes/home_island/farmstead_scene_v0_3.json")
    profile = load("content/estates/estate_generation_profile_v1.json")
    cave = load("content/caves/cave_asset_authority_v1.json")
    connectors = load("content/connectors/structural_connector_catalog_v1.json")
    instance_catalog = load("content/buildings/building_instance_catalog_v1.json")
    loader = text("crates/haven_core/src/worldgen_loader.rs")
    structural_loader = text("crates/haven_core/src/worldgen_loader_structural.rs")
    interior = text("crates/haven_assets/src/building_instance/interior.rs")
    object_draw = text("crates/haven_game/src/runtime_object_draw.rs")
    runtime_draw = text("crates/haven_game/src/runtime_draw.rs")
    generator = text("tools/automation/worldgen/Build-HomeEstateSceneW53.py")

    levels = scene.get("layers", {}).get("structuralLevels")
    terrain = scene.get("layers", {}).get("terrain")
    width, height = scene["sceneSize"]
    req(isinstance(levels, list) and len(levels) == height, "Estate structuralLevels missing or wrong height")
    req(all(isinstance(row, list) and len(row) == width for row in levels), "Estate structuralLevels width mismatch")
    req({cell for row in levels for cell in row}.issubset({0, 1, 2}), "Estate structuralLevels contains non-discrete levels")
    req(max(cell for row in levels for cell in row) == 2, "Estate never reaches structural Level 2")
    req(not any(tile == "Cliff" for row in terrain for tile in row), "Estate still paints raw Cliff terrain instead of deriving cliff faces")

    # Raised border: Level 2. Fixed south gate: Level 0.
    req(all(levels[0][x] == 2 for x in range(width)), "north Estate highland is not Level 2")
    req(all(levels[y][0] == 2 for y in range(height)), "west Estate highland is not Level 2")
    req(all(levels[y][width - 1] == 2 for y in range(height)), "east Estate highland is not Level 2")
    for y in range(60, 64):
        for x in range(46, 51):
            req(levels[y][x] == 0, f"south Estate gate remains raised at {(x, y)}")

    # Cave: one wide, two-high aperture; third source row is the threshold envelope.
    req(levels[8][78] == 2, "Estate cave host must be structural Level 2")
    req(levels[9][78] == 0, "Estate cave approach must be structural Level 0")
    cave_profile = profile["caveMouth"]
    req(cave_profile.get("tile") == [78, 8], "cave host tile drifted")
    req(cave_profile.get("thresholdTile", [78, 9]) == [78, 9], "cave threshold must remain one row below the host")
    req(cave_profile.get("interactionTile") in ([78, 9], [78, 10]), "cave interaction must remain on the threshold/clear approach lineage")
    if profile.get("pass") in {"167Z109W54F", "167Z109W57K8"}:
        req(cave_profile.get("interactionTile") == [78, 10], "W54F cave interaction must occur from the clear walkable approach tile")
    req(cave_profile.get("apertureTiles") == [1, 2], "ordinary cave aperture must be 1x2")
    req(cave_profile.get("sourceEnvelopeTiles") == [1, 3], "exact cave source envelope must remain 1x3")
    mouth = cave["entrances"]["ordinaryNarrowMouth"]
    req(mouth.get("sourceRect") == [192, 288, 32, 96], "exact narrow cave source rect changed")
    req(mouth.get("apertureTiles") == [1, 2], "cave authority aperture must be 1x2")
    req(mouth.get("thresholdTiles") == [1, 1], "cave threshold row must remain explicit")
    req(mouth.get("visualEnvelopeTiles") == [1, 3], "cave visual envelope must stay 1x3")
    cprof = next(p for p in connectors["profiles"] if p["id"] == "cave.narrow_mouth")
    req(cprof.get("apertureTiles") == [1, 2] and cprof.get("sourceEnvelopeTiles") == [1, 3], "connector cave aperture/envelope metadata drifted")

    cave_obj = next(o for o in scene["objects"] if o["id"] == "estate_cave_mouth")
    req(cave_obj["visualRect"] == [78, 6, 1, 3], "cave exact source envelope placement drifted")
    req(cave_obj["interactions"][0]["rect"] in ([78, 9, 1, 1], [78, 10, 1, 1]), "cave interaction must remain on lower threshold/clear approach lineage")
    if profile.get("pass") in {"167Z109W54F", "167Z109W57K8"}:
        req(cave_obj["interactions"][0]["rect"] == [78, 10, 1, 1], "W54F cave object interaction must use clear approach")
    cave_transition = next(t for t in scene["transitions"] if t["id"] == "to_cave_mouth")
    req(cave_transition["rect"] in ([78, 9, 1, 1], [78, 10, 1, 1]), "cave scene transition must trigger from walkable threshold/approach")
    if profile.get("pass") in {"167Z109W54F", "167Z109W57K8"}:
        req(cave_transition["rect"] == [78, 10, 1, 1], "W54F cave transition must trigger from clear approach")

    req("parse_structural_levels(" in loader and 'include!("worldgen_loader_structural.rs")' in loader, "worldgen loader does not route authored structuralLevels through focused parser")
    req('layers.get("structuralLevels")' in structural_loader, "authored structuralLevels parser is missing")
    req("MAX_STRUCTURAL_LEVEL" in loader and "set_structural_level" in structural_loader, "worldgen structural level bounds/storage missing")
    req("BuildingOpeningKind::Door | BuildingOpeningKind::Archway" in interior, "BuildingInstance doorway threshold escape repair missing")
    req("return true;" in interior, "doorway threshold is not explicitly navigable")
    req("consumed_by_structural_cliff" in object_draw and "scene.kind == SceneKind::Exterior" in object_draw, "cave structural visual ownership repair missing")
    req(("DEV — W53C Estate Visual Test" in runtime_draw) or ("DEV — W54B Estate Visual Test" in runtime_draw) or ("DEV — W54D2 Estate Visual Test" in runtime_draw) or ("DEV — W54E Estate Visual Test" in runtime_draw) or ("DEV — W54F Estate Visual Test" in runtime_draw) or ("DEV — W54G Estate Visual Test" in runtime_draw), "W53C-or-later isolated visual-test badge missing")
    req("structuralLevels" in generator and ("levels[y][x]=2" in generator or "levels[y][x] = 2" in generator), "Estate generator does not author Level-2 highlands")
    req("'Cliff'" not in generator, "Estate generator still paints raw Cliff terrain")

    # W53C rejected the old partial gable shell. Later passes may restore the cottage only
    # through a new explicit exterior contract; they may not silently reactivate that shell.
    cottage = next(e for e in instance_catalog["entries"] if e["id"] == "havenwild.estate.dev.starter_cottage")
    if cottage.get("status") == "deprecated":
        req(profile["starterCottage"].get("productionPolicy") == "deferred_until_complete_exterior_certified", "deprecated cottage must remain fail closed")
    else:
        req(cottage.get("status") == "candidate", "forward cottage status must be candidate or deprecated")
        req((ROOT / "content/buildings/exterior_grammar_contract_v1.json").is_file(), "reactivated cottage requires W54A exterior grammar contract")
        req(profile["starterCottage"].get("productionPolicy") == "development_fixture_or_progression_unlock", "reactivated cottage must remain optional/development progression content")

    print("PASS W53C Estate structural/runtime visual repair")
    print("- authored Estate now persists explicit structural Level 0/2 topology; raw Cliff paint is gone")
    print("- ordinary cave opening is 1 wide x 2 tall, with exact 1x3 source envelope including threshold")
    print("- cave interaction/transition happens from the walkable threshold/approach lane, never inside the cliff host")
    print("- structural cliff renderer owns the cave visual; PublishedWorldAsset object draw no longer double-renders it")
    print("- BuildingInstance doors/archways are navigable thresholds, preventing interior exit traps")
    print("- rejected W53B gable shell remains forbidden; later cottage restoration requires explicit exterior grammar authority")
except Exception as exc:
    print(f"FAIL W53C Estate structural/runtime visual repair: {exc}", file=sys.stderr)
    sys.exit(1)
