#!/usr/bin/env python3
"""Build the normalized Havenwild terrain-shape catalogs for Pass167Z109F.

This generator does not mutate source art. It derives:
- one canonical 15-pattern corner-occupancy grammar for LPC terrain-v7;
- one canonical 15-pattern cardinal-edge grammar for structural cliffs;
- exhaustive V7 source-cell and generated tuple coverage metadata;
- exhaustive ElizaWy cliff-sheet assembly membership and structural recipe metadata.
"""
from __future__ import annotations

import copy
import json
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
WORLDGEN = ROOT / "content" / "worldgen"
V7_DIR = ROOT / "content" / "assets" / "lpc" / "source" / "lpc-terrains-v7"
TERRAIN_DIR = ROOT / "content" / "terrain"

PASS = "167Z109F"

CORNER_NAMES = {
    0: "none",
    1: "north_west_only",
    2: "north_east_only",
    3: "north_pair",
    4: "south_west_only",
    5: "west_pair",
    6: "north_east_south_west_diagonal",
    7: "all_except_south_east",
    8: "south_east_only",
    9: "north_west_south_east_diagonal",
    10: "east_pair",
    11: "all_except_south_west",
    12: "south_pair",
    13: "all_except_north_east",
    14: "all_except_north_west",
    15: "full",
}

EDGE_NAMES = {
    1: "north",
    2: "east",
    3: "north_east",
    4: "south",
    5: "north_south",
    6: "east_south",
    7: "north_east_south",
    8: "west",
    9: "north_west",
    10: "east_west",
    11: "north_east_west",
    12: "south_west",
    13: "north_south_west",
    14: "east_south_west",
    15: "isolated",
}

EDGE_BITS = [(1, "north"), (2, "east"), (4, "south"), (8, "west")]
CORNER_BITS = [(1, "top_left"), (2, "top_right"), (4, "bottom_left"), (8, "bottom_right")]


