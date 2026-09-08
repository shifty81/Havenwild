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
        "TransitionRuleDraftAutoFixEntry",
        "TransitionRuleDraftAutoFixReport",
        "apply_transition_rule_draft_auto_fixes",
        "transition_rule_draft_auto_fix_status",
        "transition_rule_draft_auto_fix_lines",
        "auto_fix_rule_atlas_group",
        "auto_fix_rule_phase_list",
        "safe_fix_count_for_rule",
        "normalize",
        "auto_fixed_by_transition_rule_editor",
    ],
)

require(
    "crates/haven_world/src/autotile/mod.rs",
    [
        "apply_transition_rule_draft_auto_fixes",
        "transition_rule_draft_auto_fix_status",
        "transition_rule_draft_auto_fix_lines",
        "TransitionRuleDraftAutoFixEntry",
        "TransitionRuleDraftAutoFixReport",
    ],
)

require(
    "crates/haven_game/src/transition_rule_editor_panel.rs",
    [
        "AutoFix",
        "apply_transition_rule_draft_auto_fixes_editor",
        "apply_transition_rule_draft_auto_fixes",
        "transition_rule_draft_auto_fix_status",
        "transition_rule_draft_auto_fix_lines",
        "AutoFix only applies conservative draft cleanups",
        "KeyCode::A",
    ],
)

print("[OK] Terrain transition draft auto-fix validator passed")
for path, count in checks:
    print(f"  {path}: {count} checks")
