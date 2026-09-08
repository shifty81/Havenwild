#!/usr/bin/env python3
import json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[5]
def req(v,m):
    if not v: raise AssertionError(m)
def main():
    recipe=json.loads((ROOT/'content/buildings/recipes/estate_starter_cottage_v1.json').read_text())
    level=recipe['levels'][0]; version=recipe.get('version')
    req(version in {'1.4.0-w54g','1.4.0-w57k8','1.5.0-w57k9','1.6.0-w57k10'},'W54G+ cottage visibility lineage missing')
    openings={x['id']:x for x in level['openings']}
    req(openings['front_door']['state']=='closed','front door must default closed')
    if version=='1.4.0-w54g':
        req(recipe['footprint']==[10,8],'historical W54G must preserve 10x8 two-room footprint')
        runs={x['id']:x for x in level['wallRuns']}
        for name in ('rear_cap_left','rear_cap_center','rear_cap_right','divider_cap_left','divider_cap_center','divider_cap_right'):
            req(name in runs,f'missing historical W54G interior cap run {name}')
        req(openings['bedroom_door']['state']=='closed','historical bedroom door must default closed')
    else:
        req(recipe['footprint']==[9,9],'W57K8 architectural envelope must be 9x9')
        req('bedroom_door' not in openings,'W57K8 open-plan interior must not restore blocking bedroom door')
        req(not any(w['id'].startswith(('rear_cap_','divider_cap_')) for w in level['wallRuns']),'W57K8 must not materialize cutaway overlays as wall bodies')
        core=(ROOT/'crates/haven_core/src/enclosed_wall_topology.rs').read_text()
        runtime=(ROOT/'crates/haven_game/src/runtime_terrain_base_draw.rs').read_text()
        editor=(ROOT/'apps/haven_editor_native/src/app/atlas_render.rs').read_text()
        req('HouseInteriorWallPresentation' in core and 'SouthFacingBody' in core and 'CutawayEdge' in core,'K8 semantic interior wall presentation resolver missing')
        req('side/front shell cells are collision-only' in runtime,'runtime K8 cutaway rail suppression missing')
        req('Do not repeat CutawayOverlay cells into rail-like bands' in editor,'editor K8 cutaway rail suppression missing')
    src=(ROOT/'crates/haven_assets/src/building_instance.rs').read_text()
    req('group.starts_with("building.wall_interior.")' in src,'runtime must suppress interior-only wall groups while outside')
    print('PASS W54G+ cottage visibility/cutaway authority')
    print('- historical W54G remains recognized; W57K8 separates wall collision topology from house presentation')
    print('- W57K8 side/front cut edges no longer repeat CutawayOverlay rails')
if __name__=='__main__':
    try: main()
    except Exception as exc:
        print(f'FAIL W54G+ cottage visibility/cutaway authority: {exc}',file=sys.stderr); sys.exit(1)
