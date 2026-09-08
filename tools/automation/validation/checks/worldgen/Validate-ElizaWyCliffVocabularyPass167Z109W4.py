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
    cat=load('content/worldgen/elizawy_cliff_authored_vocabulary_v0_1.json')
    req(cat['pass']=='167Z109W4','W4 vocabulary pass mismatch')
    req(cat['status']=='active','W4 vocabulary not active')
    req(cat['source']['commit']=='f07f7f5892e67c932c68f70bb04472f2c64e46bc','pinned ElizaWy commit drift')
    req(cat['runtimeCells']['straightSouthFace']=={'top':[10,9],'body':[10,10],'foot':[10,11],'note':'Dedicated authored south-wall column; supersedes borrowing rounded plateau body/foot cells.'},'dedicated straight south column drift')
    req(cat['runtimeCells']['squareSouthLip']==[6,7],'square south lip drift')
    provider=txt('crates/haven_assets/src/elizawy_cliff_provider.rs')
    for token in ['ElizaWyCliffCellRole','StraightSouthTop => AuthoredSourceCell::new(10, 9)','StraightSouthBody => AuthoredSourceCell::new(10, 10)','StraightSouthFoot => AuthoredSourceCell::new(10, 11)','SquareSouthLip => AuthoredSourceCell::new(6, 7)','ElizaWyCliffStampRole']:
        req(token in provider,f'provider token missing: {token}')
    shapes=txt('crates/haven_game/src/runtime_structural_cliff_shapes.rs')
    req('ElizaWyCliffCellRole::StraightSouthTop' in shapes,'runtime straight top not provider-bound')
    req(('ElizaWyCliffCellRole::SquareSouthLip' in shapes) or ('ElizaWyCliffCellRole::ContourSouthStraightLip' in shapes),'runtime south lip not provider-bound')
    req('body: source_cell(AuthoredSourceCell::new(2, 3))' not in shapes,'rounded plateau body still used as straight wall')
    collision=txt('crates/haven_game/src/runtime_surface_streaming_structural.rs')
    req('straight south-face column is top + body + foot (three receiver rows)' in collision,'three-row straight collision contract missing')
    req('} else {\n        3\n    };' in collision,'straight collision depth is not three rows')
    preview=ROOT/'docs/assets/previews/elizawy_cliff_vocabulary_pass167z109w4.png'
    req(preview.is_file() and preview.stat().st_size>1000,'W4 vocabulary acceptance preview missing')
    gen=txt('tools/automation/terrain/Generate-ElizaWyCliffVocabularyAcceptancePass167Z109W4.py')
    req('Image.Resampling.NEAREST' in gen and 'crop_stamp' in gen,'acceptance generator missing exact-cell/window rendering')
    registry=load('content/build/validator_registry_v3.json')
    source=[e for e in registry['validators'] if 'source' in e.get('profiles',[])]
    req(len(source)==10,f'source profile must stay at 10, got {len(source)}')
    ids={e['id'] for e in source}
    req(any(i in ids for i in ['worldgen.elizawy-cliff-vertical-modularity-v167z109w5','worldgen.elizawy-cliff-connected-recipes-v167z109w6','worldgen.lpc-directional-cliff-ramps-v167z109w7','worldgen.elizawy-generated-cliff-contours-v167z109w8','worldgen.elizawy-cliff-exact-visual-height-v167z109w11']),'W4 vocabulary authority has no current successor')
    req('worldgen.elizawy-cliff-vocabulary-v167z109w4' not in ids,'W4 validator should be historical/full after W5')
    req('worldgen.authored-terrain-provider-v167z109w3' not in ids,'W3 validator should be historical/full')
    print('Pass167Z109W4 literal ElizaWy cliff vocabulary validated')
    print('- dedicated c10 r9-r11 straight south face is runtime authority')
    print('- square c6 r7 south lip is runtime authority')
    print('- exact-cell/window acceptance board exists')
    return 0
if __name__=='__main__':
    try: raise SystemExit(main())
    except Exception as e:
        print(f'Pass167Z109W4 validation FAILED: {e}')
        raise SystemExit(1)
