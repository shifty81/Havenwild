#!/usr/bin/env python3
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[5]
def req(ok,msg):
    if not ok: raise AssertionError(msg)
def txt(rel): return (ROOT/rel).read_text(encoding='utf-8')
def main():
    authority=json.loads(txt('content/worldgen/elizawy_cliff_straight_face_anchor_authority_v0_1.json'))
    req(authority.get('pass')=='167Z109W9','W9 authority pass mismatch')
    contract=authority.get('contract',{})
    req(contract.get('straightSouthHostOwnsCompatibilityLip') is False,'straight host compatibility lip must stay retired')
    req(contract.get('straightSouthTopProjectionOffsetRows')==1,'straight top must begin one projected row below plateau host')
    draw=txt('crates/haven_game/src/runtime_structural_cliff_draw.rs')
    req('draw_cliff_overlay_cell(texture, SOUTH_LIP_CELL, global_x, global_y)' not in draw,'obsolete straight south compatibility lip is still drawn')
    req('SOUTH_LIP_CELL' not in '\n'.join(draw.splitlines()[:12]), 'obsolete SOUTH_LIP_CELL still imported by draw module')
    req('SOUTH_STRAIGHT_FACE' in draw,'dedicated straight face recipe missing')
    req('let world_y = (global_y + 1) as f32 * TILE_SIZE;' in draw,'straight face projection no longer begins one receiver-facing row below host')
    shapes=txt('crates/haven_game/src/runtime_structural_cliff_shapes.rs')
    req('StraightSouthTop' in shapes and 'StraightSouthBody' in shapes and 'StraightSouthFoot' in shapes,'dedicated straight top/body/foot recipe incomplete')
    req(any(x in txt('crates/haven_game/src/runtime_diagnostics.rs') for x in ['Pass 167Z109W9','Pass 167Z109W10']),'runtime diagnostics predates W9')
    req(any(x in txt('README.md') for x in ['Pass167Z109W9','Pass167Z109W10']),'README predates W9')
    req(any(x in txt('docs/current/CURRENT_SOURCE_HANDOFF.md') for x in ['Pass167Z109W9','Pass167Z109W10']),'handoff predates W9')
    print('Pass167Z109W9 straight cliff face anchor correction validated')
if __name__=='__main__':
    try: main()
    except Exception as e:
        print(f'Pass167Z109W9 validation FAILED: {e}')
        raise
