#!/usr/bin/env python3
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[5]
def require(text: str, token: str, label: str) -> None:
    if token not in text:
        raise SystemExit(f"missing {label}: {token}")

save = (ROOT / "crates/haven_save/src/lib.rs").read_text(encoding="utf-8")
frontend = (ROOT / "crates/haven_game/src/client_frontend.rs").read_text(encoding="utf-8")
frontend += (ROOT / "crates/haven_game/src/client_frontend_modals.rs").read_text(encoding="utf-8")
frontend += (ROOT / "crates/haven_game/src/client_character_frontend_draw.rs").read_text(encoding="utf-8")
generation = (ROOT / "crates/haven_game/src/client_save_generation.rs").read_text(encoding="utf-8")
main = (ROOT / "crates/haven_game/src/main.rs").read_text(encoding="utf-8")
main += (ROOT / "crates/haven_game/src/client_entry.rs").read_text(encoding="utf-8")
persistence = (ROOT / "crates/haven_game/src/runtime_persistence.rs").read_text(encoding="utf-8")
paint = (ROOT / "crates/haven_game/src/world_paint_editor_panel.rs").read_text(encoding="utf-8")
build = (ROOT / "tools/build/Build.sh").read_text(encoding="utf-8")
contract_path = ROOT / "content/ui/client_save_slot_contract_v0_1.json"
contract = json.loads(contract_path.read_text(encoding="utf-8"))

require(save, "CLIENT_SAVE_SLOT_COUNT: usize = 3", "three-slot constant")
for token in ["Slot1", "Slot2", "Slot3", "slot_1", "slot_2", "slot_3"]:
    require(save, token, "client slot identity")
for token in ["slot.json", "world.tworld", "scene_rectangle_manifest.json", "world_paint_deltas.json"]:
    require(save, token, "per-slot file")
for token in ["New Game", "Play", "Delete Save", "World seed"]:
    require(frontend, token, "client menu action")
for token in ["world_folder_rect", "open_folder", "Folder"]:
    require(frontend, token, "open-save-folder capability")
for token in ["generate_archipelago_layout", "generate_landmass", "GameWorld::starter", "world.scenes.len()"]:
    require(generation, token, "seeded client generation")
require(main, "ClientFrontend::new()", "client frontend boot")
require(main, "Game::new(", "selected-world game launch")
require(persistence, "self.save_paths.world", "slot-specific world persistence")
require(paint, "self.save_paths.world_paint_delta", "slot-specific paint deltas")
require(build, "Package an empty save root", "clean release save packaging")
if "cp -a WORKSPACE/saves/." in build:
    raise SystemExit("tools/build/Build.sh still packages development gameplay saves")

editor_root = ROOT / "apps/haven_editor_native/src"
for path in editor_root.rglob("*.rs"):
    text = path.read_text(encoding="utf-8")
    if "ClientSaveSlot" in text or "slot_1" in text:
        raise SystemExit(f"native editor incorrectly owns gameplay slots: {path.relative_to(ROOT)}")

if contract.get("owner") != "HavenwildClient" or contract.get("slot_count") != 3:
    raise SystemExit("client save-slot contract ownership/count is incorrect")
if "does not own gameplay save slots" not in contract.get("editor_ownership", ""):
    raise SystemExit("client save-slot contract does not separate editor ownership")

print("Client save slots V74 validation passed")
