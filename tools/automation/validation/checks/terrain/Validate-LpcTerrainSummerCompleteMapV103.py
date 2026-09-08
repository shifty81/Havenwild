#!/usr/bin/env python3
"""Validate the exhaustive LPC summer terrain source map."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
CONTRACT = ROOT / "content/assets/intake/lpc_terrain_summer_complete_map_v0_1.json"
LEDGER = ROOT / "assets/generated/worldgen_v0_1/terrain/lpc_terrain_summer_complete_map_32.json"
BUILDER = ROOT / "tools/automation/terrain/Build-LpcTerrainSummerCompleteMapV103.py"


def main() -> int:
    required = [CONTRACT, LEDGER, BUILDER]
    missing = [str(path.relative_to(ROOT)) for path in required if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"missing LPC summer complete-map files: {missing}")

    completed = subprocess.run(
        [sys.executable, str(BUILDER), "--check"],
        cwd=ROOT,
        check=False,
    )
    if completed.returncode:
        return completed.returncode

    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
    summary = ledger["summary"]

    if summary["totalCells"] != 416:
        raise ValueError(f"expected 416 summer source cells, found {summary['totalCells']}")
    if summary["nonTransparentCells"] != 305:
        raise ValueError(
            f"expected 305 non-transparent summer cells, found "
            f"{summary['nonTransparentCells']}"
        )
    if summary["mappedNonTransparentCells"] != summary["nonTransparentCells"]:
        raise ValueError("not every non-transparent summer cell is mapped")
    if not summary["allNonTransparentCellsMapped"] or not summary["noPrimaryGroupOverlap"]:
        raise ValueError("summer mapping coverage/overlap contract failed")

    group_ids = {
        item["id"]
        for section in ("fillFamilies", "transitionFamilies", "modularStrips", "decorations")
        for item in contract[section]
    }
    required_groups = {
        "summer_grass_over_dirt",
        "summer_grass_over_sand",
        "summer_sand_over_wet_sand",
        "summer_sand_bank_pond",
        "summer_deep_water_basin",
        "summer_water_fill",
    }
    if not required_groups.issubset(group_ids):
        raise ValueError(f"required summer groups missing: {sorted(required_groups - group_ids)}")

    cells = ledger["cells"]
    if len(cells) != 416:
        raise ValueError(f"generated cell ledger contains {len(cells)} cells, expected 416")
    coords = {tuple(record["cell"]) for record in cells}
    expected = {(x, y) for y in range(26) for x in range(16)}
    if coords != expected:
        raise ValueError("generated cell ledger does not cover the complete 16x26 grid")

    print(
        "V103 LPC summer complete-map validation passed: "
        f"{summary['mappedNonTransparentCells']}/{summary['nonTransparentCells']} "
        "non-transparent cells mapped with seasonal layout parity"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
