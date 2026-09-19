#!/usr/bin/env python3
"""B48R15 offline asset/transport guard. Not a Rust compile or game certification."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

p = argparse.ArgumentParser()
p.add_argument('--repo', type=Path, default=Path.cwd())
a = p.parse_args()
root = a.repo.resolve()
main = (root / 'apps/haven_atlas_mapper_lite/src/main.rs').read_text(encoding='utf-8')
registry_path = root / 'content/assets/lpc/elizawy_summer_source_registry_b48r15_v0_1.json'
registry = json.loads(registry_path.read_text(encoding='utf-8'))
assert registry['schema'] == 'havenwild.elizawy_summer_source_registry.v0_1'
checks = {
    'left source catalog + right editable scene': 'LEFT | ElizaWy Summer Source Library' in main and 'RIGHT | ElizaWy Summer Scene Workspace' in main,
    'click ON/OFF activation respects used scene sources': 'self.deactivate_sheet(index)' in main and 'Sheet still used by scene placements' in main,
    'Summer seasonal filter includes shared waterfalls': 'substring "fall" is part of WATERFALL' in main and 'file.contains("non-winter")' in main,
    'other seasons excluded from sibling scan': 'for season in ["summer"]' in main and 'is_summer_elizawy_source(&sibling)' in main,
    'summer B48R7 + B48R9 source evidence loaded': 'elizawy_summer_atlas_source_crosswalk_b48r7_v0_1.json' in main and 'elizawy_all_seasons_split_source_crosswalk_b48r9_v0_1.json' in main,
    'source evidence never semantic certification': 'Pixel matches only; never semantic/visual certification' in main,
    'full sheet index + per-frame row virtualization': 'MAX_LIBRARY_SHEETS: usize = 100_000' in main and '.iter().skip(first_visible)' in main,
    'search visible list and protects editor hotkeys': 'sheet_library_search_focused' in main and 'get_char_pressed()' in main and 'self.rebuild_sheet_library_visibility();' in main,
    'mapped records written per active original source': 'fn write_all_mapping_records' in main and 'filter(|piece| piece.source_asset_id == atlas.id)' in main,
    'source exact hashes pinned from original registry': 'pinned_summer_source_hashes' in main and 'source_sha256: pinned.get(' in main,
    'candidate source review + real level one': 'unreviewed_source_assembly_not_for_runtime' in (root/'apps/haven_atlas_mapper_lite/src/review.rs').read_text() and 'including +1' in (root/'apps/haven_atlas_mapper_lite/src/review.rs').read_text(),
}
psroot = root / 'tools/control'
for name in ['InvokeRootPatchIntake.ps1','HavenwildTools.ps1','PccPatchPreflight.ps1']:
    checks['PCC cumulative discovery: '+name] = 'Havenwild_CUMULATIVE_PCC_Patch_*.zip' in (psroot/name).read_text(encoding='utf-8-sig')
checks['PCC duplicates safely held'] = 'held-duplicate-downloads' in (psroot/'InvokeRootPatchIntake.ps1').read_text()
checks['root cleanliness audit retains fail closed'] = 'RECOVERY: browser-renamed duplicate' in (psroot/'AuditRoot.ps1').read_text()
# Committed root launchers must be accepted without weakening the unknown-file guard.
audit_root = (psroot/'AuditRoot.ps1').read_text(encoding='utf-8-sig')
optional_line = next((line for line in audit_root.splitlines() if line.startswith('$optional=@(')), '')
checks['root audit recognizes all four tracked ForgePY launchers'] = all(
    "'"+name+"'" in optional_line
    for name in ('ForgePY-GUI.cmd','ForgePY-Install.cmd','ForgePY-Verify.cmd','ForgePY.cmd')
)
checks['root audit rejects unknown files'] = '$_ -notin $allowed' in audit_root and "'^Havenwild_CUMULATIVE_PCC_Patch_" in audit_root
for label, ok in checks.items():
    print(('PASS' if ok else 'FAIL')+' '+label)
if not all(checks.values()): sys.exit(1)
records = registry['sources']; assert len(records) == registry['sourceFiles'] and len(records) >= 2900
seen = set()
for asset in records:
    rel = asset['path']
    assert rel.startswith('assets/source/licensed/lpc_revised/') and rel not in seen
    seen.add(rel)
    path = root / rel
    assert path.is_file(), 'Source missing: '+rel
    assert hashlib.sha256(path.read_bytes()).hexdigest() == asset['sha256'], 'Original source hash mismatch: '+rel
print('PASS full original source registry SHA256 replay: '+str(len(records))+' Summer/neutral originals')
primary = next(x for x in records if x['path'].endswith('/Terrain/Waterfall.png') and 'seasonal_split' not in x['path'])
split = next(x for x in records if x['path'].endswith('/seasonal_split/Terrain/Waterfall.png'))
assert primary['sha256'] != split['sha256']
assert (root/'content/assets/lpc/credits/elizawy_split_source_terrain_credits_b48r15.txt').is_file()
print('PASS both distinct original waterfall sheets + split source credits retained')
seasonal = json.loads((root/'content/assets/lpc/elizawy_all_seasons_split_source_crosswalk_b48r9_v0_1.json').read_text())
summer = [e for e in seasonal['entries'] if any(t.get('season')=='summer' for t in e.get('targets',[]))]
assert len(summer) == 641
print('PASS B48R9 summer crosswalk: '+str(len(summer))+' pixel-cell evidence entries (not semantic roles)')
print('PASS B48R15 static/data tests only. Windows Cargo/GUI/PCC gate and full Summer semantic certification remain outstanding.')
