#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[5]
checks = []

def require(path: str, needles: list[str]) -> None:
    text = (ROOT / path).read_text(encoding="utf-8")
    missing = [needle for needle in needles if needle not in text]
    if missing:
        print(f"[FAIL] {path} missing:")
        for needle in missing:
            print(f"  - {needle}")
        sys.exit(1)
    checks.append((path, len(needles)))

require(
    "crates/haven_world/src/autotile/transition_rule_draft.rs",
    [
        "TERRAIN_TRANSITION_RULE_DRAFT_UNDO_PATH",
        "TransitionRuleDraftRestoreReport",
        "transition_rule_draft_undo_status",
        "transition_rule_draft_undo_lines",
        "restore_transition_rule_draft_from_undo",
        "reset_transition_rule_draft_from_live_manifest",
        "snapshot_existing_draft_for_undo",
        "undo_snapshot_before_draft_edit",
        "undo_snapshot_before_draft_autofix",
        "undo_snapshot_before_live_restore",
        "restored_from_undo_snapshot",
        "restored_from_live_manifest",
    ],
)

require(
    "crates/haven_world/src/autotile/mod.rs",
    [
        "restore_transition_rule_draft_from_undo",
        "reset_transition_rule_draft_from_live_manifest",
        "transition_rule_draft_undo_status",
        "transition_rule_draft_undo_lines",
        "TransitionRuleDraftRestoreReport",
        "TERRAIN_TRANSITION_RULE_DRAFT_UNDO_PATH",
    ],
)

require(
    "crates/haven_game/src/transition_rule_editor_panel.rs",
    [
        "Undo",
        "Live",
        "restore_transition_rule_draft_from_undo_editor",
        "reset_transition_rule_draft_from_live_editor",
        "transition_rule_draft_undo_status",
        "transition_rule_draft_undo_lines",
        "KeyCode::Z",
        "KeyCode::L",
        "Undo restores last draft snapshot",
        "Live resets draft from live manifest",
    ],
)

require(
    "crates/haven_game/src/runtime_input.rs",
    [
        "self.editor_tab != EditorTab::Transitions",
        "self.undo_world()",
        "self.redo_world()",
    ],
)

print("[OK] Terrain transition draft undo/restore validator passed")
for path, count in checks:
    print(f"  {path}: {count} checks")
