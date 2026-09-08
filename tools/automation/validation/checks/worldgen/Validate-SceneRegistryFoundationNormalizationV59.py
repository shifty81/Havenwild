#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
errors: list[str] = []


def read(rel: str) -> str:
    path = ROOT / rel
    if not path.exists():
        errors.append(f"missing {rel}")
        return ""
    return path.read_text(encoding="utf-8")


foundation = read("crates/haven_core/src/foundation.rs")
scene_world = read("crates/haven_core/src/foundation/scene_world.rs")
scene_types = read("crates/haven_core/src/scene_types.rs")
scene_registry = read("crates/haven_core/src/scene_registry.rs")
scene_identity = read("crates/haven_core/src/scene_identity.rs")
loader = read("crates/haven_core/src/worldgen_loader.rs")
scene_edit = read("crates/haven_editor/src/scene_edit.rs")
contract_text = read("content/editor/scene_identity/scene_registry_contract_v0_1.json")
read("docs/editor/SCENE_REGISTRY_FOUNDATION_NORMALIZATION_PASS48B.md")

checks = [
    ("mod scene_world;", foundation, "foundation does not own the extracted scene-world module"),
    ("mod ui_layout;", foundation, "foundation does not own the extracted UI-layout module"),
    ("pub struct SceneMap", scene_world, "SceneMap was not extracted"),
    ("pub id: ProjectSceneId", scene_world, "SceneMap identity is not ProjectSceneId"),
    ("pub scenes: SceneRegistry", scene_world, "GameWorld storage is not SceneRegistry"),
    ("pub fn insert_scene", scene_world, "GameWorld insert_scene API missing"),
    ("pub fn duplicate_scene", scene_world, "GameWorld duplicate_scene API missing"),
    ("pub fn rename_scene", scene_world, "GameWorld rename_scene API missing"),
    ("pub fn remove_scene", scene_world, "GameWorld remove_scene API missing"),
    ("ProjectSceneId::new(parts[1])", scene_world, "line save still requires legacy SceneId"),
    ("pub enum SceneId", scene_types, "legacy seed SceneId was not isolated"),
    ("pub struct SceneRegistry", scene_registry, "SceneRegistry type missing"),
    ("index_by_id: HashMap<ProjectSceneId, usize>", scene_registry, "SceneRegistry has no indexed project-ID lookup"),
    ("pub fn by_id", scene_registry, "SceneRegistry project-ID lookup missing"),
    ("pub fn rename", scene_registry, "SceneRegistry rename API missing"),
    ("pub fn validate", scene_registry, "SceneRegistry invariant validation missing"),
    ("scene_map_identity_migrated: true", scene_identity, "Rust migration plan does not mark SceneMap migration complete"),
    ("SceneRegistry::from_scenes(scenes)", loader, "worldgen loader does not build a SceneRegistry"),
    ("ProjectSceneId::new(normalize_code(scene_code))", loader, "worldgen loader still rejects arbitrary scene IDs"),
    ("scene_id: impl Into<ProjectSceneId>", scene_edit, "scene edit API is still enum-bound"),
]
for needle, text, message in checks:
    if needle not in text:
        errors.append(message)

if "pub scenes: Vec<SceneMap>" in scene_world or "pub id: SceneId" in scene_world:
    errors.append("legacy enum/vector scene storage remains active")
if len(foundation.splitlines()) > 1840:
    errors.append("foundation.rs exceeded the Pass 48B no-growth ceiling")
if len(scene_edit.splitlines()) > 750:
    errors.append("scene_edit.rs did not return below the standard module ceiling")

try:
    contract = json.loads(contract_text)
    if contract.get("identityType") != "ProjectSceneId":
        errors.append("scene registry contract identityType mismatch")
    if contract.get("storageType") != "SceneRegistry":
        errors.append("scene registry contract storageType mismatch")
    serialization = contract.get("serialization", {})
    if serialization.get("arbitraryProjectIdsRoundTrip") is not True:
        errors.append("scene registry contract does not require arbitrary ID round trips")
    if serialization.get("duplicateSceneIdsRejected") is not True:
        errors.append("scene registry contract does not reject duplicate IDs")
except Exception as exc:
    errors.append(f"invalid scene registry contract json: {exc}")

if errors:
    print("Scene registry / foundation normalization validation failed:")
    for error in errors:
        print(" -", error)
    sys.exit(1)

print("Scene registry / foundation normalization validation passed.")
