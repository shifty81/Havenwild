#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
CATALOG = ROOT / "content/asset_packs/havenwild_objects/published_world_assets_v1.json"
SCENE = ROOT / "content/worldgen/scenes/world_asset_acceptance/world_asset_acceptance_scene_v1.json"
PACK = ROOT / "content/worldgen/packs/worldgen_home_island_test_v0_11.json"
SCANNER = ROOT / "tools/automation/assets/Build-PublishedWorldAssetInventoryV1.py"
BUILDER = ROOT / "tools/automation/assets/Build-WorldAssetAcceptanceSceneV1.py"


def need(value: bool, message: str) -> None:
    if not value:
        raise SystemExit(f"FAIL W43A world asset acceptance: {message}")


def load(path: Path):
    need(path.is_file(), f"missing {path.relative_to(ROOT)}")
    return json.loads(path.read_text(encoding="utf-8-sig"))


def offset_rect(anchor: list[int], offset: list[int], size: list[int]) -> list[int]:
    return [anchor[0] + offset[0], anchor[1] + offset[1], size[0], size[1]]


def main() -> int:
    catalog = load(CATALOG)
    scene = load(SCENE)
    pack = load(PACK)
    need(BUILDER.is_file(), "acceptance scene builder missing")
    need(scene.get("sceneId") == "world_asset_acceptance", "sceneId mismatch")
    need(scene.get("role") == "diagnostic_only", "acceptance scene must remain diagnostic-only")
    need(scene.get("acceptance", {}).get("productionRegistered") is False, "W43A fixture must not become production content")

    spec = importlib.util.spec_from_file_location("havenwild_w43_asset_truth", SCANNER)
    need(spec is not None and spec.loader is not None, "could not load Asset Truth scanner")
    scanner = importlib.util.module_from_spec(spec)
    import sys
    sys.modules[spec.name] = scanner
    spec.loader.exec_module(scanner)
    queue = scanner.build(ROOT)["migrationQueue"]
    candidates = list(queue["sceneCandidates"])
    blockers = set(queue["sceneBlockers"])
    need(len(candidates) > 0, "current Asset Truth migration queue unexpectedly has no scene candidates")

    entries = catalog.get("entries", [])
    by_alias = {alias: entry for entry in entries for alias in entry.get("aliases", [])}
    objects = scene.get("objects", [])
    need(len(objects) == 29, f"expected 29 acceptance objects, got {len(objects)}")
    scene_aliases = [obj.get("assetId") for obj in objects]
    need(len(scene_aliases) == len(set(scene_aliases)), "acceptance scene contains duplicate aliases")
    # W43A is a frozen 29-item historical acceptance fixture. Later asset
    # passes legitimately promote/reclassify the live migration queue, so that
    # current queue must not rewrite or invalidate the original evidence board.
    need(scene.get("acceptance", {}).get("assetCount") == 29, "historical W43A assetCount drifted")
    need(not (set(scene_aliases) & blockers), "W41 blocker was placed into W43A acceptance fixture")

    width, height = scene["sceneSize"]
    for obj in objects:
        alias = obj["assetId"]
        entry = by_alias.get(alias)
        need(entry is not None, f"{alias} does not resolve through published aliases")
        need(obj.get("publishedAssetId") == entry.get("id"), f"{alias} canonical ID mismatch")
        need(entry.get("certification") == "candidate", f"{alias} must remain candidate pending visual acceptance")
        fp = entry["footprint"]
        collision = obj["collisionRect"]
        anchor = [collision[0] - fp.get("collision_offset", [0, 0])[0], collision[1] - fp.get("collision_offset", [0, 0])[1]]
        expected_visual = offset_rect(anchor, fp.get("visual_offset", [0, 0]), fp["visual_size"])
        expected_collision = offset_rect(anchor, fp.get("collision_offset", [0, 0]), fp["collision_size"])
        expected_interaction = offset_rect(anchor, fp.get("interaction_offset", [0, 0]), fp["interaction_size"])
        need(obj["visualRect"] == expected_visual, f"{alias} visual rect does not match published footprint")
        need(obj["collisionRect"] == expected_collision, f"{alias} collision rect does not match published footprint")
        need(obj["interactions"][0]["rect"] == expected_interaction, f"{alias} interaction rect does not match published footprint")
        for label, rect in (("visual", expected_visual), ("collision", expected_collision), ("interaction", expected_interaction)):
            x, y, w, h = rect
            need(x >= 0 and y >= 0 and x + w <= width and y + h <= height, f"{alias} {label} rect leaves the scene")
        acceptance = obj.get("acceptance", {})
        need(acceptance.get("sourceAuthority") == "lpc_revised_manifest", f"{alias} source authority is not LPC manifest")
        need(acceptance.get("sourceRect") == entry.get("provenance", {}).get("source_rect"), f"{alias} exact source rect drift")
        need(acceptance.get("runtimeCacheRect") == entry.get("visual", {}).get("frames", [{}])[0].get("source_rect"), f"{alias} cache rect drift")
        need(acceptance.get("footAnchorPixels") == entry.get("visual", {}).get("foot_anchor"), f"{alias} foot anchor drift")

    scene_rel = SCENE.relative_to(ROOT).as_posix()
    need(scene_rel in pack.get("sceneFiles", []), "acceptance scene is not loadable through the development test pack")
    need(scene_rel in pack.get("smokeTests", []), "acceptance scene is not in development smoke tests")
    need(pack.get("testWorld", {}).get("worldAssetAcceptanceSceneId") == "world_asset_acceptance", "test pack lacks W43 scene identity")

    print("PASS W43A published world asset acceptance fixture")
    print(json.dumps({
        "acceptanceAssets": len(objects),
        "historicalAcceptanceAliases": len(objects),
        "currentMigrationCandidates": len(candidates),
        "blockersExcluded": len(blockers),
        "sceneId": scene["sceneId"],
        "sceneSize": scene["sceneSize"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
