#!/usr/bin/env python3
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[5]
errors = []

required = [
    "crates/haven_world/src/world_paint_material_state.rs",
    "content/assets/world_paint/world_paint_material_state_contract_v0_1.json",
    "content/schemas/world_paint_material_state_contract.schema.v0_1.json",
    "docs/assets/WORLD_PAINT_MATERIAL_STATE_LAYER_PASS33.md",
]
for rel in required:
    if not (ROOT / rel).exists():
        errors.append(f"missing {rel}")

contract_path = ROOT / "content/assets/world_paint/world_paint_material_state_contract_v0_1.json"
if contract_path.exists():
    data = json.loads(contract_path.read_text(encoding="utf-8"))
    if data.get("canonical_tile_size") != [32, 32]:
        errors.append("material state contract must lock canonical_tile_size [32,32]")
    for mode in ["32x32", "16x16", "8x8", "4x4"]:
        if mode not in [entry.get("code") for entry in data.get("subcell_modes", [])]:
            errors.append(f"missing subcell mode {mode}")
    for family in ["sand", "water", "cave", "paved_brick", "wood_plank"]:
        if family not in data.get("families", []):
            errors.append(f"missing family {family}")

world_lib = (ROOT / "crates/haven_world/src/lib.rs").read_text(encoding="utf-8")
if "world_paint_material_state" not in world_lib:
    errors.append("haven_world lib.rs does not export world_paint_material_state")

state_src = (ROOT / "crates/haven_world/src/world_paint_material_state.rs").read_text(encoding="utf-8")
for token in [
    "WorldPaintMaterialStateDocument",
    "WorldPaintMaterialCell",
    "weights_u8",
    "apply_world_paint_delta_record_to_material_state_path",
    "validate_world_paint_material_state_document",
]:
    if token not in state_src:
        errors.append(f"world_paint_material_state.rs missing {token}")

runtime_config = (ROOT / "crates/haven_game/src/runtime_config.rs").read_text(encoding="utf-8")
if "WORLD_PAINT_MATERIAL_STATE_PATH" not in runtime_config:
    errors.append("runtime_config.rs missing WORLD_PAINT_MATERIAL_STATE_PATH")

panel = (ROOT / "crates/haven_game/src/world_paint_editor_panel.rs").read_text(encoding="utf-8")
if "apply_world_paint_delta_record_to_material_state_path" not in panel:
    errors.append("paint panel does not update material state after painting")
if "WORLD_PAINT_MATERIAL_STATE_PATH" not in panel:
    errors.append("paint panel does not use material state path")

if errors:
    print("Validate-WorldPaintMaterialStateLayerV40 FAILED")
    for error in errors:
        print(f" - {error}")
    sys.exit(1)

print("Validate-WorldPaintMaterialStateLayerV40 passed")
