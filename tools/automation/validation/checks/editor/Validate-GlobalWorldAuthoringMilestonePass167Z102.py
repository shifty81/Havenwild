#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"FAILED Pass167Z102 global world authoring: {message}")


def main() -> None:
    contract = json.loads(
        read("content/editor/world_canvas/global_world_authoring_milestone_v0_1.json")
    )
    require(
        contract["schema"]
        == "havenwild.editor.global_world_authoring_milestone.v0_1",
        "contract schema",
    )
    require(
        contract["pass"] in {"167Z102", "167Z103"},
        "contract pass or discrete-level correction",
    )
    require(contract["landmass"] == "Alderreach", "Alderreach authority")
    require(
        contract["transactionAuthority"]["oneUndoStepPerGesture"] is True,
        "one undo step per gesture",
    )
    require(
        contract["transactionAuthority"]["atomicFailureRollback"] is True,
        "atomic failure rollback",
    )
    require(
        contract["assetPlacement"]["croppedOrPartialPlacementAllowed"] is False,
        "atomic asset placement",
    )
    require(
        contract["selectionAndClipboard"]["packDefinedObjectMetadataPolicy"]
        == "compatibility_kind_and_footprint_only",
        "honest pack-defined clipboard metadata policy",
    )
    require(
        contract["selectionAndClipboard"]["exactProviderAndStatePreservation"]
        is False,
        "provider/state preservation remains explicitly deferred",
    )
    require(
        contract["passesGroupedWithoutIntermediateBuild"]
        == ["167Z99", "167Z100", "167Z101", "167Z102"],
        "grouped milestone lineage",
    )

    transaction_rs = read("crates/haven_authoring/src/transactions.rs")
    edit_operation_rs = read("crates/haven_authoring/src/edit_operation.rs")
    transaction_batch_rs = read("crates/haven_authoring/src/transaction_batch.rs")
    transaction_authority = transaction_rs + transaction_batch_rs
    command_bus = read("crates/haven_authoring/src/command_bus.rs")
    for token in [
        "pub struct EditTransactionBatch",
        "pub fn scene_count(&self) -> usize",
        "fn execute_atomically",
        "*world = backup;",
    ]:
        require(token in transaction_authority, token)
    for token in [
        "TransactionBatch",
        "pub fn record_transaction_batch",
        "every touched scene coalesce into one cross-scene undo entry",
        "pub fn cancel_gesture",
        "cross_scene_batch_undo_and_redo_are_atomic",
    ]:
        require(token in command_bus, token)

    mod_rs = read("crates/haven_editor/src/world_surface_edit/mod.rs")
    address = read("crates/haven_editor/src/world_surface_edit/address.rs")
    operations = read("crates/haven_editor/src/world_surface_edit/operations.rs")
    clipboard = read("crates/haven_editor/src/world_surface_edit/clipboard.rs")
    tests = read("crates/haven_editor/src/world_surface_edit/tests.rs")
    for token in [
        "WorldSurfaceLayer",
        "WorldSurfaceValue",
        "WorldSurfaceClipboard",
        "WorldSurfaceEditOutcome",
    ]:
        require(token in mod_rs, token)
    for token in [
        "pub fn resolve_world_surface_cell",
        "pub fn world_surface_bounds",
        "pub fn validate_world_surface_footprint",
        "crosses storage partitions",
    ]:
        require(token in address, token)
    for token in [
        "pub fn paint_world_surface_cells",
        "pub fn paint_world_surface_rectangle",
        "pub fn flood_fill_world_surface",
        "pub fn replace_world_surface_value",
        "changed_global.sort();",
        "changed_global.dedup();",
        "*world = backup;",
    ]:
        require(token in operations, token)
    for token in [
        "pub fn copy_world_surface_rectangle",
        "pub fn paste_world_surface_clipboard",
        "validate_world_surface_footprint",
        "record_transaction_batch",
    ]:
        require(token in clipboard, token)
    for token in [
        "rectangle_edit_records_one_cross_scene_undo_step",
        "invalid_global_batch_rolls_back_every_partition",
        "clipboard_paste_crosses_partition_as_one_undo_step",
        "complete_object_footprint_cannot_be_cropped_by_partition_boundary",
    ]:
        require(token in tests, token)

    app_mod = read("apps/haven_editor_native/src/app/mod.rs")
    authoring = read("apps/haven_editor_native/src/app/world_surface_authoring.rs")
    authoring_ui = read("apps/haven_editor_native/src/app/world_surface_authoring_ui.rs")
    editor_types = read("apps/haven_editor_native/src/app/editor_types.rs")
    for token in [
        "mod world_surface_authoring;",
        "mod world_surface_authoring_ui;",
        "world_edit_tool: WorldEditTool",
        "world_layer_mode: WorldLayerMode",
        "world_selection: Option<GridRect>",
        "world_clipboard: Option<WorldSurfaceClipboard>",
    ]:
        require(token in app_mod, token)
    for token in [
        "update_world_editor_input",
        "paint_world_surface_cells",
        "paint_world_surface_rectangle",
        "flood_fill_world_surface",
        "replace_world_surface_value",
        "copy_world_surface_rectangle",
        "paste_world_surface_clipboard",
        "validate_world_surface_footprint",
        "global_grid_line",
    ]:
        require(token in authoring, token)
    for token in [
        "Authoring Layer",
        "Global Tool",
        "Active Brush",
        "Transaction Actions",
        '"Undo", "Redo", "Copy", "Paste", "Frame", "Open Partition"',
    ]:
        require(token in authoring_ui, token)
    for token in [
        "pub(crate) enum WorldEditTool",
        "pub(crate) enum WorldLayerMode",
        "pub(crate) enum WorldCanvasDragKind",
    ]:
        require(token in editor_types, token)

    for relative in [
        "crates/haven_authoring/src/transactions.rs",
        "crates/haven_authoring/src/edit_operation.rs",
        "crates/haven_authoring/src/transaction_batch.rs",
        "crates/haven_editor/src/scene_edit.rs",
        "crates/haven_editor/src/scene_structure_edit.rs",
        "apps/haven_editor_native/src/app/world_surface_authoring.rs",
        "apps/haven_editor_native/src/app/world_surface_authoring_ui.rs",
        "crates/haven_editor/src/world_surface_edit/address.rs",
        "crates/haven_editor/src/world_surface_edit/clipboard.rs",
        "crates/haven_editor/src/world_surface_edit/operations.rs",
        "crates/haven_editor/src/world_surface_edit/tests.rs",
    ]:
        require(len(read(relative).splitlines()) <= 750, f"module line limit: {relative}")

    require(
        (ROOT / "docs/archive/pass_history/PASS167Z102_GLOBAL_WORLD_AUTHORING_MILESTONE.md").is_file(),
        "milestone documentation",
    )
    require(
        (ROOT / "manifests/patches/Pass167Z102-global-world-authoring-milestone.json").is_file(),
        "milestone patch manifest",
    )
    print("Pass167Z102 global world authoring milestone validation passed")


if __name__ == "__main__":
    main()
