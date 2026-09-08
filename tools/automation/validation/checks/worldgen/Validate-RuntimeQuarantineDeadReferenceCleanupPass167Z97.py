#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8-sig")


def load(path: str):
    return json.loads(read(path))


def main() -> int:
    contract = load("content/build/runtime_quarantine_dead_reference_cleanup_v167z97.json")
    assert contract["pass"] == "167Z97"
    assert contract["behaviorChange"] == "none"
    assert contract["lintPolicy"] == {
        "unusedImportSuppression": False,
        "deadCodeSuppression": False,
        "strictClippyExpected": True,
    }

    main_rs = read("crates/haven_game/src/main.rs")
    config_import = main_rs.split("use runtime_config::{", 1)[1].split("};", 1)[0]
    assert "WORLD_PAINT_TEST_ATLAS_PATH" not in config_import
    game_struct = main_rs.split("struct Game {", 1)[1].split("}\ninclude!", 1)[0]
    assert "oga_cliff_source" not in game_struct
    assert "allow(unused_imports)" not in main_rs
    assert "expect(dead_code)" not in main_rs

    bootstrap = read("crates/haven_game/src/game_bootstrap.rs")
    assert "oga_cliff_source," in bootstrap.split("let RuntimeAssets {", 1)[1].split("} = assets;", 1)[0]
    constructor = bootstrap.rsplit("Self {", 1)[1]
    assert "            oga_cliff_source," not in constructor
    assert "Procedural cliff source quarantined" in bootstrap

    runtime_assets = read("crates/haven_game/src/runtime_assets.rs")
    assert "WORLD_PAINT_TEST_ATLAS_PATH" in runtime_assets
    assert "world_paint_path.is_file()" in runtime_assets
    assert "let oga_cliff_source: Option<Texture2D> = None;" in runtime_assets

    diagnostics = read("crates/haven_game/src/runtime_diagnostics.rs")
    assert "Pass 167Z97" in diagnostics
    assert "Pass 167Z96" not in diagnostics

    print("Pass167Z97 runtime quarantine dead-reference cleanup validated")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
