#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[5]
def require(text: str, token: str, label: str) -> None:
    if token not in text:
        raise SystemExit(f"missing {label}: {token}")


mapping = json.loads(
    (ROOT / "content/assets/intake/lpc_terrain_family_mapping_v0_3.json").read_text(encoding="utf-8")
)
for tile_id, expected in [("shallow_water", [[1, 21]] * 4), ("deep_water", [[1, 24]] * 4)]:
    if mapping["baseTiles"][tile_id]["cells"] != expected:
        raise SystemExit(f"{tile_id} does not use its reviewed authored repeat center")

transition_manifest = json.loads(
    (ROOT / "assets/generated/worldgen_v0_1/terrain/terrain_autotile_47_32.json").read_text(encoding="utf-8")
)
if transition_manifest.get("version") != "0.4.0":
    raise SystemExit("transition atlas manifest was not promoted to v0.4.0")
if transition_manifest.get("source") != "tools/automation/terrain/Promote-LpcTerrainFamiliesV90.py":
    raise SystemExit("transition atlas does not identify the Pass 90 baker")
if len(transition_manifest.get("variants", [])) != 112:
    raise SystemExit("transition atlas does not contain seven complete 16-mask families")

transition_image = Image.open(ROOT / transition_manifest["output"]).convert("RGBA")
alpha = list(transition_image.getchannel("A").tobytes())
if not any(value == 0 for value in alpha) or not any(value > 0 for value in alpha):
    raise SystemExit("transition atlas does not preserve transparent authored overlays")

save_text = (ROOT / "crates/haven_save/src/lib.rs").read_text(encoding="utf-8")
frontend_text = (ROOT / "crates/haven_game/src/client_frontend.rs").read_text(encoding="utf-8")
frontend_text += (ROOT / "crates/haven_game/src/client_frontend_modals.rs").read_text(encoding="utf-8")
editor_render_text = (ROOT / "apps/haven_editor_native/src/app/atlas_render.rs").read_text(encoding="utf-8")
game_render_text = (ROOT / "crates/haven_game/src/terrain_render.rs").read_text(encoding="utf-8")

require(save_text, "CURRENT_CLIENT_GENERATION_VERSION: u32 = 3", "save generation version")
require(save_text, "generation_version: CURRENT_CLIENT_GENERATION_VERSION", "new-save generation metadata")
for token in [
    "FrontendModal::Regenerate",
    "SlotMenuAction::Regenerate",
    "Update World",
    "Regenerate generated world?",
    "create_seeded_client_save(&self.save_root, slot, seed)",
]:
    require(frontend_text, token, "client save regeneration workflow")
require(editor_render_text, "editor_transition_tint", "editor transition tint")
require(editor_render_text, "Normalized LPC transition cells already carry their authored color", "editor authored-color contract")
require(game_render_text, "Pass 90 stores authored LPC color and alpha directly", "runtime authored-color contract")

build_sh = (ROOT / "tools/build/Build.sh").read_text(encoding="utf-8")
build_ps1 = (ROOT / "tools/build/Build.ps1").read_text(encoding="utf-8")
require(build_sh, "Promote-LpcTerrainFamiliesV90.py", "Bash tile baker")
require(build_ps1, "Promote-LpcTerrainFamiliesV90.py", "PowerShell tile baker")

for preview in [
    "docs/assets/previews/havenwild_lpc_water_variants_pass86.png",
    "docs/assets/previews/havenwild_transition_contours_pass86.png",
    "docs/assets/previews/havenwild_lpc_terrain_family_foundation_pass90.png",
]:
    if not (ROOT / preview).is_file():
        raise SystemExit(f"missing retained terrain preview: {preview}")

print("LPC terrain foundation and client-save regeneration validation V85 passed")
