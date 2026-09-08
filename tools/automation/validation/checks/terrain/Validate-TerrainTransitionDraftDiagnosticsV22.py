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
        "TransitionRuleDraftDiagnosticSeverity",
        "TransitionRuleDraftDiagnostic",
        "TransitionRuleDraftValidationReport",
        "validate_transition_rule_draft_for_editor",
        "transition_rule_draft_validation_status",
        "transition_rule_draft_selected_validation_lines",
        "collect_transition_rule_draft_diagnostics",
        "SUPPORTED_TRANSITION_ATLAS_GROUPS",
        "validate_selector_material_combination",
        "promotion blocked by transition-rule draft diagnostics",
    ],
)

require(
    "crates/haven_world/src/autotile/mod.rs",
    [
        "validate_transition_rule_draft_for_editor",
        "transition_rule_draft_selected_validation_lines",
        "transition_rule_draft_validation_status",
        "TransitionRuleDraftDiagnostic",
        "TransitionRuleDraftValidationReport",
    ],
)

require(
    "crates/haven_game/src/transition_rule_editor_panel.rs",
    [
        "Validate",
        "validate_transition_rule_draft_editor",
        "validate_transition_rule_draft_for_editor",
        "transition_rule_draft_validation_status",
        "transition_rule_draft_selected_validation_lines",
        "Draft promotion is blocked until transition-rule diagnostics are fixed",
    ],
)

require(
    "crates/haven_game/src/runtime_input.rs",
    [
        "self.editor_tab != EditorTab::Transitions && is_key_pressed(KeyCode::V)",
    ],
)

print("[OK] Terrain transition draft diagnostics validator passed")
for path, count in checks:
    print(f"  {path}: {count} checks")
