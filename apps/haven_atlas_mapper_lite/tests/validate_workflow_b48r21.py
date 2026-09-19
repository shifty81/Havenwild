#!/usr/bin/env python3
"""B48R21 source-contract smoke, not a native Rust/PowerShell GUI/runtime test."""
from pathlib import Path
import argparse
import sys

ap = argparse.ArgumentParser()
ap.add_argument('--repo', default='.')
root = Path(ap.parse_args().repo).resolve()
main = (root / 'apps/haven_atlas_mapper_lite/src/main.rs').read_text(encoding='utf-8')
intake = (root / 'tools/control/InvokeRootPatchIntake.ps1').read_text(encoding='utf-8-sig')
bar = main.split('fn draw_top_bar(app:', 1)[1].split('fn draw_source_panel(', 1)[0]
inspector = main.split('fn draw_inspector(app:', 1)[1].split('fn draw_app(', 1)[0]
checks = {
    'equal pane baseline and constrained splitter': 'pane_ratio: 0.5' in main and 'let source_w = available * app.pane_ratio;' in main and 'let canvas_w = available - source_w;' in main and 'clamp(0.40, 0.60)' in main,
    'no false inactive navigation': 'fn draw_workspace_rail(' not in main and 'draw_workspace_rail(' not in main,
    'inspector no longer permanently shrinks scene': 'if app.show_inspector { draw_inspector(app, inspector_rect); }' in main and 'let canvas_rect = Rect::new(source_rect.x + source_w + GAP, body_top, canvas_w, body_h);' in main,
    'inspector overlay cannot paint underlying scene': 'let blocked_by_details = self.show_inspector && inspector_rect.contains(mouse);' in main and '&& !blocked_by_details' in main,
    'divider drag blocks unwanted painting': 'if self.resizing_divider {' in main and 'return; // A divider drag must never select, paint' in main,
    'source preview gets at least half vertical space': '(panel.h * 0.44)' in main,
    'single workflow toolbar': all(t in bar for t in ('"1 Draft"','"2 Learn"','"3 Stage missing cells"','"4 Audit"','"5 Review"','"6 Handoff"')),
    'no duplicated inspector workflow actions': not any(t in inspector for t in ('app.auto_map_sheet();','app.learn_from_scene();','app.reassemble_from_mapped_scene();','app.export_scene_audit();')),
    'no invented procedural reroll or approval': 'No recipe reroll yet; candidate only.' in main and 'Recipe-driven reroll is NOT implemented.' in main and 'approved_mapping' in main,
    'intake reports immediate first stage': 'INTAKE 1/6: approved transport;' in intake,
    'intake extracts with advance warning': 'INTAKE 3/6: extracting' in intake and 'extraction complete.' in intake,
    'intake reports verified, applied and postapply counts': all(t in intake for t in ('verified {0}/{1} files.','applied {0}/{1} files.','verified {0}/{1} installed files.')),
    'intake confirms receipt, log and rollback remain intact': '[PASS] PATCH APPLIED AND VERIFIED:' in intake and 'INTAKE REPORT:' in intake and 'ROLLBACK: restoring pre-patch files.' in intake,
}
for label, good in checks.items():
    print(('PASS' if good else 'FAIL') + ': ' + label)
if not all(checks.values()):
    sys.exit(1)
print('PASS B48R21 workflow/source guard. Windows GUI/PCC/Rust remain untested in this environment.')
