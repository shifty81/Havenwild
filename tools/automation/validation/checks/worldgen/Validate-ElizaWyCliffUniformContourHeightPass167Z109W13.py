#!/usr/bin/env python3
from pathlib import Path
import json, sys
ROOT=Path(__file__).resolve().parents[5]
def txt(rel): return (ROOT/rel).read_text(encoding='utf-8')
def req(ok,msg):
    if not ok: raise AssertionError(msg)
try:
    authority=json.loads(txt('content/worldgen/elizawy_cliff_uniform_contour_height_authority_v0_1.json'))
    req(authority.get('pass')=='167Z109W13','W13 authority pass mismatch')
    shapes=txt('crates/haven_game/src/runtime_structural_cliff_shapes.rs')
    draw=txt('crates/haven_game/src/runtime_structural_cliff_draw.rs')
    collision=txt('crates/haven_game/src/runtime_surface_streaming_structural.rs')

    req('pub(super) const fn uniform_south_face_receiver_rows' in shapes,
        'uniform south-face receiver-row helper missing')
    req('2 + authored_body_rows(face_segments)' in shapes,
        'uniform receiver-row helper no longer wraps the shared modular body count')
    req('(face_segments - 1) as usize' in shapes,
        'tier delta no longer maps to delta-1 repeatable body rows')

    req('low_side_dx: i32' in draw and 'let receiver_x = global_x + low_side_dx;' in draw,
        'diagonal low-side receiver ownership missing')
    req('diagonal_chain_role,\n                    -1,\n                    SOUTH_WEST_DIAGONAL_FACE' in draw,
        'south-west diagonal is not bound to west low-side receiver')
    req('diagonal_chain_role,\n                    1,\n                    SOUTH_EAST_DIAGONAL_FACE' in draw,
        'south-east diagonal is not bound to east low-side receiver')
    req('cliff_projection_row_visible(manifest, receiver_x, target_y, host_level)' in draw,
        'diagonal body visibility still checks the raised host column')
    req('cliff_projection_row_visible(manifest, receiver_x, foot_y, host_level)' in draw,
        'diagonal foot visibility still checks the raised host column')
    req('uniform_south_face_receiver_rows(south_segments)' in collision,
        'collision depth is not using the shared uniform contour-height helper')

    preview=ROOT/authority['acceptancePreview']
    req(preview.is_file() and preview.stat().st_size>1000,'W13 uniform-height acceptance board missing')
    req('Pass 167Z109W13' in txt('crates/haven_game/src/runtime_diagnostics.rs'),'runtime diagnostics not W13')
    req('Pass167Z109W13' in txt('README.md'),'README not W13')
    req('Pass167Z109W13' in txt('docs/current/CURRENT_SOURCE_HANDOFF.md'),'handoff not W13')

    registry=json.loads(txt('content/build/validator_registry_v3.json'))
    source=[e for e in registry['validators'] if 'source' in e.get('profiles',[])]
    req(len(source)==10,f'source profile must remain 10, got {len(source)}')
    req(any(e['id']=='worldgen.elizawy-cliff-uniform-contour-height-v167z109w13' for e in source),
        'W13 validator not current source terrain authority')
    req(not any(e['id']=='worldgen.elizawy-cliff-rim-height-v167z109w12' for e in source),
        'W12 validator should be historical/full after W13')
    print('Pass167Z109W13 uniform cliff contour-height authority validated')
except Exception as e:
    print(f'Pass167Z109W13 validation FAILED: {e}')
    sys.exit(1)
