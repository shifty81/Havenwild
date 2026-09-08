#!/usr/bin/env python3
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[5]
required = [
    "crates/haven_core/src/foundation.rs",
    "crates/haven_core/src/foundation/map_serialization.rs",
    "crates/haven_assets/src/placeable_asset_registry.rs",
    "crates/haven_game/src/runtime_assets.rs",
    "crates/haven_game/src/runtime_object_draw.rs",
    "crates/haven_game/src/runtime_interactions.rs",
    "content/asset_packs/havenwild_objects/published_world_assets_v1.json",
    "content/asset_packs/placeable_runtime_dispatch_policy_v1.json",
]
for rel in required:
    if not (ROOT / rel).is_file():
        raise SystemExit(f"missing required Pass 148O file: {rel}")

policy = json.loads((ROOT / required[-1]).read_text(encoding="utf-8"))
catalog = json.loads((ROOT / required[-2]).read_text(encoding="utf-8"))
core = (ROOT / required[0]).read_text(encoding="utf-8")
serialization = (ROOT / required[1]).read_text(encoding="utf-8")
registry = (ROOT / required[2]).read_text(encoding="utf-8")
assets = (ROOT / required[3]).read_text(encoding="utf-8")
draw = (ROOT / required[4]).read_text(encoding="utf-8")
interactions = (ROOT / required[5]).read_text(encoding="utf-8")

checks = {
    "policy schema": policy.get("schema") == "havenwild.placeable_runtime_dispatch_policy.v1",
    "stable render authority": policy["requirements"]["stable_asset_ref_is_render_authority"] is True,
    "stable interaction authority": policy["requirements"]["stable_asset_ref_is_interaction_authority"] is True,
    "object state save record": '"object_state {} {}\\n"' in serialization,
    "object state parser": 'parts[0] == "object_state"' in serialization,
    "entry-specific persistent identity": "self.entry_id.clone()" in registry,
    "persistent ref resolver": "resolve_persistent_ref" in registry,
    "visual frame contract": "PlaceableVisualFrame" in registry,
    "interaction action contract": "PlaceableInteractionAction" in registry,
    "stable placeable texture map": "placeable_textures" in assets,
    "stable render lookup": "resolve_persistent_ref(asset_ref)" in draw,
    "state-based render frame": "frame_for_state(state)" in draw,
    "stable interaction dispatch": "dispatch_placeable_interaction" in interactions,
    "legacy draw fallback retained": "object_asset_entry_for_cell(object.kind" in draw,
}
for entry in catalog.get("entries", []):
    checks[f"{entry.get('id')} interaction"] = isinstance(entry.get("interaction"), dict)
    if entry.get("id") != "cave_entrance_default":
        checks[f"{entry.get('id')} visual"] = bool(entry.get("visual", {}).get("frames"))

failed = [name for name, ok in checks.items() if not ok]
if failed:
    raise SystemExit("Pass 148O validation failed: " + "; ".join(failed))
print("Pass 148O stable placeable runtime dispatch valid: stable rendering, saved state, metadata interactions, explicit legacy fallback")
