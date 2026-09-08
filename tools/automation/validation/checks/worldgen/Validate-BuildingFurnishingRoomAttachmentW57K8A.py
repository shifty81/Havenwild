#!/usr/bin/env python3
"""W57K8A static validation for room-boundary wall-mounted furnishings."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
CATALOG = ROOT / "content/buildings/building_recipe_catalog_v1.json"


def contains(rect: list[int], tile: list[int]) -> bool:
    x, y, w, h = rect
    return x <= tile[0] < x + w and y <= tile[1] < y + h


def wall_boundary(rect: list[int], tile: list[int], edge: str | None) -> bool:
    x, y, w, h = rect
    horizontal = x <= tile[0] < x + w
    vertical = y <= tile[1] < y + h
    return {
        "north": horizontal and tile[1] == y - 1,
        "east": vertical and tile[0] == x + w,
        "south": horizontal and tile[1] == y + h,
        "west": vertical and tile[0] == x - 1,
        "interior": False,
    }.get(edge or "", False)


def main() -> int:
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    errors: list[str] = []
    wall_mounts: list[tuple[str, str, list[int], str | None]] = []

    for entry in catalog["entries"]:
        recipe = json.loads((ROOT / entry["path"]).read_text(encoding="utf-8"))
        for level in recipe.get("levels", []):
            rooms = {room["id"]: room["rect"] for room in level.get("rooms", [])}
            for furnishing in level.get("furnishings", []):
                room = rooms.get(furnishing.get("roomId"))
                if room is None:
                    continue
                tile = furnishing["tile"]
                valid = contains(room, tile)
                if furnishing.get("kind") == "wall_mounted":
                    wall_mounts.append(
                        (recipe["id"], furnishing["id"], tile, furnishing.get("wallAttachment"))
                    )
                    valid = valid or wall_boundary(room, tile, furnishing.get("wallAttachment"))
                if not valid:
                    errors.append(
                        f"{recipe['id']} furnishing {furnishing['id']} anchor {tile} is invalid for room {furnishing['roomId']}"
                    )

    required = {
        ("havenwild.tavern.standard_three_level", "taproom_inn_sign", (5, 10), "south"),
        ("havenwild.tavern.standard_three_level", "taproom_pub_sign", (9, 10), "south"),
    }
    observed = {(recipe, furnishing, tuple(tile), edge) for recipe, furnishing, tile, edge in wall_mounts}
    missing = required - observed
    if missing:
        errors.extend(f"missing expected south-wall mount {item}" for item in sorted(missing))

    if errors:
        print("FAIL W57K8A building furnishing room attachment validation")
        for error in errors:
            print(f"- {error}")
        return 1

    print("PASS W57K8A building furnishing room attachment validation")
    print("- ordinary furnishings remain constrained to their declared room")
    print("- wall-mounted furnishings may anchor on the declared one-cell room boundary")
    print("- existing tavern inn/pub signs are valid south-wall mounts at y=10")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
