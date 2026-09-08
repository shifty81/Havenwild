#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"FAILED Pass167Z94 Rust toolchain cliff renderer compatibility: {message}")


def main() -> None:
    quarantine = ROOT / "content/build/runtime_asset_integrity_cliff_quarantine_v167z96.json"
    if quarantine.is_file():
        contract = json.loads(quarantine.read_text(encoding="utf-8"))
        require(contract["pass"] == "167Z96", "Z96 quarantine pass")
        require(contract["runtimePolicy"]["proceduralCliffDrawing"] is False, "invalid renderer disabled")
        print("Pass167Z94 toolchain compatibility remains satisfied under Pass167Z96 quarantine")
        return
    contract = json.loads(
        (ROOT / "content/build/rust_toolchain_compatibility_v167z94.json").read_text(
            encoding="utf-8"
        )
    )
    require(
        contract["schema"] == "havenwild.build.rust_toolchain_compatibility.v0_1",
        "schema",
    )
    require(contract["pass"] == "167Z94", "pass")
    require(contract["repair"]["lintSuppressionAdded"] is False, "no lint suppression")
    require(contract["repair"]["runtimeBehaviorChanged"] is False, "no runtime behavior change")

    source = (
        ROOT / "crates/haven_game/src/runtime_structural_cliff_draw.rs"
    ).read_text(encoding="utf-8")
    start = source.index("fn south_face_module_anchors")
    end = source.index("fn draw_south_face_module", start)
    block = source[start:end]
    require("if length % 2 != 0" in block, "stable signed parity expression")
    require("length.is_multiple_of(2)" not in block, "unsupported signed method removed")
    require("if length < 2" in block, "positive-domain early return retained")
    require(
        "authored_south_face_modules_never_emit_single_cell_fragments" in source,
        "existing module geometry regression test retained",
    )
    require("allow(" not in block, "no local lint or compiler allowance")

    doc = (
        ROOT / "docs/archive/pass_history/PASS167Z94_RUST_TOOLCHAIN_CLIFF_RENDERER_COMPATIBILITY.md"
    ).read_text(encoding="utf-8")
    require("continuous Alderreach World Editor" in doc, "next editor lane")
    print("Pass167Z94 Rust toolchain cliff renderer compatibility validation passed")


if __name__ == "__main__":
    main()