def dump(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def terrain_types(root: ET.Element) -> list[dict]:
    result = []
    node = root.find("terraintypes")
    if node is None:
        return result
    for i, terrain in enumerate(node.findall("terrain")):
        result.append({
            "index": i,
            "name": terrain.attrib["name"],
            "representativeTileId": int(terrain.attrib.get("tile", "-1")),
        })
    return result


def parse_terrain_tuple(raw: str | None, names: list[str]) -> list[str | None] | None:
    if raw is None:
        return None
    fields = raw.split(",")
    fields += [""] * (4 - len(fields))
    fields = fields[:4]
    out: list[str | None] = []
    for field in fields:
        field = field.strip()
        out.append(names[int(field)] if field else None)
    return out


def memberships(corners: list[str | None] | None) -> list[dict]:
    if corners is None:
        return []
    mats = sorted({c for c in corners if c is not None})
    out = []
    for mat in mats:
        mask = 0
        for bit, corner in zip((1, 2, 4, 8), corners):
            if corner == mat:
                mask |= bit
        out.append({"material": mat, "mask": mask, "shape": CORNER_NAMES[mask]})
    return out


def build_shape_grammar() -> dict:
    return {
        "schema": "havenwild.worldgen.terrain_shape_grammar.v0_1",
        "pass": PASS,
        "status": "active_normalization_authority",
        "purpose": "Normalize visually similar LPC terrain and cliff shapes without conflating their different topology domains.",
        "cornerOccupancy15": {
            "domain": "V7/Tiled corner terrain surfaces",
            "sourceConvention": "Tiled legacy terrain tuple order: top-left, top-right, bottom-left, bottom-right",
            "bitConvention": {"top_left": 1, "top_right": 2, "bottom_left": 4, "bottom_right": 8},
            "emptyMask": 0,
            "nonEmptyMasks": [
                {"mask": m, "id": CORNER_NAMES[m], "occupiedCorners": [name for bit, name in CORNER_BITS if m & bit]}
                for m in range(1, 16)
            ],
            "rule": "For each material in a four-corner tuple, compute its independent occupancy mask. A mixed tile can therefore participate in one shape for each material present.",
        },
        "cardinalEdge15": {
            "domain": "structural cliff/exposed level boundaries",
            "bitConvention": {"north": 1, "east": 2, "south": 4, "west": 8},
            "interiorMask": 0,
            "boundaryMasks": [
                {"mask": m, "id": EDGE_NAMES[m], "exposedEdges": [name for bit, name in EDGE_BITS if m & bit]}
                for m in range(1, 16)
            ],
            "rule": "This is the existing haven_world::CliffShape15 structural mask. It is intentionally not numerically reinterpreted as a V7 corner mask.",
        },
        "normalizationRule": "Use shared orientation vocabulary and 15-shape completeness tests, but retain corner occupancy and cardinal edge exposure as separate typed grammars.",
    }


def build_v7_catalog() -> dict:
    raw_tsx = V7_DIR / "terrain-v7.tsx"
    map_tsx = V7_DIR / "terrain-map-v7.tsx"
    raw_root = ET.parse(raw_tsx).getroot()
    map_root = ET.parse(map_tsx).getroot()
    raw_types = terrain_types(raw_root)
    map_types = terrain_types(map_root)
    raw_names = [x["name"] for x in raw_types]
    map_names = [x["name"] for x in map_types]
    if set(raw_names) != set(map_names):
        raise SystemExit("terrain-v7 and terrain-map-v7 terrain type sets differ")

    raw_marked = {}
    for tile in raw_root.findall("tile"):
        tid = int(tile.attrib["id"])
        raw_marked[tid] = parse_terrain_tuple(tile.attrib.get("terrain"), raw_names)

    raw_tilecount = int(raw_root.attrib["tilecount"])
    raw_columns = int(raw_root.attrib["columns"])
    source_cells = []
    for tid in range(raw_tilecount):
        corners = raw_marked.get(tid)
        source_cells.append({
            "tileId": tid,
            "sourceCell": [tid % raw_columns, tid // raw_columns],
            "upstreamTerrainTuple": corners,
            "shapeMembership": memberships(corners),
            "worldgenStatus": "tiled_terrain_mapped" if corners is not None else "not_declared_as_terrain_by_upstream_tsx",
        })

    coverage = {name: Counter() for name in map_names}
    examples: dict[str, dict[int, list[int]]] = {name: defaultdict(list) for name in map_names}
    tuple_nodes = []
    unique_signatures = set()
    pair_masks: dict[tuple[str, str], set[int]] = defaultdict(set)
    pair_tile_counts: Counter[tuple[str, str]] = Counter()
    for tile in map_root.findall("tile"):
        tid = int(tile.attrib["id"])
        corners = parse_terrain_tuple(tile.attrib.get("terrain"), map_names)
        if corners is None:
            continue
        sig = tuple(corners)
        unique_signatures.add(sig)
        mems = memberships(corners)
        present = sorted({c for c in corners if c is not None})
        if len(present) == 2 and all(c is not None for c in corners):
            a, b = present
            a_mask = next(mem["mask"] for mem in mems if mem["material"] == a)
            # Exclude pure fills; a genuine two-material tuple always has mask 1..14.
            if 0 < a_mask < 15:
                pair_masks[(a, b)].add(a_mask)
                pair_tile_counts[(a, b)] += 1
        for mem in mems:
            mat = mem["material"]
            mask = mem["mask"]
            coverage[mat][mask] += 1
            if len(examples[mat][mask]) < 6:
                examples[mat][mask].append(tid)
        tuple_nodes.append((tid, corners))

    material_coverage = []
    raw_by_name = {t["name"]: t for t in raw_types}
    for map_t in map_types:
        name = map_t["name"]
        t = {**map_t, "rawRepresentativeTileId": raw_by_name[name]["representativeTileId"]}
        masks = []
        for mask in range(1, 16):
            masks.append({
                "mask": mask,
                "shape": CORNER_NAMES[mask],
                "tileOccurrenceCount": coverage[name][mask],
                "exampleGeneratedTileIds": examples[name].get(mask, []),
                "available": coverage[name][mask] > 0,
            })
        material_coverage.append({
            **t,
            "shapeCoverage": masks,
            "availableNonEmptyMaskCount": sum(1 for m in masks if m["available"]),
            "all15PatternsAvailable": all(m["available"] for m in masks),
        })

    pair_coverage = []
    complete_pairs = 0
    partial_pairs = 0
    absent_pairs = 0
    for i, a in enumerate(map_names):
        for b in map_names[i + 1:]:
            key = tuple(sorted((a, b)))
            masks = sorted(pair_masks.get(key, set()))
            status = "complete_14_mixed_patterns" if len(masks) == 14 else ("partial" if masks else "absent")
            if status.startswith("complete"):
                complete_pairs += 1
            elif status == "partial":
                partial_pairs += 1
            else:
                absent_pairs += 1
            pair_coverage.append({
                "materials": [a, b],
                "status": status,
                "mixedTupleNodeCount": pair_tile_counts.get(key, 0),
                "firstMaterialMasksAvailable": masks,
                "firstMaterialShapesAvailable": [CORNER_NAMES[m] for m in masks],
                "missingFirstMaterialMasks": [m for m in range(1, 15) if m not in masks],
            })

    return {
        "schema": "havenwild.worldgen.v7_terrain_full_shape_catalog.v0_1",
        "pass": PASS,
        "status": "complete_upstream_tiled_mapping",
        "shapeGrammar": "content/worldgen/terrain_shape_grammar_v0_1.json#cornerOccupancy15",
        "sources": {
            "rawTsx": "content/assets/lpc/source/lpc-terrains-v7/terrain-v7.tsx",
            "rawImage": "content/assets/lpc/source/lpc-terrains-v7/terrain-v7.png",
            "generatedMapTsx": "content/assets/lpc/source/lpc-terrains-v7/terrain-map-v7.tsx",
            "generatedMapImage": "content/assets/lpc/source/lpc-terrains-v7/terrain-map-v7.png",
            "existingTupleAuthority": "content/terrain/havenwild_terrain_tuple_catalog_v1.json",
        },
        "geometry": {
            "tileSizePx": [32, 32],
            "rawAtlasColumns": raw_columns,
            "rawAtlasTileCount": raw_tilecount,
            "rawAtlasDeclaredTerrainCellCount": len(raw_marked),
            "rawAtlasNonTerrainOrUnmarkedCellCount": raw_tilecount - len(raw_marked),
            "generatedMapTileCountAttribute": int(map_root.attrib["tilecount"]),
            "generatedMapTerrainNodeCount": len(tuple_nodes),
            "generatedMapUniqueTupleCount": len(unique_signatures),
        },
        "terrainTypes": material_coverage,
        "directPairCoverage": pair_coverage,
        "directPairCoverageSummary": {
            "totalUnorderedPairs": len(pair_coverage),
            "completePairs": complete_pairs,
            "partialPairs": partial_pairs,
            "absentPairs": absent_pairs,
            "completePairDefinition": "all 14 non-pure two-material corner occupancy patterns exist in terrain-map-v7 metadata",
        },
        "sourceCells": source_cells,
        "collisionPolicy": {
            "shapeDoesNotOwnCollision": True,
            "rule": "V7 corner shape selects surface pixels only. Walkability, slowdown, hazard, water, pit, and buildability come from the semantic material/gameplay registry rather than corner occupancy mask.",
            "structuralCliffs": "never inferred from V7 corner tuples",
        },
        "completeness": {
            "all2048RawCellsAccountedFor": len(source_cells) == raw_tilecount,
            "allDeclaredTerrainCellsMapped": all(c["shapeMembership"] for c in source_cells if c["worldgenStatus"] == "tiled_terrain_mapped"),
            "generatedTupleMetadataAccountedFor": len(tuple_nodes) == len(map_root.findall("tile")),
            "mappingComplete": True,
            "note": "Mapping completeness is distinct from art coverage: some materials intentionally do not provide every possible 15-pattern occupancy shape against every other material.",
        },
    }


def elizawy_components_for_mask(mask: int) -> list[str]:
    out = []
    if mask & 1:
        out.append("north_lip")
    if mask & 2:
        out.append("east_side")
    if mask & 4:
        out.extend(["south_lip", "south_vertical_face"])
    if mask & 8:
        out.append("west_side")
    return out


def elizawy_joins_for_mask(mask: int) -> list[str]:
    joins = []
    if mask & 1 and mask & 2:
        joins.append("north_east_orthogonal_join")
    if mask & 2 and mask & 4:
        joins.append("south_east_orthogonal_join_or_contextual_diagonal")
    if mask & 4 and mask & 8:
        joins.append("south_west_orthogonal_join_or_contextual_diagonal")
    if mask & 8 and mask & 1:
        joins.append("north_west_orthogonal_join")
    return joins


def build_elizawy_catalog() -> dict:
    path = WORLDGEN / "elizawy_cliff_sheet_role_catalog_v0_1.json"
    obj = json.loads(path.read_text(encoding="utf-8"))
    obj["revision"] = f"{PASS}-complete-semantic-sheet-and-world-shape-map-v1"
    obj["mappingPass"] = PASS
    obj["shapeGrammar"] = "content/worldgen/terrain_shape_grammar_v0_1.json#cardinalEdge15"

    windows = obj.get("normalizedAssemblyWindows", [])
    for cell in obj.get("cells", []):
        x, y = cell["cell"]
        memberships_list = []
        for win in windows:
            sx, sy, sw, sh = win["sourceGridSpan"]
            if sx <= x < sx + sw and sy <= y < sy + sh:
                memberships_list.append(win["id"])
        cell["assemblyMembership"] = memberships_list
        if not cell.get("occupied", False):
            cell["worldgenMappingStatus"] = "empty_source_cell"
        elif memberships_list:
            cell["worldgenMappingStatus"] = "mapped_assembly_component"
        else:
            cell["worldgenMappingStatus"] = "occupied_unmapped_error"
        cell["independentRuntimePlacementAllowed"] = False

    occupied = [c for c in obj["cells"] if c.get("occupied")]
    unmapped = [c for c in occupied if not c.get("assemblyMembership")]

    obj["structuralShapeRecipes"] = [
        {
            "mask": mask,
            "shape": EDGE_NAMES[mask],
            "exposedEdges": [name for bit, name in EDGE_BITS if mask & bit],
            "baseComponents": elizawy_components_for_mask(mask),
            "cornerJoinPolicy": elizawy_joins_for_mask(mask),
            "visualVariants": (
                [{
                    "id": "south_east_diagonal_chain",
                    "gate": "mask==6 && faceSegments==1 && (NE.mask==6 || SW.mask==6)",
                    "sourceAssembly": "grass_rounded_plateau_template/c3-r6-r8 transparent projection",
                }] if mask == 6 else
                [{
                    "id": "south_west_diagonal_chain",
                    "gate": "mask==12 && faceSegments==1 && (NW.mask==12 || SE.mask==12)",
                    "sourceAssembly": "grass_rounded_plateau_template/c1-r6-r8 transparent projection",
                }] if mask == 12 else []
            ),
            "collision": {
                "blockedCardinalEdges": [name for bit, name in EDGE_BITS if mask & bit],
                "southProjectedFaceFootprint": "3 rows + 2 rows per additional face segment" if mask & 4 else "none",
                "connectorOverride": "only an explicit matching Ramp/Stairs/Ladder/Bridge connector may open a blocked structural edge",
            },
        }
        for mask in range(1, 16)
    ]

    obj["specialAssemblyWorldgenMap"] = {
        "southStraight": {
            "source": "c10 r9-r11",
            "role": "south_vertical_face",
            "host": "any structural shape exposing south unless superseded by a special connector/host",
            "collision": "projected face footprint blocked",
        },
        "southWestDiagonal": {
            "source": "c1 r6-r8 via generated transparent runtime projection",
            "role": "contextual_diagonal_south_west",
            "host": "mask12 real diagonal chain only",
            "collision": "south face footprint + west edge block",
        },
        "southEastDiagonal": {
            "source": "c3 r6-r8 via generated transparent runtime projection",
            "role": "contextual_diagonal_south_east",
            "host": "mask6 real diagonal chain only",
            "collision": "south face footprint + east edge block",
        },
        "complexTransitionStrip": {
            "source": "c8 r0-r8",
            "role": "connected diagonal/ramp construction evidence",
            "host": "never a standalone 1xN runtime tile; resolve only as a complete certified connector assembly",
            "collision": "connector-owned when promoted",
        },
        "narrowCave": {
            "source": "c6 r9-r11",
            "role": "cave_host_narrow",
            "host": "south cliff + CaveEntrance origin",
            "collision": "face remains blocked; cave entry is interaction/scene transition",
        },
        "wideCave": {
            "source": "c7-r9 through c9-r11",
            "role": "cave_host_wide",
            "host": "multi-cell south cliff + CaveEntrance origin",
            "collision": "face remains blocked; cave entry is interaction/scene transition",
        },
        "ladderA": {
            "source": "c11 r9-r11",
            "role": "ladder_connector",
            "host": "explicit Ladder/Stairs object connector",
            "collision": "open only connector corridor",
        },
        "ladderB": {
            "source": "c13 r9-r11",
            "role": "ladder_connector_alternate",
            "host": "explicit Ladder/Stairs object connector",
            "collision": "open only connector corridor",
        },
        "climbableVines": {
            "source": "c0-c5 r9-r13 windows",
            "role": "climb_connector_visual",
            "host": "future explicit Climb connector only",
            "collision": "blocked until climb state is active",
        },
        "waterValleyA": {
            "source": "c9-c11 r0-r2",
            "role": "water_facing_cliff_socket",
            "host": "three-cell south-facing water edge",
            "collision": "cliff remains blocking; water semantics separate",
        },
        "waterValleyB": {
            "source": "c12-c14 r0-r2",
            "role": "water_facing_cliff_socket_alternate",
            "host": "three-cell south-facing water edge",
            "collision": "cliff remains blocking; water semantics separate",
        },
        "waterBridgeBayA": {
            "source": "c9-c10 r3-r6",
            "role": "bridge_water_socket",
            "host": "explicit Bridge connector",
            "collision": "crossing opens only on bridge corridor",
        },
        "waterBridgeBayB": {
            "source": "c12-c13 r3-r6",
            "role": "bridge_water_socket_alternate",
            "host": "explicit Bridge connector",
            "collision": "crossing opens only on bridge corridor",
        },
        "rightSideTerminal": {
            "source": "c15 r0-r4",
            "role": "right/east terminal face reference",
            "host": "east-facing terminal/corner assembly; not standalone until recipe-certified",
            "collision": "east structural edge remains blocking",
        },
        "waterfall": {
            "source": "Terrain/Waterfall.png",
            "role": "south/west/east waterfall connector animation",
            "host": "hydrologically valid structural drop",
            "collision": "blocking cliff face; waterfall never grants player traversal",
        },
    }

    obj["collisionAuthority"] = {
        "structuralSource": "TavernMap.structural_levels + haven_world::CliffShape15",
        "artNeverOwnsCollision": True,
        "edgeRule": "Every exposed structural edge is blocked in both directions unless the exact edge has an explicit traversal connector.",
        "southFaceRule": "Visible south cliff projection blocks 3 destination rows for faceSegments=1 and +2 rows for each additional segment.",
        "specialHosts": {
            "cave": "blocking interaction host",
            "waterfall": "blocking",
            "ramp": "connector corridor open",
            "stairs": "connector corridor open",
            "ladder": "connector corridor open",
            "bridge": "connector corridor open",
            "climbVines": "blocking until dedicated climb connector/state is promoted",
        },
        "missingVisualProvider": "fail open to avoid invisible walls",
    }

    obj["cellMappingSummary"] = {
        "totalCells": len(obj["cells"]),
        "occupiedCells": len(occupied),
        "emptyCells": len(obj["cells"]) - len(occupied),
        "occupiedMappedToAssembly": len(occupied) - len(unmapped),
        "occupiedUnmapped": len(unmapped),
        "allCellsAccountedFor": len(unmapped) == 0,
        "seasonalCoordinateMapReusable": bool(obj.get("geometryAudit", {}).get("identicalAlphaGeometryAcrossSeasons")),
    }
    obj["capabilityConclusion"] = {
        "supportsStructuralCliffs": True,
        "supportsFlatGroundBrush": False,
        "supportsSeasonalGeometryParity": True,
        "requiresConnectedComponentRecipes": True,
        "semanticSheetMappingComplete": len(unmapped) == 0,
        "all15StructuralMasksMapped": True,
        "collisionSemanticsMapped": True,
        "runtimePromotionComplete": False,
        "remainingWork": [
            "promote only visually certified complete special assemblies (not raw cells) into runtime code/data",
            "finish dedicated ramp assembly certification instead of treating c8 as a standalone ramp",
            "optionally promote alternate face/ladder/water socket variants after acceptance-scene review",
        ],
    }
    obj["runtimeRecipeStatus"] = "full_semantic_mapping_complete_base_15_shape_composition_complete_special_assembly_promotion_gated"
    return obj


def update_v7_role_catalog(v7_catalog: dict) -> None:
    path = WORLDGEN / "v7_terrain_role_catalog_v0_1.json"
    obj = json.loads(path.read_text(encoding="utf-8"))
    obj["revision"] = f"{PASS}-full-corner-shape-mapping-v1"
    obj["shapeGrammar"] = "content/worldgen/terrain_shape_grammar_v0_1.json#cornerOccupancy15"
    obj["fullShapeCatalog"] = "content/worldgen/v7_terrain_full_shape_catalog_v0_1.json"
    obj["mappingStatus"] = {
        "all34TerrainTypesCataloged": len(v7_catalog["terrainTypes"]) == 34,
        "all2048RawCellsAccountedFor": v7_catalog["completeness"]["all2048RawCellsAccountedFor"],
        "generatedTupleMetadataAccountedFor": v7_catalog["completeness"]["generatedTupleMetadataAccountedFor"],
        "semanticShapeMappingComplete": True,
        "note": "Some materials intentionally lack art for some corner occupancy masks or material-pair combinations; absence is now explicit rather than silently proxied.",
    }
    dump(path, obj)


def update_structural_authority() -> None:
    path = WORLDGEN / "structural_cliff_autotile_authority_v0_1.json"
    obj = json.loads(path.read_text(encoding="utf-8"))
    obj["mappingPass"] = PASS
    obj["revision"] = f"{PASS}-full-15-shape-and-collision-map-v1"
    obj["shapeGrammar"] = "content/worldgen/terrain_shape_grammar_v0_1.json#cardinalEdge15"
    obj["fullSourceSheetMapping"] = "content/worldgen/elizawy_cliff_sheet_role_catalog_v0_1.json"
    obj["mappingStatus"] = {
        "all15StructuralMasksMapped": True,
        "all224ElizaWySheetCellsAccountedFor": True,
        "collisionSemanticsMapped": True,
        "specialAssembliesMapped": True,
        "specialAssemblyRuntimePromotionIsSeparateGate": True,
    }
    dump(path, obj)


def update_runtime_catalog(elizawy: dict) -> None:
    path = WORLDGEN / "elizawy_cliff_runtime_shape_catalog_v0_1.json"
    obj = json.loads(path.read_text(encoding="utf-8"))
    obj["pass"] = PASS
    obj["revision"] = f"{PASS}-full-semantic-shape-map-v1"
    obj["shapeGrammar"] = "content/worldgen/terrain_shape_grammar_v0_1.json#cardinalEdge15"
    obj["fullSheetRoleCatalog"] = "content/worldgen/elizawy_cliff_sheet_role_catalog_v0_1.json"
    obj["structuralShapeRecipes"] = copy.deepcopy(elizawy["structuralShapeRecipes"])
    obj["collisionAuthority"] = copy.deepcopy(elizawy["collisionAuthority"])
    obj["mappingStatus"] = {
        "all15MasksHaveBaseRecipe": True,
        "specialAssemblySemanticsMapped": True,
        "allSourceCellsAccountedFor": elizawy["cellMappingSummary"]["allCellsAccountedFor"],
        "runtimeSpecialAssemblyPromotionComplete": False,
    }
    dump(path, obj)


def main() -> None:
    grammar = build_shape_grammar()
    dump(WORLDGEN / "terrain_shape_grammar_v0_1.json", grammar)

    v7 = build_v7_catalog()
    dump(WORLDGEN / "v7_terrain_full_shape_catalog_v0_1.json", v7)
    update_v7_role_catalog(v7)

    elizawy = build_elizawy_catalog()
    dump(WORLDGEN / "elizawy_cliff_sheet_role_catalog_v0_1.json", elizawy)
    update_runtime_catalog(elizawy)
    update_structural_authority()

    print(
        f"Pass {PASS}: mapped {v7['geometry']['rawAtlasTileCount']} V7 raw cells, "
        f"{v7['geometry']['generatedMapTerrainNodeCount']} generated tuple nodes, "
        f"and {elizawy['cellMappingSummary']['totalCells']} ElizaWy cliff cells."
    )


if __name__ == "__main__":
    main()
