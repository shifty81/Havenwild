from __future__ import annotations
import json
from pathlib import Path

from validation.domains.current_contract import run_current_contract

ROOT: Path | None = None

def _validate_editor_command_contract() -> None:
    assert ROOT is not None
    contract = json.loads((ROOT / "content/editor/commands/editor_command_contract_v1.json").read_text(encoding="utf-8"))
    if contract.get("schema") != "havenwild.editor.command-contract.v1":
        raise ValueError("editor command contract schema changed")
    if contract.get("policy", {}).get("singleMutationPath") is not True:
        raise ValueError("editor command contract no longer targets one mutation path")
    required = {"affectedBounds", "dirtyChunks", "validationRequests", "permissionScope", "persistenceIntent", "requiresAuthoritativeHost"}
    if set(contract.get("requiredMetadata", [])) != required:
        raise ValueError("target editor execution metadata contract is incomplete")
    implementation = contract.get("implementation", {})
    if implementation.get("status") != "transitional":
        raise ValueError("editor command implementation status must be explicit")
    if set(implementation.get("pendingExecutionMetadata", [])) != required:
        raise ValueError("pending execution-metadata debt is not tracked")
    source = (ROOT / "crates/haven_authoring/src/command_bus.rs").read_text(encoding="utf-8")
    for token in (
        "EditorCommandSource", "EditorCommandKind", "CommandTarget", "CommandPayload",
        "pub struct EditorCommand", "preview_only", "validation_result", "undo_patch",
        "pub struct EditorCommandBus", "begin_gesture", "record_transaction",
        "commit_gesture", "cancel_gesture", "undo_world", "redo_world",
    ):
        if token not in source:
            raise ValueError(f"current command bus missing {token}")


def validate(entry, root: Path):
    global ROOT
    ROOT = root
    return run_current_contract(entry, [("editor command, undo, dirty-chunk, and persistence contract", _validate_editor_command_contract)])
