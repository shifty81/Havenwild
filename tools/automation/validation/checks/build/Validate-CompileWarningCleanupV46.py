#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[5]
issues = []

resolver_path = ROOT / 'crates/haven_world/src/world_paint_transition_tile_resolver.rs'
resolver = resolver_path.read_text(encoding='utf-8')
if re.search(r'#\[derive\([^\]]+\)\]\s*\n\s*#\[derive\(', resolver):
    issues.append('world_paint_transition_tile_resolver.rs still contains adjacent duplicate derive blocks')

transition_atlas_path = ROOT / 'crates/haven_world/src/autotile/transition_atlas.rs'
transition_atlas = transition_atlas_path.read_text(encoding='utf-8')
import_block = transition_atlas.split('};', 1)[0]
for token in ['TerrainCornerTransition', 'TerrainEdgeTransition', 'TerrainFamily']:
    if token in import_block:
        issues.append(f'transition_atlas.rs still imports unused token {token} at module scope')

asset_autotile_path = ROOT / 'crates/haven_assets/src/autotile.rs'
asset_autotile = asset_autotile_path.read_text(encoding='utf-8')
if 'let mut candidates = self.variants.iter().filter(|variant| variant.group == group_id);' in asset_autotile:
    issues.append('haven_assets/src/autotile.rs still uses unnecessary mutable candidates iterator')
if 'let candidates = self.variants.iter().filter(|variant| variant.group == group_id);' not in asset_autotile:
    issues.append('haven_assets/src/autotile.rs missing immutable candidates iterator after cleanup')

donor_path = ROOT / 'crates/haven_assets/src/donor_reference_catalog.rs'
donor = donor_path.read_text(encoding='utf-8')
if re.search(r'fn\s+info\s*\(', donor):
    issues.append('donor_reference_catalog.rs still defines unused info(...) helper')
for required in ['fn warning(', 'fn error(']:
    if required not in donor:
        issues.append(f'donor_reference_catalog.rs missing required helper {required}')

if not (ROOT / 'docs/assets/WORLD_PAINT_COMPILE_WARNING_CLEANUP_PASS39.md').exists():
    issues.append('missing Pass 39 docs')

if issues:
    print('Validate-CompileWarningCleanupV46 FAILED')
    for issue in issues:
        print(' -', issue)
    raise SystemExit(1)
print('Validate-CompileWarningCleanupV46 OK')
