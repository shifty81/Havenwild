#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"FAILED Pass167Z105E geological-height round-trip hotfix: {message}")


def main() -> None:
    contract = json.loads(
        (ROOT / "content/build/foundation_geological_height_hotfix_v167z105e.json").read_text(encoding="utf-8")
    )
    require(contract["schema"] == "havenwild.build.foundation_geological_height_hotfix.v167z105e", "contract schema")
    require(contract["pass"] == "167Z105E", "contract pass")
    require(contract["rawGeologicalStorageDomain"] == "u8 / 0..255", "raw byte domain retained")
    require(contract["structuralLevelsRemainIndependent"] is True, "structural levels independent")
    require(contract["saveFormatSectionChanged"] is False, "save format unchanged")
    require(contract["worldgenGenerationBehaviorChanged"] is False, "worldgen behavior unchanged")
    require(contract["cliffRuntimeBehaviorChanged"] is False, "cliff runtime unchanged")
    require(contract["testWeakened"] is False, "failing test not weakened")

    foundation = (ROOT / "crates/haven_core/src/foundation.rs").read_text(encoding="utf-8")
    require("map.set_height(x as i32 + offset_x, y as i32 + offset_y, height);" in foundation,
            "deserializer preserves serialized u8 height")
    require("map.set_height(x as i32 + offset_x, y as i32 + offset_y, height.min(100));" not in foundation,
            "obsolete load-time 100 clamp removed")

    tests = (ROOT / "crates/haven_core/src/foundation/foundation_tests.rs").read_text(encoding="utf-8")
    require("fn structural_levels_round_trip_without_rewriting_geological_height()" in tests,
            "round-trip regression test retained")
    require("map.set_height(7, 9, 223);" in tests, "test still exercises byte value above 100")
    require("assert_eq!(decoded.get_height(7, 9), 223);" in tests, "test still requires exact preservation")

    print("Pass167Z105E geological-height round-trip hotfix validation passed")


if __name__ == "__main__":
    main()
