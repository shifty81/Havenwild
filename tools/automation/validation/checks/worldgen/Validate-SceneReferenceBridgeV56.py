#!/usr/bin/env python3
from pathlib import Path
import json
import sys

root = Path(__file__).resolve().parents[5]
errors = []

def require(rel: str) -> str:
    path = root / rel
    if not path.exists():
        errors.append(f"missing {rel}")
        return ""
    return path.read_text(encoding="utf-8")

scene_identity = require("crates/haven_core/src/scene_identity.rs")
foundation = (
    require("crates/haven_core/src/foundation.rs")
    + "\n"
    + require("crates/haven_core/src/foundation/authored_entities.rs")
    + "\n"
    + require("crates/haven_core/src/foundation/scene_world.rs")
)
loader = require("crates/haven_core/src/worldgen_loader.rs")
navigation = require("crates/haven_game/src/runtime_scene_navigation.rs")
runtime_editor = require("crates/haven_game/src/runtime_editor_shell.rs")
replay = require("crates/haven_world/src/world_paint_replay.rs")
contract_text = require("content/editor/scene_identity/scene_identity_migration_contract_v0_1.json")
require("docs/editor/SCENE_REFERENCE_RUNTIME_BRIDGE_PASS46.md")

checks = [
    ("pub struct SceneReference", scene_identity, "SceneReference type missing"),
    ("current_stage: \"scene_registry_foundation_normalization\"", scene_identity, "Rust migration plan stage was not advanced"),
    ("transition_targets_migrated: true", scene_identity, "Rust migration plan does not mark transition targets migrated"),
    ("pub target: SceneReference", foundation, "Transition target is not SceneReference-backed"),
    ("pub active_scene: SceneReference", foundation, "GameWorld active_scene is not SceneReference-backed"),
    ("pub fn scene_by_reference", foundation, "GameWorld scene reference lookup missing"),
    ("pub fn set_active_scene", foundation, "guarded active scene setter missing"),
    ("SceneReference::from(normalize_code(target_code))", loader, "worldgen loader does not retain project scene references"),
    ("scenes.contains(transition.target.project_id())", loader, "worldgen loader does not validate project scene references against the registry"),
    ("Transition blocked:", navigation, "runtime transition guard missing"),
    ("target: target.into()", runtime_editor, "runtime transition authoring still stores a legacy SceneId directly"),
    ("SceneReference::from(header_parts[3])", foundation, "line-save active scene loading still requires the legacy enum"),
    ("target: SceneReference::from(next_parts[x_index + 4])", foundation, "line-save transition loading still requires the legacy enum"),
    ("Option<SceneReference>", replay, "world paint replay still filters only by legacy SceneId"),
]
for needle, text, message in checks:
    if needle not in text:
        errors.append(message)

try:
    contract = json.loads(contract_text)
    if contract.get("currentStage") not in {"scene_reference_runtime_bridge", "scene_registry_foundation_normalization"}:
        errors.append("scene identity contract stage was not advanced")
    if contract.get("bridgeReferenceType") != "SceneReference":
        errors.append("scene identity contract bridgeReferenceType mismatch")
    if contract.get("transitionTargetsMigrated") is not True:
        errors.append("contract does not mark transition targets migrated")
    if contract.get("activeSceneReferenceMigrated") is not True:
        errors.append("contract does not mark active scene reference migrated")
    if contract.get("sceneMapIdentityMigrated") is not True:
        errors.append("contract does not mark SceneMap identity migration complete")
except Exception as exc:
    errors.append(f"invalid scene identity contract json: {exc}")

if errors:
    print("Scene reference bridge validation failed:")
    for error in errors:
        print(" -", error)
    sys.exit(1)
print("Scene reference bridge validation passed.")
