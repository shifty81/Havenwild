#!/usr/bin/env python3
"""Build the shared seasonal topology contract from the complete summer sheet map.

The summer source is the canonical coordinate layout. Spring, autumn, winter,
and winter-ice bind to the same cell roles, so runtime/editor topology logic is
implemented once and only the seasonal source sheet changes.
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "assets/generated/worldgen_v0_1/terrain/lpc_terrain_summer_complete_map_32.json"
OUTPUT = ROOT / "content/assets/lpc/lpc_seasonal_terrain_topology_v0_1.json"

OUTER_ROLES = [
    "outer_north_west",
    "outer_north",
    "outer_north_east",
    "outer_west",
    "center",
    "outer_east",
    "outer_south_west",
    "outer_south",
    "outer_south_east",
]
INNER_ROLES = [
    "inner_north_west",
    "inner_north_east",
    "inner_south_west",
    "inner_south_east",
]
SEASON_ORDER = ["summer", "spring", "autumn", "winter", "winter_ice"]


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def role_cells(cells: list[dict], component: str) -> dict[str, list[int]]:
    selected: dict[str, list[int]] = {}
    for cell in cells:
        if cell.get("component") != component:
            continue
        role = cell.get("role")
        coordinate = cell.get("cell")
        if isinstance(role, str) and isinstance(coordinate, list):
            selected[role] = coordinate
    return selected


def main() -> int:
    source = read_json(SOURCE)
    grouped: dict[str, list[dict]] = defaultdict(list)
    for cell in source["cells"]:
        group_id = cell.get("groupId")
        if group_id:
            grouped[group_id].append(cell)

    season_sources = {"summer": source["source"]}
    for record in source.get("seasonalLayoutParity", []):
        if not record.get("layoutCompatible"):
            raise ValueError(f"season layout is not compatible: {record}")
        season_sources[record["season"]] = record["source"]

    families: list[dict] = []
    for group_id in sorted(grouped):
        cells = grouped[group_id]
        outer = role_cells(cells, "outerBlock")
        inner = role_cells(cells, "innerCornerBlock")
        if not outer and not inner:
            continue
        missing_outer = [role for role in OUTER_ROLES if role not in outer]
        if missing_outer:
            raise ValueError(f"{group_id} missing outer roles: {missing_outer}")
        if inner:
            missing_inner = [role for role in INNER_ROLES if role not in inner]
            if missing_inner:
                raise ValueError(f"{group_id} missing inner roles: {missing_inner}")

        sample = cells[0]
        seasonal_bindings = []
        for season in SEASON_ORDER:
            source_path = season_sources.get(season)
            if source_path:
                seasonal_bindings.append(
                    {
                        "season": season,
                        "source": source_path,
                        "outerRoles": {role: outer[role] for role in OUTER_ROLES},
                        "innerRoles": {role: inner[role] for role in INNER_ROLES if role in inner},
                    }
                )

        families.append(
            {
                "id": group_id,
                "label": sample.get("groupLabel", group_id),
                "classification": sample.get("classification"),
                "owner": sample.get("owner"),
                "neighbor": sample.get("neighbor"),
                "runtimeStatus": sample.get("runtimeStatus"),
                "outerTopology": {
                    "northWest": outer["outer_north_west"],
                    "north": outer["outer_north"],
                    "northEast": outer["outer_north_east"],
                    "west": outer["outer_west"],
                    "center": outer["center"],
                    "east": outer["outer_east"],
                    "southWest": outer["outer_south_west"],
                    "south": outer["outer_south"],
                    "southEast": outer["outer_south_east"],
                },
                "innerTopology": {
                    "northWest": inner.get("inner_north_west"),
                    "northEast": inner.get("inner_north_east"),
                    "southWest": inner.get("inner_south_west"),
                    "southEast": inner.get("inner_south_east"),
                },
                "seasonalBindings": seasonal_bindings,
                "topologyRule": "shared_8_neighbor_owner_side",
            }
        )

    payload = {
        "schema": "havenwild.lpc_seasonal_terrain_topology.v0.1",
        "canonicalSeason": "summer",
        "cellSize": source["cellSize"],
        "grid": source["grid"],
        "sourceContract": str(SOURCE.relative_to(ROOT)).replace("\\", "/"),
        "seasons": [
            {"id": season, "source": season_sources[season]}
            for season in SEASON_ORDER
            if season in season_sources
        ],
        "topology": {
            "neighborModel": "8-neighbor",
            "ownerRule": "one ordered material pair owns each visual boundary",
            "outerRule": "cardinal mask selects the complete authored 3x3 role",
            "innerRule": "diagonal-only neighbor selects the matching authored 2x2 concave role",
            "seasonRule": "all seasons reuse summer coordinates and semantic role IDs",
        },
        "summary": {
            "familyCount": len(families),
            "familiesWithInnerCorners": sum(
                1 for family in families if any(family["innerTopology"].values())
            ),
            "seasonCount": len(season_sources),
        },
        "families": families,
    }
    write_json(OUTPUT, payload)
    print(
        f"Wrote {OUTPUT.relative_to(ROOT)} with {len(families)} topology families "
        f"across {len(season_sources)} seasonal sheets"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
