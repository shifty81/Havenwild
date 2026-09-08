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


transactions = read("crates/haven_authoring/src/transactions.rs")
edit_operation = read("crates/haven_authoring/src/edit_operation.rs")
transaction_authority = transactions + edit_operation
command_bus = read("crates/haven_authoring/src/command_bus.rs")
scene_edit = read("crates/haven_editor/src/scene_edit.rs")
scene_structure_edit = read("crates/haven_editor/src/scene_structure_edit.rs")
scene_edit_authority = scene_edit + scene_structure_edit
entities = read("crates/haven_core/src/foundation/authored_entities.rs")
input_code = read("apps/haven_editor_native/src/app/input.rs") + read(
    "apps/haven_editor_native/src/app/production_tools.rs"
)
scene_authoring = read("apps/haven_editor_native/src/app/scene_authoring.rs")
draw = read("apps/haven_editor_native/src/app/draw.rs")
registry = read("crates/haven_editor/src/validation_registry.rs")
contract_text = read("content/editor/transactions/transactional_undo_contract_v0_1.json")
read("docs/editor/TRANSACTIONAL_UNDO_PASS48D.md")

checks = [
    ("pub fn apply(&self, world: &mut GameWorld)", transaction_authority, "transaction apply executor missing"),
    ("pub fn revert(&self, world: &mut GameWorld)", transaction_authority, "transaction revert executor missing"),
    ("EditDirection::Reverse", transaction_authority, "undo does not reverse operation order"),
    ("let backup = world.clone()", transaction_authority, "atomic replay recovery guard missing"),
    ("InsertObject {\n        object: PlacedObject", transaction_authority, "object insert does not retain exact entity data"),
    ("RemoveObject {\n        object: PlacedObject", transaction_authority, "object removal does not retain exact entity data"),
    ("InsertTransition {\n        transition: Transition", transaction_authority, "transition insert does not retain exact entity data"),
    ("RemoveTransition {\n        transition: Transition", transaction_authority, "transition removal does not retain exact entity data"),
    ("pub fn begin_gesture", command_bus, "gesture begin lifecycle missing"),
    ("pub fn commit_gesture", command_bus, "gesture commit lifecycle missing"),
    ("pub fn cancel_gesture", command_bus, "gesture cancel lifecycle missing"),
    ("pub fn record_transaction", command_bus, "typed transaction recording missing"),
    ("pub fn undo_world", command_bus, "transaction-aware undo missing"),
    ("pub fn redo_world", command_bus, "transaction-aware redo missing"),
    ("RecordedEdit::Transaction", command_bus, "typed history entries missing"),
    ("RecordedEdit::Snapshot", command_bus, "snapshot compatibility fallback missing"),
    ("command_bus.record_transaction", scene_edit, "scene edits do not record typed transactions"),
    ("EditOperation::SetTile", scene_edit, "tile transaction emission missing"),
    ("EditOperation::SetZone", scene_edit, "zone transaction emission missing"),
    ("EditOperation::InsertObject", scene_edit, "object insert transaction emission missing"),
    ("EditOperation::RemoveObject", scene_edit, "object remove transaction emission missing"),
    ("EditOperation::MoveObject", scene_edit, "object move transaction emission missing"),
    ("EditOperation::InsertTransition", scene_edit_authority, "transition insert transaction emission missing"),
    ("EditOperation::RemoveTransition", scene_edit_authority, "transition remove transaction emission missing"),
    ("EditOperation::ResizeTransition", scene_edit_authority, "transition resize transaction emission missing"),
    ("self.command_bus.begin_gesture()", input_code, "native paint drag does not begin a gesture"),
    ("self.command_bus.commit_gesture()", input_code, "native pointer release does not commit a gesture"),
    ("self.command_bus.cancel_gesture", input_code, "native editor cannot cancel an active gesture"),
    ("KeyCode::Y", input_code, "Ctrl+Y redo shortcut missing"),
    ("shift_down && is_key_pressed(KeyCode::Z)", input_code, "Ctrl+Shift+Z redo shortcut missing"),
    ("undo_world(&mut self.model.world)", scene_authoring, "native editor still bypasses typed undo"),
    ("redo_world(&mut self.model.world)", scene_authoring, "native editor typed redo missing"),
    ("typed_undo_len", draw, "history UI does not report typed transaction count"),
    ("id: \"typed_edit_transactions\"", registry, "validation registry omits typed transactions"),
    ("status: ValidationRegistryStatus::Active", registry, "typed transaction registry entry is not active"),
    ("PartialEq, Eq", entities, "authored entities are not comparable for strict transaction replay"),
]
for needle, text, message in checks:
    if needle not in text:
        errors.append(message)

for forbidden, message in [
    ("serialize_lines()", "scene_edit.rs still serializes the whole world for an editor edit"),
    ("capture_undo_snapshot", "scene_edit.rs still records snapshot undo"),
]:
    if forbidden in scene_edit:
        errors.append(message)

if len(transactions.splitlines()) > 750:
    errors.append("transactions.rs exceeds the standard module ceiling")
if len(edit_operation.splitlines()) > 750:
    errors.append("edit_operation.rs exceeds the standard module ceiling")
if len(command_bus.splitlines()) > 750:
    errors.append("command_bus.rs exceeds the standard module ceiling")
if len(scene_edit.splitlines()) > 750:
    errors.append("scene_edit.rs exceeds the standard module ceiling")
if len(scene_structure_edit.splitlines()) > 750:
    errors.append("scene_structure_edit.rs exceeds the standard module ceiling")

try:
    contract = json.loads(contract_text)
    if contract.get("pass") != "48D":
        errors.append("transaction contract pass mismatch")
    history = contract.get("history", {})
    if history.get("primaryMode") != "typed_transactions":
        errors.append("typed transactions are not the contract primary history mode")
    if history.get("snapshotFallback") is not True:
        errors.append("snapshot migration fallback is not preserved")
    lifecycle = contract.get("gestureLifecycle", {})
    if lifecycle.get("paintDragOneUndoEntry") is not True:
        errors.append("paint drag one-entry rule missing")
    if lifecycle.get("cancelRevertsUncommittedOperations") is not True:
        errors.append("gesture cancel rollback rule missing")
    safety = contract.get("safety", {})
    if safety.get("fullWorldSerializationPerEditorCellForbidden") is not True:
        errors.append("contract does not forbid per-cell world serialization")
    if safety.get("atomicWorldRestoreOnReplayFailure") is not True:
        errors.append("atomic replay recovery rule missing")
except Exception as exc:
    errors.append(f"invalid transactional undo contract json: {exc}")

if errors:
    print("Transactional undo validation failed:")
    for error in errors:
        print(" -", error)
    sys.exit(1)

print("Transactional undo / gesture coalescing validation passed.")
