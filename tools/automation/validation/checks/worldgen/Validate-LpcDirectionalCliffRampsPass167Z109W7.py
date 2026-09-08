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
    a=load('content/worldgen/lpc_directional_cliff_ramp_authority_v0_1.json')
    req(a['pass']=='167Z109W7','W7 ramp authority pass mismatch')
    req(a['status']=='active','W7 ramp authority not active')
    rr=a['authoredRamps']['riseRight']; rl=a['authoredRamps']['riseLeft']
    req(rr['sourceGridSpan']==[3,5,3,4],'RiseRight source span drift')
    req(rl['sourceGridSpan']==[6,5,3,4],'RiseLeft source span drift')
    req(rr['worldVisualFootprintTiles']==[3,4] and rl['worldVisualFootprintTiles']==[3,4],'ramps must remain natural 3x4 stamps')
    req(rr['hostAnchorOffsetTiles']==[-1,-1] and rl['hostAnchorOffsetTiles']==[-1,-1],'ramp host anchor must align the 3x4 source envelope to the six-cell corridor bounding box')
    req(len(rr['traversableCorridorOffsetsFromHost'])==6 and len(rl['traversableCorridorOffsetsFromHost'])==6,'six-cell ramp corridor drift')
    for ramp in (rr, rl):
        xs=[p[0] for p in ramp['traversableCorridorOffsetsFromHost']]; ys=[p[1] for p in ramp['traversableCorridorOffsetsFromHost']]
        req([min(xs), min(ys), max(xs), max(ys)]==[-1,-1,1,2],'3x4 ramp stamp/corridor bounding box drift')
    p=a['placementContract']
    req(p['mirrorAllowed'] is False and p['rotationAllowed'] is False and p['stretchAllowed'] is False,'ramp transform gate drift')
    req(p['cropToSingleColumnAllowed'] is False,'partial ramp crop must remain forbidden')
    req(p['multiTierRampAllowed'] is False,'single ramp must remain one-tier')

    provider=txt('crates/haven_assets/src/lpc_cliff_ramp_provider.rs')
    for token in ['LpcDirectionalCliffRampRole','RiseRight','RiseLeft','AuthoredSourceStamp::new(3, 5, 3, 4)','AuthoredSourceStamp::new(6, 5, 3, 4)','(-1, -1)']:
        req(token in provider,f'authored ramp provider token missing: {token}')
    req('mirror' in provider.lower() and 'rotate' in provider.lower() and 'stretch' in provider.lower(),'provider source-safety comment missing')

    assets=txt('crates/haven_game/src/runtime_assets.rs')
    req('LPC_CLIFF_RAMP_GRASS_SOURCE_PATH' in assets,'runtime does not load certified ramp source')
    req('oga_cliff_source' in assets,'runtime ramp source handle missing')

    draw=txt('crates/haven_game/src/runtime_structural_cliff_draw.rs')
    ramp_draw=txt('crates/haven_game/src/runtime_structural_cliff_ramps.rs')
    for token in ['draw_authored_directional_ramp','complete_directional_ramp_owner_for_cell','complete_directional_ramp_role_for_host','stamp.width_cells','stamp.height_cells']:
        req(token in ramp_draw,f'runtime ramp renderer token missing: {token}')
    req('complete_directional_ramp_owner_for_cell' in draw,'main cliff pass does not honor ramp recipe ownership')
    req('deferred_ramp_overlays' in draw and 'for (owner_x, owner_y) in deferred_ramp_overlays' in draw, 'complete ramp stamp must replay after the base cliff pass')
    ramp=ramp_draw[ramp_draw.index('StructuralConnectorKind::Ramp => {'):ramp_draw.index('StructuralConnectorKind::Ladder => {')]
    req('draw_authored_directional_ramp' in ramp,'Ramp connector not routed to exact authored stamp')
    req('draw_diagonal_cliff_face' not in ramp and 'SOUTH_EAST_DIAGONAL_FACE' not in ramp and 'SOUTH_WEST_DIAGONAL_FACE' not in ramp,'fabricated W6 ramp composition returned')

    world=txt('crates/haven_world/src/structural_landform_generation.rs')
    ramp_world=txt('crates/haven_world/src/structural_landform_ramps.rs')
    for token in ['directional_ramp_corridor_indices','directional_ramp_orientation_for_candidate','Vec<(usize, usize, bool)>']:
        req(token in ramp_world,f'worldgen directional ramp token missing: {token}')
    req('for (upper_index, lower_index, rises_right) in ramp_edges' in world,'landform materializer does not consume directional ramp ownership')
    req('(-side, 2)' in ramp_world,'six-cell diagonal departure corridor missing')
    req('directional_ramp_corridors_follow_the_authored_six_cell_diagonals' in world,'ramp corridor unit test missing')
    req('directional_ramp_orientation_requires_the_complete_authored_level_footprint' in world,'ramp footprint validation test missing')

    shape=load('content/worldgen/elizawy_cliff_runtime_shape_catalog_v0_1.json')
    dr=shape['sourceComponents']['directionalRampReference']
    req(dr['runtimeStatus']=='runtime_certified_exact_3x4_stamps','runtime shape catalog ramp status drift')
    req(shape['runtimeGate']['ramps'].startswith('enabled_exact_authored_directional_3x4_stamps'),'runtime gate does not promote exact ramps')
    coll=load('content/worldgen/structural_collision_cliff_assembly_authority_v0_1.json')
    req(coll['collisionPolicy']['rampVisualFootprintIsCollisionAuthority'] is False,'ramp pixels must not own collision')
    req('six cardinal MountainPath cells' in coll['collisionPolicy']['rampCorridorRule'],'collision authority missing six-cell corridor')

    preview=ROOT/'docs/assets/previews/lpc_directional_cliff_ramps_pass167z109w7.png'
    req(preview.is_file() and preview.stat().st_size>1000,'W7 directional ramp acceptance board missing')
    gen=txt('tools/automation/terrain/Generate-LpcDirectionalCliffRampAcceptancePass167Z109W7.py')
    for token in ['Image.Resampling.NEAREST','c3-c5','c6-c8','six cardinal corridor']:
        req(token in gen,f'W7 acceptance generator token missing: {token}')

    registry=load('content/build/validator_registry_v3.json')
    source=[e for e in registry['validators'] if 'source' in e.get('profiles',[])]
    req(len(source) >= 10,f'source profile unexpectedly small: {len(source)}')
    ids={e['id'] for e in source}
    # The source profile has since advanced through H20/A14; W7 remains in the
    # full historical profile while newer structural authorities own source gating.
    req('worldgen.lpc-directional-cliff-ramps-v167z109w7' not in ids,
        'W7 should remain historical/full after H20/A14 structural normalization')
    req('worldgen.elizawy-cliff-connected-recipes-v167z109w6' not in ids,
        'W6 validator should remain historical/full after W7')
    req(any(i in ids for i in [
        'worldgen.h20v2-world-foundation-closure',
        'editor.h21-a14-universal-authoring-normalization-closure',
    ]), 'current source profile lacks the superseding structural/world authority')

    req('Current project authority' in txt('README.md'),'README current-project authority section missing')
    req('Havenwild Current Source Handoff' in txt('docs/current/CURRENT_SOURCE_HANDOFF.md'),'current source handoff missing')
    req(any(p in txt('crates/haven_game/src/runtime_diagnostics.rs') for p in ['Pass 167Z109W7','Pass 167Z109W15B']),'runtime diagnostics predate the directional-ramp authority')
    print('Pass167Z109W7 authored directional cliff ramps validated')
    print('- exact left/right 3x4 source stamps are runtime-promoted at natural scale')
    print('- fresh PCG owns the matching six-cell MountainPath corridor')
    print('- six-cell corridor suppresses conflicting hosts; complete 3x4 stamp replays after base cliffs')
    print('- structural topology remains collision/navigation authority')
    return 0

if __name__=='__main__':
    try: raise SystemExit(main())
    except Exception as e:
        print(f'Pass167Z109W7 validation FAILED: {e}')
        raise SystemExit(1)
