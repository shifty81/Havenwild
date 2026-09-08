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
    a=load('content/worldgen/elizawy_cliff_vertical_modularity_v0_1.json')
    req(a['pass']=='167Z109W5','W5 authority pass mismatch')
    req(a['status']=='active','W5 vertical authority not active')
    req(a['source']['commit']=='f07f7f5892e67c932c68f70bb04472f2c64e46bc','ElizaWy source commit drift')
    s=a['structuralContract']
    req(s['extraMiddleRowsPerAdditionalTier']==1,'extra tier must insert exactly one authored middle row')
    req(s['formula']=='body_rows = max(face_segments, 1)','body-row formula drift')
    req(s['structuralLevelsChangedByThisPass'] is False,'W5 may not change structural topology')
    fam=a['certifiedRepeatFamilies']
    req(fam['straightSouth']['repeatBody']==[10,10],'straight repeat body drift')
    req(fam['roundedSouthWest']['repeatBody']==[1,3],'SW repeat body drift')
    req(fam['roundedSouthEast']['repeatBody']==[3,3],'SE repeat body drift')
    req(fam['ladderA']['repeatBody']==[11,10] and fam['ladderB']['repeatBody']==[13,10],'ladder repeat body drift')
    req(fam['roundedSouthTerminal']['repeatBodyRow']==[[1,3],[2,3],[3,3]],'terminal repeat row drift')

    provider=txt('crates/haven_assets/src/elizawy_cliff_provider.rs')
    for token in ['is_repeatable_vertical_body','Self::StraightSouthBody','Self::RoundedSouthWestBody','Self::RoundedSouthEastBody','Self::LadderABody','Self::LadderBBody']:
        req(token in provider,f'provider repeat token missing: {token}')

    shapes=txt('crates/haven_game/src/runtime_structural_cliff_shapes.rs')
    req('pub(super) const fn authored_body_rows(face_segments: u8) -> usize' in shapes,'authored body-row helper missing')
    req('authored_face_rows(face_segments)' in shapes,'current exact face-row successor missing')
    req('extra_authored_body_rows' in shapes,'extra body-row helper missing')

    draw=txt('crates/haven_game/src/runtime_structural_cliff_draw.rs')
    caps=txt('crates/haven_game/src/runtime_structural_cliff_caps.rs')
    collision=txt('crates/haven_game/src/runtime_surface_streaming_structural.rs')
    for body,name in [(draw,'draw'),(caps,'caps')]:
        req('authored_body_rows(face_segments)' in body,f'{name} does not use authored body-row count')
        req('saturating_sub(1)) * 2' not in body,f'{name} still doubles vertical rows')
    req('authored_face_rows' in collision,'collision is not tied to current authored face-row authority')
    req('saturating_sub(1)) * 2' not in collision,'collision still doubles vertical rows')
    req('structural tier delta' in collision.lower(),'collision exact-height contract comment missing')

    req(a['featureHeightPolicy']['cave'].startswith('Cave mouth is a fixed authored terminal feature'),'cave fixed-feature policy missing')
    req(a['featureHeightPolicy']['ramp'].startswith('One structural tier only'),'ramp one-tier policy missing')

    preview=ROOT/'docs/assets/previews/elizawy_cliff_vertical_modularity_pass167z109w5.png'
    req(preview.is_file() and preview.stat().st_size>1000,'W5 modularity acceptance preview missing')
    gen=txt('tools/automation/terrain/Generate-ElizaWyCliffVerticalModularityAcceptancePass167Z109W5.py')
    for token in ['Image.Resampling.NEAREST','for seg in (1,2,3)','whole 3-cell body row']:
        req(token in gen,f'W5 preview generator token missing: {token}')

    registry=load('content/build/validator_registry_v3.json')
    source=[e for e in registry['validators'] if 'source' in e.get('profiles',[])]
    req(len(source)==10,f'source profile must stay at 10, got {len(source)}')
    ids={e['id'] for e in source}
    req(any(i in ids for i in ['worldgen.elizawy-cliff-vertical-modularity-v167z109w5','worldgen.elizawy-cliff-connected-recipes-v167z109w6','worldgen.lpc-directional-cliff-ramps-v167z109w7','worldgen.elizawy-generated-cliff-contours-v167z109w8','worldgen.elizawy-cliff-exact-visual-height-v167z109w11']),'W5 vertical authority has no current successor')
    req('worldgen.elizawy-cliff-vocabulary-v167z109w4' not in ids,'W4 validator should be historical/full')

    req('Pass167Z109W' in txt('README.md'),'README not advanced through W terrain lane')
    req('Pass167Z109W' in txt('docs/current/CURRENT_SOURCE_HANDOFF.md'),'handoff not advanced through W terrain lane')
    req('Pass 167Z109W' in txt('crates/haven_game/src/runtime_diagnostics.rs'),'runtime diagnostic not advanced through W terrain lane')

    print('Pass167Z109W5 authored vertical cliff modularity validated')
    print('- one complete authored middle module per structural tier')
    print('- straight, rounded, terminal and ladder families share the same height rule')
    print('- collision grows by the same authored-row count')
    print('- cave/waterfall mouths remain fixed features pending their own continuation certification')
    return 0

if __name__=='__main__':
    try: raise SystemExit(main())
    except Exception as e:
        print(f'Pass167Z109W5 validation FAILED: {e}')
        raise SystemExit(1)
