#!/usr/bin/env python3
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
CATALOG = ROOT / "content/asset_packs/havenwild_objects/published_world_assets_v1.json"
SCENE_ROOT = ROOT / "content/worldgen/scenes/home_island"
REPORT = ROOT / "content/build/w56d_scene_population_acceptance_v1.json"

SCENES = {
    "north_road": 25,
    "south_field": 20,
    "east_woods": 45,
    "cave_mouth": 20,
}
NATURAL_PREFIXES = (
    "tree_",
    "shrub_",
    "resource_boulder_",
    "forage_",
    "flora_",
)
DEFERRED_PLACEHOLDERS = {
    "stone_signpost",
    "greenhouse_stub",
    "home_birch_tree_mature",
    "old_growth_landmark_tree",
    "ore_node_copper",
}


def intersects(a: list[int], b: list[int]) -> bool:
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    if aw <= 0 or ah <= 0 or bw <= 0 or bh <= 0:
        return False
    return ax < bx + bw and bx < ax + aw and ay < by + bh and by < ay + ah


def rect_inside(rect: list[int], width: int, height: int) -> bool:
    x, y, w, h = rect
    return w >= 0 and h >= 0 and x >= 0 and y >= 0 and x + w <= width and y + h <= height


def main() -> int:
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    published = {entry["id"] for entry in catalog["entries"]}
    failures: list[str] = []
    summaries: list[dict] = []
    deferred: Counter[str] = Counter()

    for scene_id, minimum in SCENES.items():
        path = SCENE_ROOT / f"{scene_id}_scene_v0_3.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        width, height = data["sceneSize"]
        natural = [
            obj
            for obj in data["objects"]
            if obj.get("id", "").startswith(f"{scene_id}_natural_")
        ]
        if len(natural) < minimum:
            failures.append(
                f"{scene_id}: expected at least {minimum} W56 natural objects, found {len(natural)}"
            )
        semantic_ids = Counter(obj["assetId"] for obj in natural)
        if len(semantic_ids) < 6:
            failures.append(
                f"{scene_id}: natural population has only {len(semantic_ids)} semantic asset identities"
            )

        for obj in natural:
            asset_id = obj["assetId"]
            if asset_id not in published:
                failures.append(f"{scene_id}/{obj['id']}: unpublished assetId {asset_id}")
            if not rect_inside(obj["visualRect"], width, height):
                failures.append(f"{scene_id}/{obj['id']}: visualRect leaves scene bounds")
            if not rect_inside(obj["collisionRect"], width, height):
                failures.append(f"{scene_id}/{obj['id']}: collisionRect leaves scene bounds")
            if obj.get("blocksMovement"):
                for transition in data["transitions"]:
                    if intersects(obj["collisionRect"], transition["rect"]):
                        failures.append(
                            f"{scene_id}/{obj['id']}: blocking collision overlaps transition {transition['id']}"
                        )

        for obj in data["objects"]:
            if obj.get("assetId") in DEFERRED_PLACEHOLDERS:
                deferred[obj["assetId"]] += 1

        summaries.append(
            {
                "sceneId": scene_id,
                "naturalObjectCount": len(natural),
                "semanticAssetCount": len(semantic_ids),
                "semanticAssets": dict(sorted(semantic_ids.items())),
            }
        )

    cave = json.loads((SCENE_ROOT / "cave_mouth_scene_v0_3.json").read_text(encoding="utf-8"))
    entrance = next((obj for obj in cave["objects"] if obj.get("id") == "cave_entrance"), None)
    transition = next((item for item in cave["transitions"] if item.get("id") == "to_cave_depths"), None)
    if entrance is None:
        failures.append("cave_mouth: missing cave_entrance object")
    else:
        if entrance.get("assetId") != "cave_entrance_default":
            failures.append("cave_mouth: entrance is not using published cave_entrance_default")
        if entrance.get("visualRect", [0, 0, 0, 0])[2:] != [1, 3]:
            failures.append("cave_mouth: certified host visual must remain 1x3 tiles")
        interactions = entrance.get("interactions", [])
        aperture = next((item for item in interactions if item.get("targetTransition") == "to_cave_depths"), None)
        if aperture is None or aperture.get("rect", [0, 0, 0, 0])[2:] != [1, 2]:
            failures.append("cave_mouth: visible/interaction aperture must be exactly 1x2 tiles")
        if entrance.get("blocksMovement"):
            failures.append("cave_mouth: open cave entrance must not block its approach/aperture")
    if transition is None or transition.get("rect", [0, 0, 0, 0])[2:] != [1, 2]:
        failures.append("cave_mouth: to_cave_depths transition must be exactly 1x2 tiles")

    payload = {
        "schema": "havenwild.scene_population_acceptance.v1",
        "pass": "167Z109W56E",
        "status": "FAIL" if failures else "PASS",
        "scenes": summaries,
        "deferredPlaceholderAssets": dict(sorted(deferred.items())),
        "caveMouth": {
            "assetId": entrance.get("assetId") if entrance else None,
            "hostVisualTiles": entrance.get("visualRect", [0, 0, 0, 0])[2:] if entrance else None,
            "transitionApertureTiles": transition.get("rect", [0, 0, 0, 0])[2:] if transition else None,
        },
        "failures": failures,
    }
    REPORT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    if failures:
        print("FAIL: W56 scene population/cave-mouth authority")
        for failure in failures:
            print(f" - {failure}")
        return 1
    print("PASS: W56 scene population uses published semantic assets and the cave aperture is 1x2.")
    for summary in summaries:
        print(
            f" - {summary['sceneId']}: natural={summary['naturalObjectCount']} "
            f"semantic_assets={summary['semanticAssetCount']}"
        )
    if deferred:
        print("Deferred placeholder assets (not silently substituted):")
        for asset_id, count in sorted(deferred.items()):
            print(f" - {asset_id}: {count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
