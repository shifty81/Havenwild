#!/usr/bin/env python3
"""Build W43D complete ObjectKind visual acceptance scene.

Unlike the W43A published-candidate fixture, this board deliberately contains
one slot for every gameplay ObjectKind. Rejected/missing/quarantined kinds are
kept as empty/fail-closed diagnostic objects so the editor can expose their
identity without substituting unrelated artwork.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

SWEEP_REL = Path("content/asset_packs/havenwild_objects/placeable_visual_sweep_v1.json")
MANIFEST_REL = Path("assets/generated/havenwild_lpc_objects_160x192_v2.json")
OUTPUT_REL = Path("content/worldgen/scenes/world_asset_acceptance/placeable_visual_acceptance_scene_v1.json")
SCENE_W = 72
SCENE_H = 52
COLS = 4
START_X = 8
START_Y = 7
STEP_X = 17
STEP_Y = 7


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def centered_visual(anchor_x: int, anchor_y: int, size: list[int]) -> list[int]:
    w, h = max(1, int(size[0])), max(1, int(size[1]))
    # Object anchors are bottom-center/root cells in Havenwild's world-object
    # contract. Keep large visual footprints above the root cell.
    return [anchor_x - (w // 2), anchor_y - (h - 1), w, h]


def build(root: Path) -> dict:
    sweep = load(root / SWEEP_REL)
    manifest = load(root / MANIFEST_REL)
    cache_by_id = {e.get("id"): e for e in manifest.get("objects", []) if e.get("id")}

    objects = []
    rows = []
    for index, entry in enumerate(sweep.get("entries", [])):
        kind = str(entry["objectKind"])
        status = str(entry["status"])
        runtime_binding = entry.get("runtimeBinding")
        cache = cache_by_id.get(runtime_binding) if runtime_binding else None
        col = index % COLS
        row = index // COLS
        x = START_X + col * STEP_X
        y = START_Y + row * STEP_Y

        visual_size = list((cache or {}).get("visualFootprintTiles", [1, 1]))
        collision_size = list((cache or {}).get("collisionFootprintTiles", [1, 1]))
        visual_rect = centered_visual(x, y, visual_size)
        collision_rect = [x, y, max(0, int(collision_size[0])), max(0, int(collision_size[1]))]
        asset_id = runtime_binding or kind

        obj = {
            "id": f"accept_object_kind_{kind}",
            "assetId": asset_id,
            "objectKind": kind,
            "acceptanceLane": "complete_placeable_visual_sweep",
            "acceptanceStatus": status,
            "visualRect": visual_rect,
            "collisionRect": collision_rect,
            "layer": "tall_object" if kind == "tree" else "low_object",
            "blocksMovement": collision_rect[2] > 0 and collision_rect[3] > 0,
            "occludesPlayer": bool((cache or {}).get("occludesPlayer", False)),
            "fadeWhenPlayerBehind": bool((cache or {}).get("fadeWhenPlayerBehind", False)),
            "interactions": [{"id": f"inspect_{kind}", "kind": "inspect", "rect": [x, y, 1, 1]}],
            "acceptance": {
                "status": status,
                "role": entry.get("role"),
                "runtimeBinding": runtime_binding,
                "nextAction": entry.get("nextAction"),
                "note": entry.get("note"),
                "sourcePath": (cache or {}).get("source"),
                "sourceRect": (cache or {}).get("sourceRect"),
                "sourceMode": (cache or {}).get("sourceMode"),
                "runtimeCacheRect": (cache or {}).get("rect"),
                "footAnchorPixels": (cache or {}).get("footAnchor"),
                "failClosedExpected": status in {"REJECTED", "MISSING", "PLACEHOLDER"},
            },
        }
        objects.append(obj)
        rows.append({
            "objectKind": kind,
            "status": status,
            "assetId": asset_id,
            "anchor": [x, y],
            "visibleArtworkExpected": bool(runtime_binding) and status not in {"REJECTED", "MISSING", "PLACEHOLDER"},
        })

    terrain = [["grass" for _ in range(SCENE_W)] for _ in range(SCENE_H)]
    zones = [["none" for _ in range(SCENE_W)] for _ in range(SCENE_H)]
    return {
        "id": "placeable_visual_acceptance_scene_v1",
        "version": "1.0.0",
        "kind": "worldgen_scene",
        "sceneId": "placeable_visual_acceptance",
        "title": "Placeable Visual Acceptance — W43D",
        "sceneKind": "exterior",
        "biome": "temperate",
        "role": "diagnostic_only",
        "sceneSize": [SCENE_W, SCENE_H],
        "tileSize": [32, 32],
        "edgePolicy": {"mustAvoidVoid": True, "resolvedBorders": {"north": "grass", "south": "grass", "east": "grass", "west": "grass"}},
        "layers": {"terrain": terrain, "zones": zones},
        "objects": objects,
        "transitions": [],
        "spawns": [{"id": "player_default", "kind": "player", "tile": [3, 49]}],
        "editor": {
            "showLayers": ["terrain", "objects", "collision", "interactions"],
            "defaultTool": "inspect_select",
            "allowPaintTerrain": False,
            "allowMoveObjects": True,
        },
        "acceptance": {
            "milestone": "Pass167Z109W43D",
            "productionRegistered": False,
            "visualSweep": SWEEP_REL.as_posix(),
            "objectKindCount": len(rows),
            "rows": rows,
            "visualAssertions": [
                "one diagnostic slot exists for every gameplay ObjectKind",
                "ordinary crate renders one singular crate rather than an entire source sheet",
                "rejected/missing/placeholder kinds fail closed instead of rendering unrelated artwork",
                "candidate anchors, footprint, sorting and source identity are reviewed before certification",
            ],
        },
        "validationRules": [
            "all_object_kinds_present_once",
            "rejected_and_missing_bindings_fail_closed",
            "crate_is_singular_exact_source_slice",
            "diagnostic_scene_never_becomes_production_content",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[3])
    args = parser.parse_args()
    root = args.root.resolve()
    scene = build(root)
    output = root / OUTPUT_REL
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(scene, indent=2) + "\n", encoding="utf-8")
    print(f"W43D placeable visual acceptance scene: {len(scene['objects'])} ObjectKinds -> {OUTPUT_REL.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
