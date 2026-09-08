#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
errors = []

def text(path: str) -> str:
    target = ROOT / path
    if not target.is_file():
        errors.append(f"missing {path}")
        return ""
    return target.read_text(encoding="utf-8")

preview = text("crates/haven_world/src/world_preview.rs")
world_lib = text("crates/haven_world/src/lib.rs")
generation = text("crates/haven_game/src/client_save_generation.rs")
frontend = text("crates/haven_game/src/client_frontend.rs")
pause = text("crates/haven_game/src/client_pause_menu.rs")
main = text("crates/haven_game/src/main.rs")
save = text("crates/haven_save/src/lib.rs")
editor_tree = "\n".join(
    path.read_text(encoding="utf-8")
    for path in (ROOT / "apps/haven_editor_native/src").rglob("*.rs")
)

checks = [
    ("pub mod world_preview;", world_lib, "world preview module is not registered"),
    ("export_archipelago_preview", generation, "new-game generation does not export a preview"),
    ("CLIENT_ARCHIPELAGO_PREVIEW_FILENAME", generation, "client preview path constant is not used"),
    ("generated_island_count", save, "save metadata does not retain island count"),
    ("generated_exterior_scene_count", save, "save metadata does not retain exterior scene count"),
    ("preview_textures", frontend, "slot preview texture cache is missing"),
    ("Texture2D::from_file_with_format", frontend, "slot preview PNG loading is missing"),
    ("Save & Main Menu", pause, "pause menu return action is missing"),
    ("ClientRuntimeFlow::ReturnToMainMenu", main, "runtime does not return to the client menu"),
    ("frontend.refresh_slots();", main, "client menu does not refresh after returning"),
    ("if self.pause_menu_open", pause, "runtime pause gate is missing"),
]
for needle, haystack, message in checks:
    if needle not in haystack:
        errors.append(message)

if "ClientSaveSlot" in editor_tree or "slot_1" in editor_tree:
    errors.append("native editor must not own client gameplay save slots")
if "WORKSPACE/saves/slot_" in editor_tree:
    errors.append("native editor contains direct client-slot paths")
if "worldgen/previews" not in save:
    errors.append("client save paths do not reserve the preview directory")
if "43" not in preview or "rendered_scene_count" not in preview:
    errors.append("preview exporter lacks generated scene coverage reporting")

if errors:
    print("Client save preview/pause menu V75 FAILED")
    for error in errors:
        print(f"- {error}")
    raise SystemExit(1)

print("Client save preview/pause menu V75 passed")
