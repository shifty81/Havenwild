#!/usr/bin/env python3
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[5]
required = [
    "crates/haven_core/src/foundation/authored_entities.rs",
    "crates/haven_core/src/foundation.rs",
    "crates/haven_assets/src/placeable_asset_registry.rs",
    "crates/haven_assets/src/asset_browser.rs",
    "crates/haven_editor/src/scene_edit.rs",
    "apps/haven_editor_native/src/app/asset_library_panel.rs",
    "apps/haven_editor_native/src/app/scene_authoring.rs",
    "crates/haven_game/src/runtime_editor_shell.rs",
    "crates/haven_game/src/runtime_input.rs",
    "content/asset_packs/placeable_persistence_policy_v1.json",
]
for rel in required:
    if not (ROOT / rel).is_file():
        raise SystemExit(f"missing required Pass 148N file: {rel}")

policy = json.loads((ROOT / required[-1]).read_text(encoding="utf-8"))
assert policy["schema"] == "havenwild.placeable_persistence_policy.v1"
assert policy["requirements"]["new_placeables_require_legacy_object_kind"] is False

core = (ROOT / "crates/haven_core/src/foundation.rs").read_text(encoding="utf-8")
entities = (ROOT / "crates/haven_core/src/foundation/authored_entities.rs").read_text(encoding="utf-8")
registry = (ROOT / "crates/haven_assets/src/placeable_asset_registry.rs").read_text(encoding="utf-8")
browser = (ROOT / "crates/haven_assets/src/asset_browser.rs").read_text(encoding="utf-8")
editor = (ROOT / "apps/haven_editor_native/src/app/scene_authoring.rs").read_text(encoding="utf-8")
f3 = (ROOT / "crates/haven_game/src/runtime_editor_shell.rs").read_text(encoding="utf-8")

checks = {
    "stable placeable ref contract": "pub struct StablePlaceableAssetRef" in entities,
    "save sidecar record": '"object_asset {} {} {} {} {} {}\\n"' in core,
    "save sidecar parser": 'parts[0] == "object_asset"' in core,
    "pack-defined placement API": "place_pack_defined_object" in core,
    "registry persistent conversion": "persistent_ref" in registry,
    "generic compatibility fallback": "compatibility_kind" in registry,
    "content browser placeable entries": "placeable_stable_id" in browser,
    "native editor data-driven placement": "place_scene_pack_asset" in editor,
    "F3 pack-defined placement": "place_pack_defined_object" in f3,
    "F3 provider cycling": "selected_placeable_index" in f3 or "selected_placeable_index" in (ROOT / "crates/haven_game/src/runtime_input.rs").read_text(encoding="utf-8"),
}
failed = [name for name, ok in checks.items() if not ok]
if failed:
    raise SystemExit("Pass 148N validation failed: " + "; ".join(failed))
print("Pass 148N generic placeable persistence valid: stable save refs, data-driven native/F3 selection, legacy compatibility retained")
