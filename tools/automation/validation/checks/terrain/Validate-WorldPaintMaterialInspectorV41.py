#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
errors: list[str] = []

required_files = [
    "crates/haven_world/src/world_paint_material_state.rs",
    "crates/haven_game/src/world_paint_editor_panel.rs",
    "crates/haven_game/src/main.rs",
    "content/assets/world_paint/world_paint_material_inspector_contract_v0_1.json",
    "content/schemas/world_paint_material_inspector_contract.schema.v0_1.json",
    "docs/assets/WORLD_PAINT_MATERIAL_INSPECTOR_PASS34.md",
]
for rel in required_files:
    if not (ROOT / rel).exists():
        errors.append(f"missing required file: {rel}")

state_rs = (ROOT / "crates/haven_world/src/world_paint_material_state.rs").read_text()
for token in [
    "WorldPaintMaterialCellInspection",
    "inspect_world_paint_material_cell(",
    "inspect_world_paint_material_cell_path(",
    "ready_for_adjacency",
    "ready_for_debris",
    "status_line(&self)",
]:
    if token not in state_rs:
        errors.append(f"world_paint_material_state.rs missing {token}")

panel_rs = (ROOT / "crates/haven_game/src/world_paint_editor_panel.rs").read_text()
draw_path = ROOT / "crates/haven_game/src/world_paint_editor_draw.rs"
if draw_path.exists():
    panel_rs += "\n" + draw_path.read_text()
for token in [
    "inspect_selected_world_paint_material_cell",
    "Inspect",
    "KeyCode::I",
    "world_paint_inspector_status",
    "world_paint_inspector",
    "Cell material state:",
]:
    if token not in panel_rs:
        errors.append(f"world_paint_editor_panel.rs missing {token}")

main_rs = (ROOT / "crates/haven_game/src/main.rs").read_text()
for token in [
    "inspect_world_paint_material_cell_path",
    "WorldPaintMaterialCellInspection",
    "world_paint_inspector_status",
    "world_paint_inspector: None",
]:
    if token not in main_rs:
        errors.append(f"main.rs missing {token}")

contract_path = ROOT / "content/assets/world_paint/world_paint_material_inspector_contract_v0_1.json"
try:
    contract = json.loads(contract_path.read_text())
    if contract.get("schema") != "havenwild.world_paint_material_inspector_contract.v0.1":
        errors.append("inspector contract schema id mismatch")
    controls = contract.get("paint_tab_controls", [])
    if not any(c.get("label") == "Inspect" for c in controls if isinstance(c, dict)):
        errors.append("inspector contract missing Inspect button control")
    if not any(c.get("hotkey") == "I" for c in controls if isinstance(c, dict)):
        errors.append("inspector contract missing I hotkey control")
    selected = contract.get("selected_cell_inspection", {})
    for field in ["entries", "readiness_flags", "display_fields"]:
        if field not in selected:
            errors.append(f"inspector contract missing selected_cell_inspection.{field}")
except Exception as exc:
    errors.append(f"failed to parse inspector contract: {exc}")

if errors:
    print("Validate-WorldPaintMaterialInspectorV41 FAILED")
    for err in errors:
        print(f" - {err}")
    raise SystemExit(1)

print("Validate-WorldPaintMaterialInspectorV41 passed")
print("Checked selected-cell material-state inspection, Paint tab Inspect/I control, and modular contract files.")
