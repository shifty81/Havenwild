#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(
            f"FAILED Pass167Z95 cliff renderer strict-Clippy compatibility: {message}"
        )


def main() -> None:
    quarantine = ROOT / "content/build/runtime_asset_integrity_cliff_quarantine_v167z96.json"
    if quarantine.is_file():
        contract = json.loads(quarantine.read_text(encoding="utf-8"))
        require(contract["pass"] == "167Z96", "Z96 quarantine pass")
        source = (ROOT / "crates/haven_game/src/runtime_structural_cliff_draw.rs").read_text(encoding="utf-8")
        require("while anchor + 1 <= end_x" not in source, "old int-plus-one form absent")
        require("is_multiple_of" not in source, "unsupported parity API absent")
        current = ROOT / "content/worldgen/structural_cliff_autotile_authority_v0_1.json"
        if current.is_file():
            active = json.loads(current.read_text(encoding="utf-8-sig"))
            if active.get("pass") in {"167Z107", "167Z109C", "167Z109D", "167Z109G"} and active.get("status") == "active":
                require("draw_texture_ex" in source, "active structural cliff renderer draws through supported API")
                print(f"Pass167Z95 compatibility remains satisfied under {active.get('pass')} structural cliff supersession")
                return
        z106 = ROOT / "content/worldgen/elizawy_cliff_runtime_preview_certification_v0_1.json"
        if z106.is_file():
            preview = json.loads(z106.read_text(encoding="utf-8"))
            require(preview["pass"] == "167Z106", "Z106 preview pass")
            require(preview["runtimeGate"]["collision"] == "fail_open", "Z106 collision remains fail-open")
            require("draw_texture_ex" in source, "certified ElizaWy preview renderer active")
            print("Pass167Z95 compatibility remains satisfied under Pass167Z106 certified preview supersession")
        else:
            require("pub(super) fn draw_structural_cliffs(&self) {}" in source, "invalid runtime renderer quarantined")
            print("Pass167Z95 compatibility remains satisfied under Pass167Z96 quarantine")
        return
    contract = json.loads(
        (
            ROOT
            / "content/build/cliff_renderer_strict_clippy_compatibility_v167z95.json"
        ).read_text(encoding="utf-8")
    )
    require(
        contract["schema"]
        == "havenwild.build.cliff_renderer_strict_clippy_compatibility.v0_1",
        "schema",
    )
    require(contract["pass"] == "167Z95", "pass")
    require(contract["repair"]["lintSuppressionAdded"] is False, "no lint suppression")
    require(
        contract["repair"]["runtimeBehaviorChanged"] is False,
        "runtime behavior unchanged",
    )

    source = (
        ROOT / "crates/haven_game/src/runtime_structural_cliff_draw.rs"
    ).read_text(encoding="utf-8")
    start = source.index("fn south_face_module_anchors")
    end = source.index("fn draw_south_face_module", start)
    block = source[start:end]
    require("while anchor < end_x" in block, "Clippy-compatible loop condition")
    require("while anchor + 1 <= end_x" not in block, "old int-plus-one form removed")
    require("anchor += 2" in block, "two-cell module step retained")
    require("if length % 2 != 0" in block, "odd-length fallback retained")
    require("let final_anchor = end_x - 1" in block, "final complete pair retained")
    require("allow(" not in block, "no local lint allowance")

    doc = (
        ROOT
        / "docs/archive/pass_history/PASS167Z95_CLIFF_RENDERER_STRICT_CLIPPY_COMPATIBILITY.md"
    ).read_text(encoding="utf-8")
    require("continuous Alderreach World Editor" in doc, "next editor lane")
    print("Pass167Z95 cliff renderer strict-Clippy compatibility validation passed")


if __name__ == "__main__":
    main()
