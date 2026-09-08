#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[5]

def req(v,m):
    if not v: raise AssertionError(m)
def txt(rel): return (ROOT/rel).read_text(encoding='utf-8-sig')
def load(rel): return json.loads(txt(rel))

def main():
    a=load('content/worldgen/authored_terrain_provider_authority_v0_1.json')
    req(a['revision'].startswith('167Z109W3'), 'W3 authority revision missing')
    req(a['status']=='active','W3 authority not active')
    req(a['cellContract']['wholeCellOnly'] is True,'whole-cell provider contract missing')
    req(a['w2Correction']['supersedesHalfCellTerminal'] is True,'W2 synthesized terminal not superseded')
    w2=load('content/worldgen/cliff_terminal_band_authority_v0_1.json')
    req(w2.get('status')=='superseded','W2 authority must be historical')

    provider=txt('crates/haven_assets/src/authored_terrain_provider.rs')
    for token in ['AUTHORED_TERRAIN_CELL_PX: u16 = 32','AuthoredSourceCell','AuthoredSourceStamp','resolve_authored_v7_surface_for_map']:
        req(token in provider, f'provider token missing: {token}')
    cache=txt('crates/haven_game/src/base_terrain_cache.rs')
    req('resolve_authored_v7_surface_for_map' in cache,'V7 surface cache not using authored provider')

    shapes=txt('crates/haven_game/src/runtime_structural_cliff_shapes.rs')
    for forbidden in ['source_crop(', 'SouthDoubleCap', 'NORTH_LIP_STRIP', 'SOUTH_LIP_STRIP', 'WEST_EDGE_STRIP', 'EAST_EDGE_STRIP']:
        req(forbidden not in shapes, f'forbidden synthesized/crop cliff path remains: {forbidden}')
    for token in ['SouthAuthoredTerminal','SOUTH_TERMINAL_LIP_ROW']:
        req(token in shapes, f'authored cliff role missing: {token}')
    req(
        ('AuthoredSourceCell::new(1, 6)' in shapes and 'AuthoredSourceCell::new(3, 6)' in shapes)
        or ('ElizaWyCliffCellRole::RoundedSouthWestLip' in shapes and 'ElizaWyCliffCellRole::RoundedSouthEastLip' in shapes),
        'authored diagonal source roles missing',
    )

    caps=txt('crates/haven_game/src/runtime_structural_cliff_caps.rs')
    for forbidden in ['* 0.5','left_source','right_source']:
        req(forbidden not in caps, f'half-tile terminal synthesis remains: {forbidden}')
    for token in ['draw_authored_south_terminal','target_x = global_x + column_offset as i32 - 1','SOUTH_TERMINAL_FOOT_ROW']:
        req(token in caps, f'natural-scale terminal token missing: {token}')

    draw=txt('crates/haven_game/src/runtime_structural_cliff_draw.rs')
    req('CliffVisualShape::SouthAuthoredTerminal' in draw,'authored terminal not wired')
    req('draw_authored_south_terminal' in draw,'authored terminal renderer call missing')
    req('draw_cliff_overlay_cell' in draw,'whole-cell overlay helper missing')
    req('draw_cliff_lip(' not in draw and 'draw_cliff_side_strip(' not in draw,'cropped strip helpers remain')

    collision=txt('crates/haven_game/src/runtime_surface_streaming_structural.rs')
    for token in ['structural_south_face_covers_column','is_south_authored_terminal','(tile.x - 1)..=(tile.x + 1)']:
        req(token in collision, f'authored stamp collision token missing: {token}')

    builder=txt('tools/automation/terrain/Build-ElizaWyCliffRuntimeOverlayPass167Z109D.py')
    req('strip_semantic_ground' in builder,'semantic-ground overlay mask missing')
    for forbidden in ['normalize_diagonal_receiver','adapt_owner_fill','left.w * 0.5']:
        req(forbidden not in builder,f'old receiver/synthesis path remains: {forbidden}')

    diagnostic=txt('crates/haven_game/src/runtime_diagnostics.rs')
    req('Pass 167Z109W' in diagnostic,'runtime diagnostic not advanced')
    handoff=txt('docs/current/CURRENT_SOURCE_HANDOFF.md')
    req('Pass167Z109W' in handoff and 'terrain' in handoff.lower(),'current handoff not advanced beyond W3')
    registry=load('content/build/validator_registry_v3.json')
    source=[e for e in registry['validators'] if 'source' in e.get('profiles',[])]
    req(len(source)==10,f'source profile must stay at 10, got {len(source)}')
    ids={e['id'] for e in source}
    req(any(i in ids for i in ['worldgen.authored-terrain-provider-v167z109w3','worldgen.elizawy-cliff-vocabulary-v167z109w4','worldgen.elizawy-cliff-vertical-modularity-v167z109w5','worldgen.elizawy-cliff-connected-recipes-v167z109w6','worldgen.lpc-directional-cliff-ramps-v167z109w7','worldgen.elizawy-generated-cliff-contours-v167z109w8','worldgen.elizawy-cliff-exact-visual-height-v167z109w11']),'W3 authored-provider authority has no current successor')
    req('worldgen.cliff-terminal-band-v167z109w2' not in ids,'W2 validator should be historical/full')
    print('Pass167Z109W3 unified authored terrain/cliff provider validated')
    print('- V7 uses exact authored four-corner tuple lookup')
    print('- ElizaWy cliff projection uses whole 32x32 cells/natural-scale stamps')
    print('- W2 half-tile terminal synthesis is retired')
    return 0

if __name__=='__main__':
    try: raise SystemExit(main())
    except Exception as e:
        print(f'Pass167Z109W3 validation FAILED: {e}')
        raise SystemExit(1)
