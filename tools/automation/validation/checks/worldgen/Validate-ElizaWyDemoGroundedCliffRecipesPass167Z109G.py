#!/usr/bin/env python3
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[5]
errors=[]

def req(path, tokens):
    p=ROOT/path
    if not p.is_file():
        errors.append(f"missing {path}")
        return
    s=p.read_text(encoding='utf-8-sig')
    for t in tokens:
        if t not in s:
            errors.append(f"{path} missing {t}")

req('crates/haven_game/src/runtime_structural_cliff_shapes.rs', [
    'body: source_cell(2, 3)', 'foot: source_cell(2, 8)',
    'shoulder: source_cell(1, 7)', 'body: source_cell(1, 3)',
    'shoulder: source_cell(3, 7)', 'body: source_cell(3, 3)',
])
shapes=(ROOT/'crates/haven_game/src/runtime_structural_cliff_shapes.rs').read_text(encoding='utf-8-sig')
if not any(token in shapes for token in (
    'source_crop(2, 7, 0, 24, 32, 8)',
    'source_crop(2, 7, 0, 20, 32, 12)',
)):
    errors.append('runtime south lip no longer grounded in c2/r7')

streaming=(ROOT/'crates/haven_game/src/runtime_surface_streaming.rs').read_text(encoding='utf-8-sig')
if '_ => 2' not in streaming:
    errors.append('ordinary south face no longer projects two rows')
if not any(token in streaming for token in (
    'Some(CliffShape15::SouthWest | CliffShape15::EastSouth) => 3',
    'if !chain_role.uses_compact_projection() => 3',
)):
    errors.append('isolated rounded corner three-row projection missing')

# The runtime banner advances with later passes; recipe authority is verified from source/catalog above.
req('crates/haven_game/src/runtime_diagnostics.rs', ['Pass 167Z109'])

mapping=ROOT/'content/worldgen/elizawy_cliff_complete_mapping_v0_1.json'
if mapping.is_file():
    obj=json.loads(mapping.read_text(encoding='utf-8-sig'))
    if obj.get('pass') != '167Z109G': errors.append('complete mapping pass is not Z109G')
    if obj['worldgenShapeBindings'].get('mask4') != 'south: c2r7 host/lip + c2r3 body + c2r8 receiver-transparent foot':
        errors.append('mask4 demo recipe mismatch')
else: errors.append('missing complete mapping')

if errors:
    print('Pass167Z109G demo-grounded cliff recipe validation FAILED')
    for e in errors: print(' -',e)
    sys.exit(1)
print('Pass167Z109G demo-grounded cliff recipe validation passed')
