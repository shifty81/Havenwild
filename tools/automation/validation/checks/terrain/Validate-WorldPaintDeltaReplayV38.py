#!/usr/bin/env python3
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[5]
errors = []

required_files = [
    ROOT / "crates/haven_world/src/world_paint_replay.rs",
    ROOT / "crates/haven_world/src/world_paint.rs",
    ROOT / "crates/haven_world/src/world_paint_delta.rs",
    ROOT / "crates/haven_game/src/world_paint_editor_panel.rs",
    ROOT / "content/assets/world_paint/world_paint_delta_replay_contract_v0_1.json",
    ROOT / "content/schemas/world_paint_delta_replay_contract.schema.v0_1.json",
    ROOT / "docs/assets/WORLD_PAINT_DELTA_REPLAY_PASS31.md",
]
for path in required_files:
    if not path.exists():
        errors.append(f"missing required file: {path.relative_to(ROOT)}")

contract_path = ROOT / "content/assets/world_paint/world_paint_delta_replay_contract_v0_1.json"
if contract_path.exists():
    contract = json.loads(contract_path.read_text())
    if contract.get("schema") != "havenwild.world_paint_delta_replay_contract.v0.1":
        errors.append("replay contract schema mismatch")
    if contract.get("canonicalTileSize") != [32, 32]:
        errors.append("replay contract must lock canonicalTileSize [32,32]")
    for scope in ["active_scene", "all_scenes"]:
        if scope not in contract.get("replayScope", []):
            errors.append(f"replay contract missing scope {scope}")
    for key in ["scene_id", "center", "family", "subcell_mode", "mirror_horizontal", "mirror_vertical"]:
        if key not in contract.get("authoritativeInputs", []):
            errors.append(f"replay contract authoritativeInputs missing {key}")
    if not any("foam" in value for value in contract.get("derivedClientOutputs", [])):
        errors.append("replay contract should keep foam as client-derived output")

replay_rs = (ROOT / "crates/haven_world/src/world_paint_replay.rs").read_text() if (ROOT / "crates/haven_world/src/world_paint_replay.rs").exists() else ""
for token in [
    "WorldPaintReplayReport",
    "WorldPaintReplayIssue",
    "replay_world_paint_delta_document_onto_world",
    "replay_world_paint_delta_record_onto_map",
    "load_and_replay_world_paint_deltas",
    "apply_world_paint_brush",
    "SceneId::from_code",
]:
    if token not in replay_rs:
        errors.append(f"world_paint_replay.rs missing token {token}")

world_paint_rs = (ROOT / "crates/haven_world/src/world_paint.rs").read_text() if (ROOT / "crates/haven_world/src/world_paint.rs").exists() else ""
if world_paint_rs.count("pub fn from_code(code: &str) -> Option<Self>") < 3:
    errors.append("world_paint.rs must expose from_code helpers for family, layer, and subcell mode")

lib_rs = (ROOT / "crates/haven_world/src/lib.rs").read_text() if (ROOT / "crates/haven_world/src/lib.rs").exists() else ""
for token in ["pub mod world_paint_replay;", "pub use world_paint_replay::*;"]:
    if token not in lib_rs:
        errors.append(f"haven_world lib.rs missing {token}")

panel_rs = (ROOT / "crates/haven_game/src/world_paint_editor_panel.rs").read_text() if (ROOT / "crates/haven_game/src/world_paint_editor_panel.rs").exists() else ""
for token in ["replay_world_paint_deltas", "load_and_replay_world_paint_deltas", "ReplayAll", "KeyCode::T"]:
    if token not in panel_rs:
        errors.append(f"world_paint_editor_panel.rs missing replay UI token {token}")

main_rs = (ROOT / "crates/haven_game/src/main.rs").read_text() if (ROOT / "crates/haven_game/src/main.rs").exists() else ""
if "load_and_replay_world_paint_deltas" not in main_rs:
    errors.append("main.rs must import load_and_replay_world_paint_deltas")

if errors:
    print("Validate-WorldPaintDeltaReplayV38 FAILED")
    for e in errors:
        print(" -", e)
    sys.exit(1)
print("Validate-WorldPaintDeltaReplayV38 passed")
