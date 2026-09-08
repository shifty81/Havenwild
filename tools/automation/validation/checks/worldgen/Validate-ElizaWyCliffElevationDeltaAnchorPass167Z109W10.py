#!/usr/bin/env python3
from pathlib import Path
import json, sys
ROOT = Path(__file__).resolve().parents[5]

def txt(rel): return (ROOT / rel).read_text(encoding='utf-8')
def req(ok, msg):
    if not ok: raise AssertionError(msg)

try:
    authority = json.loads(txt('content/worldgen/elizawy_cliff_elevation_delta_anchor_authority_v0_1.json'))
    req(authority.get('pass') == '167Z109W10', 'W10 authority pass mismatch')
    shapes = txt('crates/haven_game/src/runtime_structural_cliff_shapes.rs')
    draw = txt('crates/haven_game/src/runtime_structural_cliff_draw.rs')
    collision = txt('crates/haven_game/src/runtime_surface_streaming_structural.rs')
    req('authored_face_segments_for_edge' in shapes, 'edge-specific face segment resolver missing')
    req('STRUCTURAL_ELEVATION_RESOLVER_STEP_V2' in shapes, 'structural-tier resolver step not used')
    req('authored_south_face_segments(center)' in draw, 'renderer is not using exact south-edge height')
    req('let compact = chain_role.uses_compact_projection()' not in draw, 'historical compact diagonal renderer still active')
    req('recipe.shoulder' in draw, 'authored diagonal shoulder no longer rendered')
    req('authored_south_face_segments(host)' in collision, 'collision is not using exact south-edge height')
    req('Pass 167Z109W' in txt('crates/haven_game/src/runtime_diagnostics.rs'), 'runtime diagnostics left W terrain lane')
    req('Pass167Z109W' in txt('README.md'), 'README left W terrain lane')
    req('Pass167Z109W' in txt('docs/current/CURRENT_SOURCE_HANDOFF.md'), 'handoff left W terrain lane')
    req((ROOT / authority['acceptancePreview']).is_file(), 'W10 acceptance preview missing')
    print('Pass167Z109W10 cliff elevation-delta + full-diagonal alignment validated')
except Exception as e:
    print(f'Pass167Z109W10 validation FAILED: {e}')
    sys.exit(1)
