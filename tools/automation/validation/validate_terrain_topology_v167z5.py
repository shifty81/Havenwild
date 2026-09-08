#!/usr/bin/env python3
"""Validate generated terrain topology, acceptance coverage, and render ownership."""
from __future__ import annotations

from collections import Counter
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CONTRACT_PATH = ROOT / "content/worldgen/terrain_topology_contract_v0_2.json"
CLIENT_SCENE = ROOT / "content/worldgen/scenes/open_world/willowmere_outskirts_region_v0_1.json"
ACCEPTANCE_MANIFEST = ROOT / "content/worldgen/scenes/terrain_acceptance/terrain_acceptance_scene_manifest_v1.json"
METRICS_PATH = ROOT / "docs/audits/generated/havenwild_open_world_biome_v167z38_metrics.json"
LPC_REPORT = ROOT / "docs/audits/generated/havenwild_terrain_lpc_certification_report_v167z5a.json"
TEST_PACK = ROOT / "content/worldgen/packs/worldgen_open_world_test_v0_12.json"

WATER = {"ShallowWater", "Water", "DeepWater", "OceanShallow", "OceanDeep", "RiverWater"}


def load(path: Path):
    if not path.is_file():
        raise FileNotFoundError(path.relative_to(ROOT))
    return json.loads(path.read_text(encoding="utf-8"))


def neighbors(x: int, y: int, width: int, height: int, eight_way: bool):
    offsets = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    if eight_way:
        offsets += [(-1, -1), (1, -1), (-1, 1), (1, 1)]
    for dx, dy in offsets:
        nx, ny = x + dx, y + dy
        if 0 <= nx < width and 0 <= ny < height:
            yield nx, ny


def validate_scene(scene: dict, contract: dict, allow_compatibility: bool = False) -> dict:
    width, height = scene["sceneSize"]
    terrain = scene.get("layers", {}).get("terrain", [])
    if len(terrain) != height or any(len(row) != width for row in terrain):
        raise ValueError(f"{scene.get('sceneId')} has invalid terrain dimensions")
    flat = [tile for row in terrain for tile in row]
    compatibility = set(contract["generated_semantic_policy"]["compatibility_only_tiles"])
    if not allow_compatibility and compatibility & set(flat):
        raise ValueError(
            f"{scene.get('sceneId')} contains compatibility-only semantic terrain: "
            f"{sorted(compatibility & set(flat))}"
        )

    if allow_compatibility:
        return dict(Counter(flat))

    violations: list[str] = []
    for rule in contract["adjacency_rules"]:
        mode8 = rule["neighbor_mode"] == "8-way"
        for y, row in enumerate(terrain):
            for x, tile in enumerate(row):
                if tile != rule["tile"]:
                    continue
                values = {terrain[ny][nx] for nx, ny in neighbors(x, y, width, height, mode8)}
                allowed = set(rule.get("allowed_neighbors", []))
                required = set(rule.get("required_any", []))
                if allowed and any(value not in allowed for value in values):
                    violations.append(f"{rule['id']}@{x},{y}:{sorted(values - allowed)}")
                if required and not (values & required):
                    violations.append(f"{rule['id']}@{x},{y}:missing-{sorted(required)}")
    if violations:
        raise ValueError(
            f"{scene.get('sceneId')} terrain topology failed: " + "; ".join(violations[:16])
        )
    return dict(Counter(flat))


