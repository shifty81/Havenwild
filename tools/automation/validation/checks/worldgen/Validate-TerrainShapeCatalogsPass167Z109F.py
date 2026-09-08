#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
WORLDGEN = ROOT / "content" / "worldgen"
V7_DIR = ROOT / "content" / "assets" / "lpc" / "source" / "lpc-terrains-v7"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def fail(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    grammar = load(WORLDGEN / "terrain_shape_grammar_v0_1.json")
    v7 = load(WORLDGEN / "v7_terrain_full_shape_catalog_v0_1.json")
    cliffs = load(WORLDGEN / "elizawy_cliff_sheet_role_catalog_v0_1.json")
    structural = load(WORLDGEN / "structural_cliff_autotile_authority_v0_1.json")

    corner_masks = [x["mask"] for x in grammar["cornerOccupancy15"]["nonEmptyMasks"]]
    edge_masks = [x["mask"] for x in grammar["cardinalEdge15"]["boundaryMasks"]]
    if corner_masks != list(range(1, 16)):
        fail("corner occupancy grammar does not contain masks 1..15 exactly")
    if edge_masks != list(range(1, 16)):
        fail("cardinal edge grammar does not contain masks 1..15 exactly")

    raw_root = ET.parse(V7_DIR / "terrain-v7.tsx").getroot()
    map_root = ET.parse(V7_DIR / "terrain-map-v7.tsx").getroot()
    if v7["geometry"]["rawAtlasTileCount"] != int(raw_root.attrib["tilecount"]):
        fail("V7 raw tile count drift")
    if len(v7["sourceCells"]) != int(raw_root.attrib["tilecount"]):
        fail("V7 source cell catalog is not exhaustive")
    if len(v7["terrainTypes"]) != 34:
        fail("V7 terrain type count must remain 34")
    if v7["geometry"]["generatedMapTerrainNodeCount"] != len(map_root.findall("tile")):
        fail("V7 generated tuple node count drift")
    if v7["geometry"]["generatedMapUniqueTupleCount"] != 15562:
        fail("V7 unique tuple count drift from upstream generated atlas")
    if not v7["completeness"]["mappingComplete"]:
        fail("V7 mapping is not marked complete")

    # The generated V7 map is deliberately binary-complete for supported pairs:
    # each pair has all 14 mixed occupancy patterns or is absent. This makes
    # missing direct contacts explicit instead of silently half-mapped.
    pair_summary = v7["directPairCoverageSummary"]
    if pair_summary["totalUnorderedPairs"] != 561:
        fail("V7 pair matrix must account for all C(34,2)=561 material pairs")
    for pair in v7["directPairCoverage"]:
        status = pair["status"]
        count = len(pair["firstMaterialMasksAvailable"])
        if status == "complete_14_mixed_patterns" and count != 14:
            fail(f"pair {pair['materials']} claims complete coverage with {count} masks")
        if status == "absent" and count != 0:
            fail(f"pair {pair['materials']} claims absent coverage but has masks")
        if status == "partial":
            fail(f"unexpected partial pair coverage for {pair['materials']}")

    # Grass_Light is intentionally only a pure-fill source family in the map;
    # every other terrain family has at least one complete shape set across its
    # authored pair relationships.
    by_name = {x["name"]: x for x in v7["terrainTypes"]}
    if by_name["Grass_Light"]["availableNonEmptyMaskCount"] != 1:
        fail("Grass_Light expected to remain a fill-only/sparse variant")
    for name, material in by_name.items():
        if name == "Grass_Light":
            continue
        if material["availableNonEmptyMaskCount"] != 15:
            fail(f"{name} does not expose all 15 occupancy patterns somewhere in V7")

    summary = cliffs["cellMappingSummary"]
    if summary["totalCells"] != 224 or summary["occupiedCells"] != 164 or summary["emptyCells"] != 60:
        fail("ElizaWy cliff sheet geometry count drift")
    if summary["occupiedUnmapped"] != 0 or not summary["allCellsAccountedFor"]:
        fail("ElizaWy cliff sheet contains occupied cells without assembly mapping")
    if not summary["seasonalCoordinateMapReusable"]:
        fail("ElizaWy seasonal alpha geometry parity lost")

    recipes = cliffs["structuralShapeRecipes"]
    if [x["mask"] for x in recipes] != list(range(1, 16)):
        fail("ElizaWy structural recipes do not cover masks 1..15 exactly")
    bits = [(1, "north"), (2, "east"), (4, "south"), (8, "west")]
    for recipe in recipes:
        expected = [name for bit, name in bits if recipe["mask"] & bit]
        if recipe["collision"]["blockedCardinalEdges"] != expected:
            fail(f"collision edge mapping drift for cliff mask {recipe['mask']}")
        south_rule = recipe["collision"]["southProjectedFaceFootprint"]
        if recipe["mask"] & 4:
            if not south_rule.startswith("3 rows"):
                fail(f"south face depth missing for cliff mask {recipe['mask']}")
        elif south_rule != "none":
            fail(f"non-south cliff mask {recipe['mask']} owns a projected south face")

    if not structural["mappingStatus"]["collisionSemanticsMapped"]:
        fail("structural cliff authority does not certify collision mapping")

    runtime = (ROOT / "crates" / "haven_game" / "src" / "runtime_surface_streaming.rs").read_text(encoding="utf-8")
    required_runtime_tokens = [
        "structural_cliff_face_occupies_tile",
        "structural_south_face_projection_depth",
        "structural_attachment_opens_edge",
        "structural_connector_from_host_edge_in_manifest",
    ]
    for token in required_runtime_tokens:
        if token not in runtime:
            fail(f"runtime structural collision token missing: {token}")

    print("Pass167Z109F terrain/cliff full shape catalog validation passed")
    print(f"  V7: {len(v7['sourceCells'])} raw cells, {v7['geometry']['generatedMapTerrainNodeCount']} tuple nodes, {pair_summary['completePairs']} complete direct pairs, {pair_summary['absentPairs']} explicit absent pairs")
    print(f"  ElizaWy: {summary['occupiedCells']} occupied + {summary['emptyCells']} empty cells accounted for, 15/15 structural masks mapped")


if __name__ == "__main__":
    main()
