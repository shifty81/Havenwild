from pathlib import Path
import json

root = Path(__file__).resolve().parents[5]
contract = json.loads((root / "content/characters/starter_character_creator_v149h.json").read_text())
assert contract["base_body_policy"]["clothing_baked_into_body"] is False
assert set(contract["base_body_policy"]["variants"]) == {"male_neutral", "female_neutral"}
model = (root / "crates/haven_game/src/character_creator_model.rs").read_text()
frontend = (root / "crates/haven_game/src/client_frontend.rs").read_text()
draw = (root / "crates/haven_game/src/client_character_frontend_draw.rs").read_text()
for token in ["neutral_base_body", "starter_tshirt", "starter_pants", "starter_boots", "starter_skirt", "starter_shoes"]:
    assert token in model, token
for token in ["get_char_pressed", "creator_body_rect", "creator_color_rect", "sync_creator_appearance"]:
    assert token in frontend, token
assert "draw_layered_starter_preview" in draw
print("Pass 149H interactive character creator contract validated")
