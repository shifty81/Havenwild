#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCENE_ROOT = ROOT / "content/worldgen/scenes/home_island"
LEGACY_SIZE = (48, 32)
RUNTIME_SIZE = (96, 64)
OFFSET = (
    (RUNTIME_SIZE[0] - LEGACY_SIZE[0]) // 2,
    (RUNTIME_SIZE[1] - LEGACY_SIZE[1]) // 2,
)


def shifted_point(value: list[int]) -> list[int]:
    return [int(value[0]) + OFFSET[0], int(value[1]) + OFFSET[1]]


def shifted_rect(value: list[int]) -> list[int]:
    return [int(value[0]) + OFFSET[0], int(value[1]) + OFFSET[1], int(value[2]), int(value[3])]


def promote_grid(grid: list[list[str]], fill: str) -> list[list[str]]:
    if len(grid) == RUNTIME_SIZE[1] and all(len(row) == RUNTIME_SIZE[0] for row in grid):
        return grid
    if len(grid) != LEGACY_SIZE[1] or any(len(row) != LEGACY_SIZE[0] for row in grid):
        raise ValueError(f"unexpected grid size {len(grid)} rows")
    output = [[fill for _ in range(RUNTIME_SIZE[0])] for _ in range(RUNTIME_SIZE[1])]
    for y, row in enumerate(grid):
        output[y + OFFSET[1]][OFFSET[0] : OFFSET[0] + LEGACY_SIZE[0]] = row
    return output


def promote_scene(path: Path) -> bool:
    scene = json.loads(path.read_text(encoding="utf-8"))
    source_size = tuple(scene.get("sceneSize", []))
    if source_size == RUNTIME_SIZE:
        return False
    if source_size != LEGACY_SIZE:
        raise ValueError(f"{path.name}: unsupported sceneSize {source_size}")

    scene_kind = str(scene.get("sceneKind", "exterior"))
    terrain_fill = {
        "exterior": "Grass",
        "interior": "Wall",
        "cave": "CaveWall",
    }.get(scene_kind, "Grass")
    layers = scene.setdefault("layers", {})
    layers["terrain"] = promote_grid(layers.get("terrain", []), terrain_fill)
    if "zones" in layers:
        layers["zones"] = promote_grid(layers["zones"], "none")

    for placed in scene.get("objects", []):
        for key in ("visualRect", "collisionRect"):
            if key in placed:
                placed[key] = shifted_rect(placed[key])
        for interaction in placed.get("interactions", []):
            if "rect" in interaction:
                interaction["rect"] = shifted_rect(interaction["rect"])

    for transition in scene.get("transitions", []):
        if "rect" in transition:
            transition["rect"] = shifted_rect(transition["rect"])
        if "toSpawn" in transition:
            transition["toSpawn"] = shifted_point(transition["toSpawn"])

    for spawn in scene.get("spawns", []):
        if "tile" in spawn:
            spawn["tile"] = shifted_point(spawn["tile"])

    scene["sceneSize"] = list(RUNTIME_SIZE)
    scene["sceneScaleMigration"] = {
        "from": list(LEGACY_SIZE),
        "to": list(RUNTIME_SIZE),
        "offset": list(OFFSET),
        "mode": "center_preserve_authored_content",
        "pass": 88,
    }
    path.write_text(json.dumps(scene, indent=2) + "\n", encoding="utf-8")
    return True


def main() -> int:
    changed = 0
    files = sorted(SCENE_ROOT.glob("*_scene_v0_3.json"))
    if not files:
        raise SystemExit("no home-island scenes found")
    for path in files:
        changed += int(promote_scene(path))
    print(
        f"Scene scale promotion V88 complete: {changed} changed, {len(files)} checked, "
        f"runtime {RUNTIME_SIZE[0]}x{RUNTIME_SIZE[1]}, offset {OFFSET[0]},{OFFSET[1]}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
