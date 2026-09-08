from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[5]
contract = json.loads((ROOT / "content/animations/character_animation_contract_v0_10.json").read_text(encoding="utf-8"))
runtime = contract["runtime_compositor_v149i"]
assert runtime["appearance_source"] == "persistent character profile"
assert runtime["walk_frames"] == 8
assert runtime["fallback_order"][0] == "saved layered appearance"
source = (ROOT / "crates/haven_game/src/character_runtime_compositor.rs").read_text(encoding="utf-8")
for token in ["RuntimeCharacterAppearance", "CharacterAnimationFrame", "body/base", "clothing/torso", "clothing/legs", "clothing/feet", "load_character_profile"]:
    assert token in source, token
main = (ROOT / "crates/haven_game/src/main.rs").read_text(encoding="utf-8")
draw = (ROOT / "crates/haven_game/src/runtime_draw.rs").read_text(encoding="utf-8")
assert "runtime_character_appearance" in main
assert "RuntimeCharacterAppearance::frame" in draw
print("Pass 149I animated character runtime contract validated")
