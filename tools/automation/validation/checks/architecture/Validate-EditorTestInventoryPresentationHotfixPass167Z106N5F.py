from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
TESTS = ROOT / "crates/haven_editor/src/lib_tests.rs"
SCENE_EDIT = ROOT / "crates/haven_editor/src/scene_edit.rs"
RUNTIME_DRAW = ROOT / "crates/haven_game/src/runtime_draw.rs"
INVENTORY_DRAW = ROOT / "crates/haven_game/src/player_inventory_ui/draw.rs"


def fail(message: str) -> None:
    print(f"FAILED Pass167Z106N5F editor test/inventory presentation hotfix: {message}")
    raise SystemExit(1)


for path in (TESTS, SCENE_EDIT, RUNTIME_DRAW, INVENTORY_DRAW):
    if not path.is_file():
        fail(f"missing {path.relative_to(ROOT)}")

tests = TESTS.read_text(encoding="utf-8")
scene_edit = SCENE_EDIT.read_text(encoding="utf-8")
runtime_draw = RUNTIME_DRAW.read_text(encoding="utf-8")
inventory_draw = INVENTORY_DRAW.read_text(encoding="utf-8")

if "use haven_core::{TavernMap, TileKind};" not in tests:
    fail("haven_editor lib regression tests must import TavernMap and TileKind explicitly")
if "TavernMap::empty_with(TileKind::Grass)" not in tests:
    fail("autotile inspector regression test no longer exercises TavernMap/TileKind")
if "MAP_H, MAP_W" in scene_edit or "MAP_H," in scene_edit:
    fail("scene_edit.rs retained the unused MAP_H import")
if "if self.player_inventory_ui.open" not in runtime_draw:
    fail("runtime draw no longer presents the player inventory when its UI is open")
if "self.player_inventory_ui.draw();" not in runtime_draw:
    fail("runtime draw no longer invokes the inventory presentation owner")
if "self.player_inventory_ui.draw_processing_notifications();" not in runtime_draw:
    fail("runtime draw no longer presents processing notifications")
if "#[allow(dead_code)]\n    pub(crate) fn draw(&self)" in inventory_draw:
    fail("inventory draw path is still marked as dead code instead of being runtime-wired")

print("Pass167Z106N5F editor test/inventory presentation hotfix validated")
