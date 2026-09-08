#!/usr/bin/env python3
"""Validate the Pass 134 LPC tuple promotion plan workflow."""
from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[5]
BUILD_SCRIPT = ROOT / "tools/automation/terrain/Build-LpcTuplePromotionPlanV134.py"
PLAN_JSON = ROOT / "content/assets/lpc/lpc_tuple_promotion_plan_v0_1.json"
PLAN_MD = ROOT / "docs/assets/LPC_TUPLE_PROMOTION_PLAN_PASS134.md"
PLAN_PREVIEW = ROOT / "docs/assets/previews/havenwild_lpc_tuple_promotion_plan_pass134.png"


def require_tokens(path: Path, tokens: list[str]) -> None:
    text = path.read_text(encoding="utf-8")
    missing = [token for token in tokens if token not in text]
    if missing:
        raise SystemExit(f"V134: {path.relative_to(ROOT)} is missing {missing}")


def main() -> int:
    require_tokens(
        BUILD_SCRIPT,
        [
            "production_water_shore",
            "water_depth",
            "production_land_edge",
            "fallbackSafety",
            "havenwild_lpc_tuple_promotion_plan_pass134.png",
        ],
    )
    for path in [PLAN_JSON, PLAN_MD, PLAN_PREVIEW]:
        if not path.exists():
            raise SystemExit(f"V134: missing {path.relative_to(ROOT)}")

    plan = json.loads(PLAN_JSON.read_text(encoding="utf-8"))
    if plan.get("kind") != "terrain_tuple_promotion_plan":
        raise SystemExit("V134: tuple promotion plan kind is incorrect")
    rows = plan.get("rows", [])
    if not rows:
        raise SystemExit("V134: tuple promotion plan has no rows")
    if not all(row.get("fallbackPatterns", 0) > 0 for row in rows):
        raise SystemExit("V134: tuple promotion rows must only contain fallback-heavy pairs")
    categories = {row.get("category") for row in rows}
    completed = set(plan.get("completedPromotionCategories", []))
    required = {"production_water_shore", "water_depth", "production_land_edge"}
    if not required.issubset(categories | completed):
        raise SystemExit(
            f"V134: tuple promotion plan missing active/completed priority categories "
            f"{sorted(required - categories - completed)}"
        )
    priorities = [row.get("priority", 0) for row in rows]
    if priorities != sorted(priorities, reverse=True):
        raise SystemExit("V134: tuple promotion rows must be priority sorted")

    with Image.open(PLAN_PREVIEW) as preview:
        if preview.width < 700 or preview.height < 500:
            raise SystemExit("V134: tuple promotion preview is unexpectedly small")

    print("V134 OK: fallback-heavy LPC terrain tuples are prioritized for exact-art promotion")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
