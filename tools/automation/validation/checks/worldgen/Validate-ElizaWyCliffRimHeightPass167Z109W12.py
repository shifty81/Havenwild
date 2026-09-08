#!/usr/bin/env python3
from pathlib import Path
import json, sys
ROOT=Path(__file__).resolve().parents[5]
def txt(rel): return (ROOT/rel).read_text(encoding='utf-8')
def req(ok,msg):
    if not ok: raise AssertionError(msg)
try:
    a=json.loads(txt('content/worldgen/elizawy_cliff_rim_height_authority_v0_1.json'))
    req(a.get('pass')=='167Z109W12','W12 authority pass mismatch')
    provider=txt('crates/haven_assets/src/elizawy_cliff_provider.rs')
    shapes=txt('crates/haven_game/src/runtime_structural_cliff_shapes.rs')
    draw=txt('crates/haven_game/src/runtime_structural_cliff_draw.rs')
    collision=txt('crates/haven_game/src/runtime_surface_streaming_structural.rs')

    for token in [
        'Self::ContourNorthStraight => AuthoredSourceCell::new(2, 5)',
        'Self::ContourWestStraight => AuthoredSourceCell::new(0, 5)',
        'Self::ContourEastStraight => AuthoredSourceCell::new(4, 5)',
        'Self::ContourNorthWestConvex => AuthoredSourceCell::new(1, 5)',
        'Self::ContourNorthEastConvex => AuthoredSourceCell::new(3, 5)',
    ]:
        req(token in provider, f'clean authored rim mapping missing: {token}')
    req('Self::ContourEastStraight => AuthoredSourceCell::new(7, 6)' not in provider,
        'contaminated c7r6 east whole-cell contour returned')

    req('if face_segments <= 1' in shapes and '(face_segments - 1) as usize' in shapes,
        'middle-row count no longer uses tier_delta - 1')
    req('if face_segments <= 2' in shapes and '(face_segments - 2) as usize' in shapes,
        'cave continuation offset no longer begins above two tiers')
    req('recipe.leading' in draw and 'recipe.body' in draw and 'recipe.foot' in draw,
        'straight authored top/body/foot recipe missing')
    req('recipe.shoulder' in draw and 'recipe.body' in draw and 'recipe.foot' in draw,
        'diagonal authored shoulder/body/foot recipe missing')
    req(('2 + i32::try_from(crate::runtime_structural_cliff_shapes::authored_body_rows' in collision) or ('uniform_south_face_receiver_rows(south_segments)' in collision),
        'collision no longer matches top/shoulder + middle repeats + foot projection')

    preview=ROOT/a['acceptancePreview']
    req(preview.is_file() and preview.stat().st_size>1000,'W12 acceptance preview missing')
    req('Pass 167Z109W' in txt('crates/haven_game/src/runtime_diagnostics.rs'),'runtime diagnostics left W terrain lane')
    req('Pass167Z109W' in txt('README.md'),'README left W terrain lane')
    req('Pass167Z109W' in txt('docs/current/CURRENT_SOURCE_HANDOFF.md'),'handoff left W terrain lane')

    registry=json.loads(txt('content/build/validator_registry_v3.json'))
    source=[e for e in registry['validators'] if 'source' in e.get('profiles',[])]
    req(len(source)==10,f'source profile must remain 10, got {len(source)}')
    req(any(e['id'] in {'worldgen.elizawy-cliff-rim-height-v167z109w12','worldgen.elizawy-cliff-uniform-contour-height-v167z109w13'} for e in source),
        'W12 has no current terrain successor')
    req(not any(e['id']=='worldgen.elizawy-cliff-authored-vertical-recipe-restore-v167z109w11-2' for e in source),
        'W11.2 validator should be historical/full after W12')
    print('Pass167Z109W12 cliff rim + modular-height authority validated')
except Exception as e:
    print(f'Pass167Z109W12 validation FAILED: {e}')
    sys.exit(1)
