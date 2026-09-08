#!/usr/bin/env python3
"""Restore Pass 95 runtime metadata from the canonical complete summer contract.

The original source-only Pass 95 export excluded content/assets too broadly.
This deterministic migration reconstructs the two promoted transition entries
and pebble fill bindings from the already validated complete-map contract.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CONTRACT = ROOT / "content/assets/intake/lpc_terrain_summer_complete_map_v0_1.json"
MAPPING = ROOT / "content/assets/intake/lpc_terrain_family_mapping_v0_3.json"
PROMOTION = ROOT / "content/assets/intake/lpc_terrain_promotion_v0_2.json"


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def by_id(records: list[dict], wanted: str) -> dict:
    for record in records:
        if record.get("id") in {wanted, f"summer_{wanted}"}:
            return record
    raise KeyError(f"canonical summer contract is missing {wanted}")


def runtime_family(source: dict, runtime_id: str, classifier: str, inner: bool) -> dict:
    result = {
        "id": runtime_id,
        "owner": source["owner"],
        "neighbor": source["neighbor"],
        "outerBlock": source["outerBlock"],
        "foregroundClassifier": source.get("foregroundClassifier", classifier),
        "runtimeOuterMasks": True,
        "runtimeInnerCorners": inner,
    }
    if inner:
        block = source.get("innerCornerBlock")
        if block is None:
            raise ValueError(f"{runtime_id} requires its verified 2x2 inner-corner block")
        result["innerCornerBlock"] = block
    return result


def replace_or_append(records: list[dict], replacement: dict) -> None:
    for index, record in enumerate(records):
        if record.get("id") == replacement["id"]:
            records[index] = replacement
            return
    records.append(replacement)


def main() -> int:
    contract = read(CONTRACT)
    mapping = read(MAPPING)
    promotion = read(PROMOTION) if PROMOTION.is_file() else {
        "schema": "havenwild.lpc_terrain_promotion.v0_2",
        "baseTileCells": {},
    }

    sand = by_id(contract["transitionFamilies"], "sand_over_wet_sand")
    pebble = by_id(contract["transitionFamilies"], "pebble_path_over_dirt")
    pebble_fill = by_id(contract["fillFamilies"], "pebble_path_fill")
    for source_group in (sand, pebble, pebble_fill):
        source_group["runtimeStatus"] = "active"

    families = mapping.setdefault("transitionFamilies", [])
    replace_or_append(families, runtime_family(sand, "sand_over_wet_sand", "sand", True))
    replace_or_append(
        families,
        runtime_family(pebble, "pebble_path_over_dirt", "non_water_bank", False),
    )

    cells = pebble_fill.get("cells")
    if not cells:
        raise ValueError("summer_pebble_path_fill has no source cells")
    base_cells = promotion.setdefault("baseTileCells", {})
    base_cells["pebble_shore"] = cells
    base_cells["stone_path"] = cells
    promotion["schema"] = "havenwild.lpc_terrain_promotion.v0_2"
    promotion["sourceContract"] = str(CONTRACT.relative_to(ROOT)).replace("\\", "/")
    promotion["notes"] = [
        "Pass 96A restores metadata omitted by the Pass 95 source-only export.",
        "Coordinates are copied from the validated complete summer source contract; none are guessed.",
    ]

    write(MAPPING, mapping)
    write(PROMOTION, promotion)
    write(CONTRACT, contract)
    print("Restored Pass 95 runtime metadata: sand_over_wet_sand, pebble_path_over_dirt, pebble_path_fill")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
