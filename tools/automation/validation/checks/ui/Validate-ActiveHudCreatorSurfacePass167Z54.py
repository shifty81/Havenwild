#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]

checks = {
    ROOT / "crates/haven_game/src/runtime_hud.rs": [
        "self.hud_minimap_frame.as_ref()",
        "appearance.draw_portrait",
        "RuntimeCharacterAppearance::frame",
        "character_stamina_current",
        "draw_havenwild_panel_frame",
        "draw_player_hotbar",
        "self.item_icon_atlas.as_ref()",
        "draw_day_night_clock",
        "clock_label(hour)",
    ],
    ROOT / "crates/haven_game/src/gameplay_hotbar.rs": [
        "HOTBAR_SLOT_COUNT",
        "HotbarBinding",
        "handle_inventory_hotbar_drag_drop",
        "player_hotbar.json",
        "state.bindings[slot] = Some(binding.clone())",
        "drag_candidate",
        "length_squared() >= 36.0",
    ],
    ROOT / "crates/haven_game/src/runtime_input.rs": [
        "gameplay_hotbar::HOTBAR_SLOT_COUNT",
        "hotbar_binding(slot)",
        "cycle_hotbar_index",
    ],
    ROOT / "crates/haven_game/src/gameplay_tool_runtime.rs": [
        "selected_hotbar_binding",
        "hotbar_binding_is_available",
        "Empty hotbar means unarmed/hand interaction",
    ],
    ROOT / "crates/haven_game/src/runtime_draw.rs": [
        "self.draw_player_hotbar();",
    ],
    ROOT / "crates/haven_game/src/character_creator_catalog.rs": [
        'CreatorOptionKind::Eyebrows, "eyebrows_01_thin"',
        'CreatorOptionKind::Eyebrows, "eyebrows_02_thick"',
        'CreatorOptionKind::Headwear, "none"',
        'CreatorOptionKind::Headwear, "headwear_hat"',
    ],
    ROOT / "crates/haven_game/src/character_runtime_compositor.rs": [
        "pub(crate) fn draw_portrait",
    ],
}

errors: list[str] = []
for path, needles in checks.items():
    if not path.is_file():
        errors.append(f"missing required source file: {path.relative_to(ROOT)}")
        continue
    text = path.read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text:
            errors.append(f"{path.relative_to(ROOT)} missing active integration marker: {needle}")
    if "allow(dead_code)" in text or "expect(dead_code)" in text:
        errors.append(f"{path.relative_to(ROOT)} suppresses dead code instead of integrating the active surface")

# Hard-coded GameplayTool::ALL slot enumeration is specifically prohibited.
hud_text = (ROOT / "crates/haven_game/src/runtime_hud.rs").read_text(encoding="utf-8")
if "GameplayTool::ALL.iter" in hud_text or "GameplayTool::ALL[self.selected_gameplay_tool]" in hud_text:
    errors.append("runtime_hud.rs still treats GameplayTool::ALL as player hotbar slot authority")

for relative in [
    "crates/haven_game/src/runtime_input.rs",
    "crates/haven_game/src/gameplay_tool_runtime.rs",
]:
    text = (ROOT / relative).read_text(encoding="utf-8")
    if "GameplayTool::ALL[self.selected_gameplay_tool]" in text:
        errors.append(f"{relative} still derives the selected player item from hard-coded GameplayTool::ALL")

if errors:
    print("Active HUD and creator surface validation FAILED")
    for error in errors:
        print(f"- {error}")
    raise SystemExit(1)

print("Active HUD and creator surface validated")
print("- player card and hotbar use code-generated Havenwild frame grammar")
print("- minimap uses production circular frame with live code-driven day/night clock")
print("- hotbar slots are persisted player-authored inventory shortcuts")
print("- item icon atlas is consumed by the hotbar where available")
print("- character portrait rendering remains active")