def validate_acceptance(contract: dict) -> None:
    manifest = load(ACCEPTANCE_MANIFEST)
    if manifest.get("version") != 5:
        raise ValueError("terrain acceptance manifest must be version 5 with exact-V7/workbench evidence")
    ids = {entry["id"] for entry in manifest.get("scenes", [])}
    required = {
        "coastline", "river", "pond_bridge", "farm_soil", "mountain",
        "junctions", "snow_ice", "wrapped_world_seam", "terrain_gallery",
    }
    if ids != required:
        raise ValueError(f"terrain acceptance coverage changed: {sorted(ids)}")
    gallery_tiles: set[str] = set()
    for entry in manifest["scenes"]:
        scene = load(ROOT / entry["path"])
        allow_compatibility = entry["id"] == "terrain_gallery"
        validate_scene(scene, contract, allow_compatibility=allow_compatibility)
        if entry["id"] == "terrain_gallery":
            gallery_tiles = {tile for row in scene["layers"]["terrain"] for tile in row}
    expected_gallery = set(manifest.get("mappedTerrainSemantics", []))
    if gallery_tiles != expected_gallery:
        raise ValueError("terrain gallery does not cover every mapped terrain semantic")
    excluded = set(manifest.get("excludedPresentationSemantics", []))
    if not {"WoodFloor", "Wall", "Crop", "GreenhouseZone"}.issubset(excluded):
        raise ValueError("non-terrain presentation semantics are not explicitly separated")
    if manifest.get("semanticTopologyOnly") is not True:
        raise ValueError("semantic topology evidence must be explicitly labeled as non-game art")
    evidence = manifest.get("evidencePolicy", {})
    if evidence.get("semanticTopologyIsGameArt") is not False:
        raise ValueError("semantic topology maps are incorrectly presented as game art")
    if evidence.get("lpcMappedEvidenceUsesAtlasPixelsOnly") is not True:
        raise ValueError("LPC evidence does not require reviewed source pixels")
    if evidence.get("renderContract") != "exact_v7_presentation_authority_w77":
        raise ValueError("terrain evidence is not using the W77 exact-V7 presentation contract")
    if evidence.get("unresolvedTransitionCellsAreWorkbenchCandidates") is not True:
        raise ValueError("terrain evidence does not route unresolved contacts to the workbench")
    workbench = ROOT / evidence.get("workbench", "")
    if not workbench.is_file():
        raise FileNotFoundError("terrain evidence workbench manifest is missing")
    for entry in manifest["scenes"]:
        for key in ("semanticTopologyPreview", "lpcMappedPreview", "comparisonPreview"):
            preview = ROOT / entry.get(key, "")
            if not preview.is_file():
                raise FileNotFoundError(f"missing terrain evidence {key}: {preview}")

    test_pack = load(TEST_PACK)
    acceptance_paths = {entry["path"] for entry in manifest["scenes"]}
    pack_paths = set(test_pack.get("sceneFiles", []))
    if not acceptance_paths.issubset(pack_paths):
        raise ValueError("client test pack does not load every terrain acceptance scene")
    if test_pack.get("testWorld", {}).get("developerNavigation") != "F3 then PageUp/PageDown":
        raise ValueError("client test pack does not expose developer scene navigation")



def validate_lpc_evidence() -> None:
    report = load(LPC_REPORT)
    if report.get("schema") != "havenwild.terrain_lpc_certification_report.v167z27":
        raise ValueError("unexpected exact-V7 terrain certification report schema")
    if report.get("renderContract") != "exact_v7_presentation_authority_w77":
        raise ValueError("terrain certification report is not using W77 presentation authority")
    counts = report.get("aggregateCounts", {})
    if report.get("missingBindings"):
        raise ValueError(f"LPC terrain evidence has missing bindings: {report['missingBindings']}")
    if counts.get("missing_binding_cells", 0) != 0 or counts.get("transparent_source_cells", 0) != 0:
        raise ValueError("exact-V7 terrain evidence has missing/transparent source cells")
    unresolved = counts.get("unresolved_transition_cells", 0)
    rules = report.get("certificationRules", {})
    if unresolved and rules.get("unresolvedTransitionCellsAreWorkbenchCandidates") is not True:
        raise ValueError("unresolved terrain contacts are not explicitly routed to the workbench")
    if unresolved and rules.get("workbenchRequiredForUnresolvedContacts") is not True:
        raise ValueError("unresolved terrain contacts do not require hand-author workbench coverage")
    outputs = report.get("outputs", {})
    for key, relative in outputs.items():
        path = ROOT / relative
        if not path.is_file():
            raise FileNotFoundError(f"missing LPC terrain evidence output {key}: {relative}")
        if path.suffix.lower() == ".png":
            from PIL import Image
            with Image.open(path) as image:
                if image.width <= 0 or image.height <= 0:
                    raise ValueError(f"empty LPC terrain evidence image: {relative}")
    client = next((scene for scene in report.get("scenes", []) if scene.get("sceneId") == "client_test_world"), None)
    if client is None:
        raise ValueError("LPC terrain evidence does not include the client test world")
    client_counts = client.get("counts", {})
    if client_counts.get("rendered_cells", 0) <= 0:
        raise ValueError("client exact-V7 evidence rendered no terrain cells")
    atlas = load(ROOT / report["transitionManifest"])
    coverage = atlas.get("coverage", {})
    if coverage.get("mappedSourceMaterials") != 15:
        raise ValueError("exact-V7 atlas material coverage changed")
    if coverage.get("completeTwoMaterialPairs") != 48:
        raise ValueError("exact-V7 atlas complete-pair coverage changed")
    if coverage.get("twoMaterialPairShapeTarget") != 14:
        raise ValueError("exact-V7 atlas mixed-shape target changed")

