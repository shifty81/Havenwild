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


mod_rs = read("apps/haven_editor_native/src/app/mod.rs")
outliner = read("apps/haven_editor_native/src/app/scene_outliner.rs")
inspector = read("apps/haven_editor_native/src/app/object_inspector.rs")
draw = read("apps/haven_editor_native/src/app/draw.rs")
input_rs = read("apps/haven_editor_native/src/app/input.rs")
headless_inspector = read("crates/haven_editor/src/object_inspector.rs")
scene_management = read("crates/haven_editor/src/scene_management.rs")
transactions = read("crates/haven_authoring/src/transactions.rs")
scene_registry = read("crates/haven_core/src/scene_registry.rs")
scene_world = read("crates/haven_core/src/foundation/scene_world.rs")
editor_lib = read("crates/haven_editor/src/lib.rs")
registry = read("crates/haven_editor/src/validation_registry.rs")
contract_text = read(
    "content/editor/objects/production_object_outliner_inspector_contract_v0_1.json"
)
read("docs/editor/PRODUCTION_OBJECT_OUTLINER_INSPECTOR_PASS50.md")

checks = [
    ("mod scene_outliner;", mod_rs, "native scene outliner module is not registered"),
    ("mod object_inspector;", mod_rs, "native object inspector module is not registered"),
    ("SceneDockTab", mod_rs, "Tools/Inspector dock-tab state is missing"),
    ("EditorTextFocus", mod_rs, "inline scene/filter text focus state is missing"),
    ("FootprintEditTarget", mod_rs, "footprint target state is missing"),
    ("draw_scene_outliner", draw, "Scene Map does not draw the production outliner"),
    ("draw_scene_dock", draw, "Scene Map does not draw the Tools/Inspector dock"),
    ("handle_scene_outliner_click", input_rs, "left dock does not route outliner input"),
    ("handle_scene_dock_click", input_rs, "right dock does not route inspector input"),
    ("create_project_scene", outliner, "scene Create action is missing"),
    ("duplicate_project_scene", outliner, "scene Duplicate action is missing"),
    ("rename_project_scene", outliner, "scene Rename action is missing"),
    ("delete_project_scene", outliner, "scene Delete action is missing"),
    ("scene_delete_armed", outliner, "scene deletion lacks explicit confirmation state"),
    ("filtered_outliner_entries", outliner, "searchable object/stamp outliner is missing"),
    ("SelectionItem::Object(object.id)", outliner, "object outliner does not select by stable ID"),
    ("scene_dock_tab = SceneDockTab::Inspector", outliner, "outliner selection does not open Inspector"),
    ("object_visible_rows", outliner, "object outliner does not adapt rows to dock height"),
    ("update_scene_object", inspector, "native inspector does not call the headless update service"),
    ("FootprintEditTarget::Visual", inspector, "visual footprint editor is missing"),
    ("FootprintEditTarget::Collision", inspector, "collision footprint editor is missing"),
    ("FootprintEditTarget::Interaction", inspector, "interaction footprint editor is missing"),
    ("blocks_movement", inspector, "movement blocking toggle is missing"),
    ("occludes_player", inspector, "occlusion toggle is missing"),
    ("fade_when_player_behind", inspector, "fade-behind toggle is missing"),
    ("draw_selected_object_footprints", inspector, "canvas footprint overlays are missing"),
    ("authored_object_footprint(object.kind)", inspector, "object footprint reset is missing"),
    ("placement_issues_for_object_excluding", headless_inspector, "object updates are not placement-validated"),
    ("EditOperation::UpdateObject", headless_inspector, "object updates are not typed transactions"),
    ("pub fn create_project_scene", scene_management, "headless Create Scene service is missing"),
    ("pub fn duplicate_project_scene", scene_management, "headless Duplicate Scene service is missing"),
    ("pub fn rename_project_scene", scene_management, "headless Rename Scene service is missing"),
    ("pub fn delete_project_scene", scene_management, "headless Delete Scene service is missing"),
    ("EditOperation::InsertScene", scene_management, "Create Scene does not record InsertScene"),
    ("EditOperation::RemoveScene", scene_management, "Delete Scene does not record RemoveScene"),
    ("EditOperation::RenameScene", scene_management, "Rename Scene does not record RenameScene"),
    ("UpdateObject", transactions, "transaction operation set omits UpdateObject"),
    ("InsertScene", transactions, "transaction operation set omits InsertScene"),
    ("RemoveScene", transactions, "transaction operation set omits RemoveScene"),
    ("RenameScene", transactions, "transaction operation set omits RenameScene"),
    ("pub fn insert_at", scene_registry, "scene registry cannot restore authored insertion order"),
    ("pub fn blank", scene_world, "blank project-scene factory is missing"),
    ("pub use object_inspector::update_scene_object", editor_lib, "headless object inspector service is not exported"),
    ("pub use scene_management", editor_lib, "headless scene management services are not exported"),
    ("id: \"production_object_outliner_inspector\"", registry, "validation registry omits Pass 50"),
]
for needle, text, message in checks:
    if needle not in text:
        errors.append(message)

for rel, text in [
    ("scene_outliner.rs", outliner),
    ("object_inspector.rs", inspector),
    ("headless object_inspector.rs", headless_inspector),
    ("scene_management.rs", scene_management),
    ("transactions.rs", transactions),
]:
    if len(text.splitlines()) > 750:
        errors.append(f"{rel} exceeds the 750-line module ceiling")

combined_native = mod_rs + outliner + inspector + draw + input_rs
if "selected_scene_object: Option<usize>" in combined_native:
    errors.append("native inspector regressed to unstable object vector-index selection")
if "selection.replace_many(scene_id, vec![SelectionItem::Object(index" in combined_native:
    errors.append("object outliner stores a vector index instead of ObjectId")
if "serialize_lines()" in headless_inspector + scene_management:
    errors.append("Pass 50 headless services regressed to full-world snapshot history")
if "SceneId::ALL" in scene_management:
    errors.append("scene lifecycle is still constrained to the legacy scene enum")

try:
    contract = json.loads(contract_text)
    if contract.get("pass") != "50":
        errors.append("production object outliner contract pass mismatch")
    outliner_contract = contract.get("objectOutliner", {})
    if outliner_contract.get("stableObjectIds") is not True:
        errors.append("stable object IDs are not contractually required")
    if outliner_contract.get("vectorIndexSelectionForbidden") is not True:
        errors.append("vector-index selection is not contractually forbidden")
    scene_contract = contract.get("sceneOutliner", {})
    for action in ("create", "duplicate", "rename", "delete"):
        if scene_contract.get(action) is not True:
            errors.append(f"scene lifecycle action '{action}' is not contractually required")
    if scene_contract.get("deleteRequiresConfirmation") is not True:
        errors.append("scene-delete confirmation is not contractually required")
    inspector_contract = contract.get("inspector", {})
    if inspector_contract.get("editableFootprints") != ["Visual", "Collision", "Interaction"]:
        errors.append("all three footprint targets are not contractually editable")
    if inspector_contract.get("placementValidation") is not True:
        errors.append("object property placement validation is not contractually required")
    transaction_contract = contract.get("transactions", {})
    for operation in ("updateObject", "insertScene", "removeScene", "renameScene"):
        if transaction_contract.get(operation) is not True:
            errors.append(f"typed transaction '{operation}' is not contractually required")
except Exception as exc:
    errors.append(f"invalid production object outliner contract json: {exc}")

if errors:
    print("Production object outliner and inspector validation failed:")
    for error in errors:
        print(" -", error)
    sys.exit(1)

print("Production object outliner and inspector validation passed.")
