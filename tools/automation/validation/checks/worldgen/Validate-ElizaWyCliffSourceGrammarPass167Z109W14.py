#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[5]

def req(v,m):
    if not v:
        raise AssertionError(m)
def txt(p):
    return (ROOT/p).read_text(encoding='utf-8-sig')
def load(p):
    return json.loads(txt(p))

def main():
    a=load('content/worldgen/elizawy_cliff_source_grammar_authority_v0_1.json')
    req(a['pass']=='167Z109W14','W14 source grammar authority pass mismatch')
    req(a['status']=='active','W14 source grammar authority not active')
    req(a['source']['commit']=='f07f7f5892e67c932c68f70bb04472f2c64e46bc','pinned ElizaWy commit drift')
    req(a['ordinarySouthRoles']['leftAngle']=={
        'crest':[1,7],'body':[1,3],'foot':[1,8],'runtimeFamily':'SOUTH_WEST_DIAGONAL_FACE'
    },'W14 left-angle source role drift')
    req(a['ordinarySouthRoles']['straight']=={
        'crest':[2,7],'body':[2,3],'foot':[2,8],'runtimeFamily':'SOUTH_STRAIGHT_FACE'
    },'W14 straight source role drift')
    req(a['ordinarySouthRoles']['rightAngle']=={
        'crest':[3,7],'body':[3,3],'foot':[3,8],'runtimeFamily':'SOUTH_EAST_DIAGONAL_FACE'
    },'W14 right-angle source role drift')
    req(a['heightContract']['receiverRowsBelowHost']=='edge_tier_delta','W14 receiver height no longer literal')
    req(a['heightContract']['crestCountsAsReceiverFacingHeight'] is False,'crest must not count as receiver-facing height')
    req(a['sourceSafety']['userQuickPasteupIsSource'] is False,'user mockup may not become source authority')
    req('cave interior wall tiling' in a['outOfScope'],'caves must remain deferred in W14')

    provider=txt('crates/haven_assets/src/elizawy_cliff_provider.rs')
    for token in [
        'StraightSouthTop => AuthoredSourceCell::new(2, 7)',
        'StraightSouthBody => AuthoredSourceCell::new(2, 3)',
        'StraightSouthFoot => AuthoredSourceCell::new(2, 8)',
    ]:
        req(token in provider,f'W14 straight source binding missing: {token}')
    req('StraightSouthTop => AuthoredSourceCell::new(10, 9)' not in provider,
        'old c10r9 ordinary straight authority returned')

    shapes=txt('crates/haven_render/src/structural_cliff_visual.rs')
    for token in [
        'crest: role_cell(ElizaWyCliffCellRole::RoundedSouthWestShoulder)',
        'body: role_cell(ElizaWyCliffCellRole::RoundedSouthWestBody)',
        'foot: role_cell(ElizaWyCliffCellRole::RoundedSouthWestFoot)',
        'crest: role_cell(ElizaWyCliffCellRole::RoundedSouthEastShoulder)',
        'body: role_cell(ElizaWyCliffCellRole::RoundedSouthEastBody)',
        'foot: role_cell(ElizaWyCliffCellRole::RoundedSouthEastFoot)',
        'pub const SOUTH_TERMINAL_CREST_ROW',
        'source_cell(AuthoredSourceCell::new(2, 7))',
        'source_cell(AuthoredSourceCell::new(2, 3))',
        'source_cell(AuthoredSourceCell::new(2, 8))',
        '1 + authored_body_rows(face_segments)',
    ]:
        req(token in shapes,f'W14 source/height shape token missing: {token}')
    req('pub lip: Rect' not in shapes and 'pub shoulder: Rect' not in shapes,
        'ordinary diagonal still owns an extra lip/shoulder receiver row')
    req('(face_segments - 1) as usize' in shapes,
        'W14 body rows no longer map structural delta to delta-1')

    draw=txt('crates/haven_game/src/runtime_structural_cliff_draw.rs')
    req('self.draw_cliff_source_cell(texture, recipe.crest, world_x, world_y);' in draw,
        'diagonal crest is not on host row')
    req('let receiver_x = global_x + low_side_dx;' in draw,
        'W13 low-side diagonal receiver ownership was lost')
    req('let first_body_offset = 1_i32;' in draw,
        'W14 diagonal receiver projection no longer begins one row below host')
    req('self.draw_cliff_source_cell(texture, leading, world_x, host_y);' in draw,
        'straight crest is not on host row')
    req('let foot_y = global_y + 1 + body_rows as i32;' in draw,
        'straight foot no longer terminates at literal structural height')

    caps=txt('crates/haven_game/src/runtime_structural_cliff_caps.rs')
    req('SOUTH_TERMINAL_CREST_ROW' in caps,'W14 terminal crest row missing')
    req('global_y + 1 + row_index as i32' in caps and 'global_y + 1 + body_rows as i32' in caps,
        'W14 terminal body/foot height no longer matches straight/diagonal')

    collision=txt('crates/haven_game/src/runtime_surface_streaming_structural.rs')
    req('uniform_south_face_receiver_rows(south_segments)' in collision,
        'collision no longer follows shared W14 literal receiver-height helper')
    tests=txt('crates/haven_game/src/runtime_surface_streaming_tests.rs')
    req('[(1_u8, 1_i32), (2, 2), (3, 3), (4, 4)]' in tests,
        '1/2/3/4 literal collision-depth regression table missing')

    connector_draw=txt('crates/haven_game/src/runtime_structural_cliff_ramps.rs')
    req('self.draw_cliff_feature_vertical_face(' in connector_draw,
        'ladder connector was accidentally moved onto ordinary W14 host-row crest semantics')
    req('pub(super) fn draw_cliff_feature_vertical_face' in draw,
        'preserved fixed-feature vertical renderer missing')

    ramps=txt('crates/haven_assets/src/lpc_cliff_ramp_provider.rs')
    for token in [
        'Self::RiseRight => AuthoredSourceStamp::new(3, 5, 3, 4)',
        'Self::RiseLeft => AuthoredSourceStamp::new(6, 5, 3, 4)',
        'never mirrors, rotates, crops, or stretches',
    ]:
        req(token in ramps,f'W7 authored ramp contract drift: {token}')

    preview=ROOT/a['acceptancePreview']
    req(preview.is_file() and preview.stat().st_size>1000,'W14 cliff-only acceptance board missing')

    req('Pass 167Z109W14' in txt('crates/haven_game/src/runtime_diagnostics.rs'),'runtime diagnostics not W14')

    registry=load('content/build/validator_registry_v3.json')
    source=[e for e in registry['validators'] if 'source' in e.get('profiles',[])]
    ids={e['id'] for e in source}
    req('worldgen.elizawy-cliff-source-grammar-v167z109w14' in ids,
        'W14 validator is not current source terrain authority')
    req('worldgen.elizawy-cliff-uniform-contour-height-v167z109w13' not in ids,
        'W13 validator should be historical/full after W14')

    print('Pass167Z109W14 ElizaWy cliff source grammar validated')
    print('- straight: c2r7 / c2r3 / c2r8')
    print('- left:     c1r7 / c1r3 / c1r8')
    print('- right:    c3r7 / c3r3 / c3r8')
    print('- receiver depth: literal structural tier delta')
    print('- W13 low-side diagonal ownership preserved')
    print('- W7 authored 3x4 ramps preserved')
    print('- caves deferred')
    return 0

if __name__=='__main__':
    try:
        raise SystemExit(main())
    except Exception as e:
        print(f'Pass167Z109W14 validation FAILED: {e}')
        raise SystemExit(1)