def validate_runtime_ownership(contract: dict) -> None:
    terrain_pass = (ROOT / "crates/haven_game/src/runtime_terrain_pass.rs").read_text(encoding="utf-8")
    main = (ROOT / "crates/haven_game/src/main.rs").read_text(encoding="utf-8")
    runtime_config = (ROOT / "crates/haven_game/src/runtime_config.rs").read_text(encoding="utf-8")
    required_tokens = (
        "VisibleTerrainPlanCache",
        "water_spans",
        "base_indices",
        "transition_indices",
        "emergency no-atlas fallback",
        "if self.dev_mode {",
    )
    missing = [token for token in required_tokens if token not in terrain_pass]
    if missing:
        raise ValueError(f"terrain frame-plan runtime is incomplete: {missing}")
    if "visible_terrain_plan" not in main or "visible_terrain_scratch" in main:
        raise ValueError("Game does not own the retained visible terrain frame plan")
    if "worldgen_open_world_test_v0_12.json" not in runtime_config:
        raise ValueError("client terrain test mode does not select the open-world certification pack")
    if "pixel_snapped_screen_origin" not in terrain_pass:
        raise ValueError("terrain cells are not anchored to a pixel-snapped screen origin")
    base_draw = (ROOT / "crates/haven_game/src/runtime_terrain_base_draw.rs").read_text(encoding="utf-8")
    if base_draw.count("dest_size: Some(vec2(TILE_SIZE, TILE_SIZE))") < 4:
        raise ValueError("direct LPC base cells do not use exact 32x32 destination rectangles")
    runtime_rules = contract["runtime_rules"]
    if runtime_rules.get("direct_lpc_quadrant_composition_owns_compound_boundaries") is not False:
        raise ValueError("legacy direct-quadrant compound-boundary ownership returned")
    if runtime_rules.get("mapped_tuple_atlas_owns_mixed_boundaries") is not True:
        raise ValueError("W77 exact mapped-tuple atlas lost mixed-boundary ownership")
    if runtime_rules.get("unsupported_mixed_tuple_policy") != "owner_fill_plus_diagnostic_workbench_candidate":
        raise ValueError("unsupported mixed tuples no longer route to owner-fill + workbench diagnostics")


def main() -> int:
    contract = load(CONTRACT_PATH)
    if contract.get("schema") != "havenwild.terrain_topology_contract.v0_2":
        raise ValueError("unexpected terrain topology contract schema")
    client = load(CLIENT_SCENE)
    counts = validate_scene(client, contract)
    metrics = load(METRICS_PATH)
    if metrics.get("transition_band_violations") != 0:
        raise ValueError("client terrain metrics report topology violations")
    if metrics.get("terrain_counts") != dict(sorted(counts.items())):
        raise ValueError("client terrain metrics are stale")
    validate_acceptance(contract)
    validate_lpc_evidence()
    validate_runtime_ownership(contract)
    print(
        "Terrain topology validated: "
        f"{len(counts)} semantic roles, 9 acceptance scenes, atlas-backed LPC evidence, retained frame-plan runtime"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
