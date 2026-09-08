#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[5]

def req(v,m):
    if not v: raise AssertionError(m)
def txt(p): return (ROOT/p).read_text(encoding='utf-8-sig')
def load(p): return json.loads(txt(p))

def main():
    a=load('content/worldgen/elizawy_cliff_generated_contour_authority_v0_1.json')
    req(a['pass']=='167Z109W8','W8 generated contour authority pass mismatch')
    req(a['status']=='active','W8 generated contour authority not active')
    req(a['topologyAuthority']['freshPcgCertifiedMasks']==[1,2,3,4,5,6,8,9,10,12],'fresh-PCG certified cliff mask set drift')
    req(a['topologyAuthority']['freshPcgRejectedThinMasks']==[7,11,13,14,15],'thin-cap normalization mask set drift')
    req(a['sourceSafety']['halfTileSynthesis'] is False,'half-tile cliff synthesis must remain forbidden')
    req(a['sourceSafety']['textureStretching'] is False,'cliff stretching must remain forbidden')
    req(a['sourceSafety']['arbitraryMirrorOrRotation'] is False,'directional source transforms must remain forbidden')

    cave=load('content/worldgen/cliff_cave_mouth_policy_v0_1.json')
    req(cave['pass']=='167Z109W8','W8 cave mouth policy pass mismatch')
    req(cave['defaultCave']['sourceGridSpan']==[6,9,1,3],'default generated cave must stay exact narrow source recipe')
    req(cave['defaultCave']['visualWidthTiles']==1,'default generated cave width must stay one tile')
    req(cave['defaultCave']['widthDependsOnCliffHeight'] is False,'cave width must not depend on cliff height')
    req(cave['largeTunnel']['sourceGridSpan']==[7,9,3,3],'reserved large-tunnel source recipe drift')
    req(cave['largeTunnel']['automaticSelectionFromFaceSegments'] is False,'large tunnel may not be selected automatically')

    provider=txt('crates/haven_assets/src/elizawy_cliff_provider.rs')
    for token in [
        'ElizaWyGeneratedCliffContourRole', 'ContourNorthStraight', 'ContourWestStraight',
        'ContourEastStraight', 'ContourNorthWestConvex', 'ContourNorthEastConvex',
        'AuthoredSourceCell::new(5, 5)', 'AuthoredSourceCell::new(7, 5)',
        'ContourSouthStraightLip',
    ]:
        req(token in provider,f'W8 exact ElizaWy contour provider token missing: {token}')

    companion=txt('crates/haven_assets/src/lpc_cliff_ramp_provider.rs')
    for token in ['LpcCliffContourStampRole','VerticalRidgeMiddle','AuthoredSourceStamp::new(8, 2, 3, 1)','(-1, 0)']:
        req(token in companion,f'W8 exact ridge provider token missing: {token}')

    runtime=txt('crates/haven_game/src/runtime_structural_cliff_contours.rs')
    for token in ['draw_non_south_connected_contour','NORTH_EAST_CORNER_CELL','NORTH_WEST_CORNER_CELL','draw_authored_vertical_ridge_middle','VerticalRidgeMiddle']:
        req(token in runtime,f'W8 runtime connected-contour token missing: {token}')
    req('draw_single_edge_compatibility_rim' not in txt('crates/haven_game/src/runtime_structural_cliff_draw.rs'),'retired generic single-edge compatibility rim returned')

    draw=txt('crates/haven_game/src/runtime_structural_cliff_draw.rs')
    req('CAVE_NARROW_SOURCE' in draw,'ordinary cave renderer must use narrow authored recipe')
    req('center.face_segments > 1' not in draw,'ordinary cave width must not switch from cliff height')
    req('extra_authored_body_rows' in draw,'taller cliffs must anchor the fixed cave below added authored rock continuation')
    connectors=txt('crates/haven_game/src/runtime_structural_connectors.rs')
    req('Reserved authored 3x3 portal for an explicit road/cart mountain tunnel' in connectors,'wide cave/tunnel reservation comment missing')
    req('#[allow(dead_code)]' in connectors and 'CAVE_WIDE_SOURCE' in connectors,'wide tunnel source must stay reserved, not height-selected')

    masks=txt('crates/haven_world/src/structural_landform_masks.rs')
    req('generated_cleanup_leaves_no_three_edge_or_isolated_raised_hosts' in masks,'fresh-PCG thin-cap cleanup regression test missing')
    req('support >= 2' in masks,'fresh-PCG contour support gate missing')

    preview=ROOT/'docs/assets/previews/elizawy_cliff_generated_contours_pass167z109w8.png'
    req(preview.is_file() and preview.stat().st_size>1000,'W8 generated-cliff acceptance board missing')
    gen=txt('tools/automation/terrain/Generate-ElizaWyCliffGeneratedContourAcceptancePass167Z109W8.py')
    for token in ['Image.Resampling.NEAREST','1,2,3,4,5,6,8,9,10,12','7 / 11 / 13 / 14 / 15','c8-c10 r2']:
        req(token in gen,f'W8 acceptance generator token missing: {token}')

    shape=load('content/worldgen/elizawy_cliff_runtime_shape_catalog_v0_1.json')
    req(shape['pass']=='167Z109W8','runtime cliff shape catalog not advanced to W8')
    req(shape['runtimeGate']['generatedContourGrammar'].startswith('frozen_10_mask'),'runtime gate missing W8 generated contour freeze')
    req(shape['runtimeGate']['caves'].startswith('default_1_tile'),'runtime gate missing one-tile default cave policy')
    coll=load('content/worldgen/structural_collision_cliff_assembly_authority_v0_1.json')
    req(coll['revision'].startswith('167Z109W8-'),'collision authority not advanced to W8')
    req('one-tile-wide' in coll['collisionPolicy']['caveRule'],'collision cave policy not normalized to one-tile default mouth')

    registry=load('content/build/validator_registry_v3.json')
    source=[e for e in registry['validators'] if 'source' in e.get('profiles',[])]
    req(len(source)==10,f'source profile must stay at 10, got {len(source)}')
    ids={e['id'] for e in source}
    later_current = any(i in ids for i in [
        'worldgen.elizawy-cliff-straight-face-anchor-v167z109w9',
        'worldgen.elizawy-cliff-elevation-delta-anchor-v167z109w10',
        'worldgen.elizawy-cliff-exact-visual-height-v167z109w11',
    ])
    if later_current:
        req('worldgen.elizawy-generated-cliff-contours-v167z109w8' not in ids,'W8 should be historical/full after W9+')
    else:
        req('worldgen.elizawy-generated-cliff-contours-v167z109w8' in ids,'W8 validator not current source authority')
    req('worldgen.lpc-directional-cliff-ramps-v167z109w7' not in ids,'W7 validator should be historical/full after W8')

    req(any(x in txt('README.md') for x in ['Pass167Z109W8','Pass167Z109W9','Pass167Z109W10','Pass167Z109W11']),'README predates W8')
    req(any(x in txt('docs/current/CURRENT_SOURCE_HANDOFF.md') for x in ['Pass167Z109W8','Pass167Z109W9','Pass167Z109W10','Pass167Z109W11']),'handoff predates W8')
    req(any(x in txt('crates/haven_game/src/runtime_diagnostics.rs') for x in ['Pass 167Z109W8','Pass 167Z109W9','Pass 167Z109W10','Pass 167Z109W11']),'runtime diagnostics predates W8')
    print('Pass167Z109W8 generated cliff grammar freeze validated')
    print('- fresh PCG cliff output is restricted to the ten stable authored contour masks')
    print('- three/four-edge one-cell caps are normalized out instead of receiving fake art')
    print('- exact north/east/west corners and the authored narrow ridge are source-bound')
    print('- ordinary caves stay one tile wide regardless of cliff height')
    return 0

if __name__=='__main__':
    try: raise SystemExit(main())
    except Exception as e:
        print(f'Pass167Z109W8 validation FAILED: {e}')
        raise SystemExit(1)
