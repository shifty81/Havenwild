#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
required = [
    ROOT / "crates/haven_game/src/character_runtime_compositor.rs",
    ROOT / "crates/haven_game/src/runtime_assets.rs",
    ROOT / "crates/haven_game/src/runtime_texture_cache.rs",
    ROOT / "crates/haven_assets/src/runtime_asset_cache.rs",
    ROOT / "content/characters/production_lpc_runtime_binding_v149j.json",
]
missing = [str(path.relative_to(ROOT)) for path in required if not path.is_file()]
if missing:
    raise SystemExit("missing Pass 149J files: " + ", ".join(missing))
policy = json.loads(required[-1].read_text(encoding="utf-8"))
assert policy["frame_cell"] == [64, 96]
assert policy["source_resolution"] == "stable_asset_ref"
assert policy["production_enabled_packs_only"] is True
compositor = required[0].read_text(encoding="utf-8")
for token in ["load_stable_ref", "draw_texture_ex", "layer_order", "generated_component_path"]:
    assert token in compositor, token
assets = required[1].read_text(encoding="utf-8")
assert "character_appearance" in assets
assert "RuntimeCharacterAppearance::load" in assets
cache = required[2].read_text(encoding="utf-8")
assert "load_stable_ref" in cache
session = required[3].read_text(encoding="utf-8")
assert "source_for_ref" in session
print("Pass 149J production LPC runtime binding contract validated")
