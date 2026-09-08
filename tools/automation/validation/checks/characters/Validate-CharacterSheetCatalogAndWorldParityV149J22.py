from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
def require(path: str, token: str, label: str) -> None:
    text = (ROOT / path).read_text(encoding="utf-8")
    if token not in text:
        raise SystemExit(f"J22 missing {label}: {path} -> {token}")

require("tools/automation/characters/Build-LpcPlayerAtlas.py", "lpc_character_sheet_catalog_v0_1.json", "full LPC character sheet catalog")
require("tools/automation/characters/Build-LpcPlayerAtlas.py", "selectedByStarterCreator", "catalog starter selection provenance")
require("crates/haven_game/src/character_runtime_compositor.rs", "profile_path(save_root, character_id)", "shared profile path")
require("crates/haven_game/src/character_runtime_compositor.rs", ".parent()\n        .unwrap_or(save_root)", "WORKSPACE profile root")
require("crates/haven_game/src/character_runtime_compositor.rs", "layer.asset.pack_id == \"havenwild_starter_character\"", "generated starter layer priority")
require("crates/haven_game/src/character_runtime_compositor.rs", "appearance_occludes_slot(&appearance, \"hair\")", "runtime hood occlusion")
require("crates/haven_game/src/client_character_frontend_draw.rs", "hood_occludes_hair", "creator hood occlusion")
require("crates/haven_game/src/character_creator_model.rs", "Hood hides the hair layer", "creator compatibility explanation")
print("Pass 149J22 full LPC character-sheet catalog, hood occlusion, and creator/runtime parity validated")
