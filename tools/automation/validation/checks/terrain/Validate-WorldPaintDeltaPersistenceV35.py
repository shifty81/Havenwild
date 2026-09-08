#!/usr/bin/env python3
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[5]
errors = []

required_files = [
    ROOT / "crates/haven_world/src/world_paint_delta.rs",
    ROOT / "crates/haven_world/src/world_paint.rs",
    ROOT / "crates/haven_game/src/world_paint_editor_panel.rs",
    ROOT / "content/assets/world_paint/world_paint_delta_contract_v0_1.json",
    ROOT / "content/schemas/world_paint_delta_contract.schema.v0_1.json",
    ROOT / "WORKSPACE/generated/world_paint/world_paint_deltas_v0_1.json",
    ROOT / "docs/assets/WORLD_PAINT_DELTA_PERSISTENCE_PASS29.md",
]
for path in required_files:
    if not path.exists():
        errors.append(f"missing required file: {path.relative_to(ROOT)}")

contract_path = ROOT / "content/assets/world_paint/world_paint_delta_contract_v0_1.json"
if contract_path.exists():
    contract = json.loads(contract_path.read_text())
    if contract.get("schema") != "havenwild.world_paint_delta_contract.v0.1":
        errors.append("world paint delta contract schema mismatch")
    if contract.get("canonicalTileSize") != [32, 32]:
        errors.append("world paint delta contract must lock canonicalTileSize [32,32]")
    for mode in ["32x32", "16x16", "8x8", "4x4"]:
        if mode not in contract.get("supportedSubcellModes", []):
            errors.append(f"world paint delta contract missing subcell mode {mode}")
    for key in ["sequence", "scene_id", "family", "layer", "subcell_mode", "resolved_tile_kind"]:
        if key not in contract.get("authoritativeState", []):
            errors.append(f"authoritativeState missing {key}")
    if "shoreline_overlay" not in contract.get("clientDerivedState", []):
        errors.append("clientDerivedState should list shoreline_overlay as derived")

initial_delta_path = ROOT / "WORKSPACE/generated/world_paint/world_paint_deltas_v0_1.json"
if initial_delta_path.exists():
    doc = json.loads(initial_delta_path.read_text())
    if doc.get("schema") != "havenwild.world_paint_deltas.v0.1":
        errors.append("initial world paint delta document schema mismatch")
    if doc.get("canonical_tile_size") != [32, 32]:
        errors.append("initial world paint delta document must use canonical_tile_size [32,32]")
    if not isinstance(doc.get("records"), list):
        errors.append("initial world paint delta document records must be a list")

world_delta_rs = (ROOT / "crates/haven_world/src/world_paint_delta.rs").read_text() if (ROOT / "crates/haven_world/src/world_paint_delta.rs").exists() else ""
for token in [
    "WorldPaintDeltaRecord",
    "WorldPaintDeltaDocument",
    "append_world_paint_delta_record",
    "validate_world_paint_delta_document",
    "client_visual_note",
    "host/server authoritative operation log",
]:
    if token not in world_delta_rs:
        errors.append(f"world_paint_delta.rs missing token {token}")

world_paint_rs = (ROOT / "crates/haven_world/src/world_paint.rs").read_text() if (ROOT / "crates/haven_world/src/world_paint.rs").exists() else ""
for token in ["WorldPaintBounds", "changed_bounds", "include(&mut self", "bounds"]:
    if token not in world_paint_rs:
        errors.append(f"world_paint.rs missing changed-bounds token {token}")

lib_rs = (ROOT / "crates/haven_world/src/lib.rs").read_text() if (ROOT / "crates/haven_world/src/lib.rs").exists() else ""
if "world_paint_delta" not in lib_rs:
    errors.append("haven_world lib.rs must export world_paint_delta")

panel_rs = (ROOT / "crates/haven_game/src/world_paint_editor_panel.rs").read_text() if (ROOT / "crates/haven_game/src/world_paint_editor_panel.rs").exists() else ""
for token in ["WorldPaintDeltaRecord::from_report", "append_world_paint_delta_record", "WORLD_PAINT_DELTA_PATH", "world_paint_delta_status", "world_paint_edit_sequence"]:
    if token not in panel_rs:
        errors.append(f"world_paint_editor_panel.rs missing token {token}")

main_rs = (ROOT / "crates/haven_game/src/main.rs").read_text() if (ROOT / "crates/haven_game/src/main.rs").exists() else ""
for token in ["world_paint_delta_status", "world_paint_edit_sequence", "WorldPaintDeltaRecord"]:
    if token not in main_rs:
        errors.append(f"main.rs missing token {token}")

runtime_config = (ROOT / "crates/haven_game/src/runtime_config.rs").read_text() if (ROOT / "crates/haven_game/src/runtime_config.rs").exists() else ""
if "WORLD_PAINT_DELTA_PATH" not in runtime_config:
    errors.append("runtime_config.rs missing WORLD_PAINT_DELTA_PATH")

if errors:
    print("Validate-WorldPaintDeltaPersistenceV35 FAILED")
    for e in errors:
        print(" -", e)
    sys.exit(1)
print("Validate-WorldPaintDeltaPersistenceV35 passed")
