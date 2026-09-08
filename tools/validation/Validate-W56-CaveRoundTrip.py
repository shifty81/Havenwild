#!/usr/bin/env python3
"""Validate the canonical Estate -> Cave Mouth -> Cave Depths round trip.

Checks the facts the runtime actually consumes: transition rectangles and toSpawn cells.
ReturnTransitionId is retained as authored metadata, but current runtime movement uses toSpawn
coordinates directly, so all destination cells must be clear and must not themselves be a
transition trigger.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCENE_DIR = ROOT / "content/worldgen/scenes/home_island"
FILES = {
    "farmstead": SCENE_DIR / "farmstead_scene_v0_3.json",
    "cave_mouth": SCENE_DIR / "cave_mouth_scene_v0_3.json",
    "cave_depths": SCENE_DIR / "cave_depths_scene_v0_3.json",
}
SOLID_TILES = {"Wall", "CaveWall", "Cliff", "MountainRock", "Water", "Void"}


def load(path: Path):
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def contains(rect, x, y):
    rx, ry, rw, rh = rect
    return rx <= x < rx + rw and ry <= y < ry + rh


def transition(scene, transition_id):
    for item in scene.get("transitions", []):
        if item.get("id") == transition_id:
            return item
    raise AssertionError(f"{scene.get('sceneId')}: missing transition {transition_id}")


def destination_is_clear(scene, x, y):
    width, height = scene["sceneSize"]
    if not (0 <= x < width and 0 <= y < height):
        return False, "outside scene bounds"
    tile = scene["layers"]["terrain"][y][x]
    if tile in SOLID_TILES:
        return False, f"solid terrain {tile}"
    for obj in scene.get("objects", []):
        rect = obj.get("collisionRect")
        if rect and contains(rect, x, y):
            # A zero-area collision does not block. Existing authored scenes often omit
            # blocksMovement, so a non-empty collision rectangle is treated as blocking.
            if rect[2] > 0 and rect[3] > 0:
                return False, f"object collision {obj.get('id')} {rect}"
    for tr in scene.get("transitions", []):
        if contains(tr["rect"], x, y):
            return False, f"destination sits on transition trigger {tr.get('id')}"
    return True, tile


def main():
    scenes = {key: load(path) for key, path in FILES.items()}
    expected = [
        ("farmstead", "to_cave_mouth", "cave_mouth", [48, 44]),
        ("cave_mouth", "to_farmstead", "farmstead", [78, 11]),
        ("cave_mouth", "to_cave_depths", "cave_depths", [48, 43]),
        ("cave_depths", "to_cave_mouth", "cave_mouth", [48, 31]),
    ]
    failures = []
    for source_id, transition_id, target_id, expected_spawn in expected:
        tr = transition(scenes[source_id], transition_id)
        if tr.get("toScene") != target_id:
            failures.append(f"{source_id}/{transition_id}: target={tr.get('toScene')} expected={target_id}")
        if tr.get("toSpawn") != expected_spawn:
            failures.append(f"{source_id}/{transition_id}: toSpawn={tr.get('toSpawn')} expected={expected_spawn}")
        x, y = tr["toSpawn"]
        clear, detail = destination_is_clear(scenes[target_id], x, y)
        if not clear:
            failures.append(f"{source_id}/{transition_id}: destination {target_id}@{x},{y} is not clear: {detail}")

    depth_exit = transition(scenes["cave_depths"], "to_cave_mouth")
    rx, ry, rw, rh = depth_exit["rect"]
    for y in range(ry, ry + rh):
        for x in range(rx, rx + rw):
            tile = scenes["cave_depths"]["layers"]["terrain"][y][x]
            if tile in SOLID_TILES:
                failures.append(f"cave_depths return trigger includes solid tile {tile} at {x},{y}")

    # Estate's authored return spawn is deliberately outside the automatic trigger cell.
    from_cave = next(s for s in scenes["farmstead"].get("spawns", []) if s.get("id") == "from_cave")
    if from_cave.get("tile") != [78, 11]:
        failures.append(f"Estate from_cave spawn is {from_cave.get('tile')}, expected [78, 11]")

    if failures:
        for failure in failures:
            print("FAIL:", failure)
        return 1
    print("PASS: Estate / Cave Mouth / Cave Depths form a clear, non-bouncing runtime round trip.")
    for source_id, transition_id, target_id, _ in expected:
        tr = transition(scenes[source_id], transition_id)
        print(f"  {source_id}:{transition_id} -> {target_id}@{tr['toSpawn']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
