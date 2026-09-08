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
    a=load('content/worldgen/elizawy_cliff_connected_recipe_authority_v0_1.json')
    req(a['pass']=='167Z109W6','W6 authority pass mismatch')
    req(a['status']=='active','W6 authority not active')
    req(a['source']['commit']=='f07f7f5892e67c932c68f70bb04472f2c64e46bc','ElizaWy source commit drift')
    g=a['runtimePromotionContract']
    req(g['individualSourceCellPromotionAllowed'] is False,'raw cell promotion must remain disabled')
    req(g['normalizedConnectedRecipeRequired'] is True,'connected recipe gate missing')
    req(g['halfTileSynthesisAllowed'] is False and g['stretchAllowed'] is False,'visual synthesis gate drift')
    req(a['constructionAndReferenceRegions']['complexTransitionStrip']['standaloneRamp'] is False,'c8 strip must not be a standalone ramp')
    req(a['collisionContract']['extraRowsPerAdditionalStructuralTier']==1,'W5 one-row-per-tier collision rule drift')

    provider=txt('crates/haven_assets/src/elizawy_cliff_provider.rs')
    for token in [
        'ElizaWyCliffCertification','CompatibilityTemplateOnly','RejectedPartialAssembly',
        'ElizaWyCliffConnectedRecipeRole','ComplexTransitionStripReference',
        'SideEntryRampPending','SquarePlateauConstructionTemplate'
    ]:
        req(token in provider,f'provider source-certification token missing: {token}')
    req('SquareNorthWestCorner' not in provider and 'SquareNorthEastCorner' not in provider,'guessed square corner cell promotion returned')

    draw=txt('crates/haven_game/src/runtime_structural_cliff_draw.rs')
    w8_current=any(p in txt('README.md') for p in ['Pass167Z109W8','Pass167Z109W9','Pass167Z109W10','Pass167Z109W11'])
    if w8_current:
        req('draw_single_edge_compatibility_rim' not in draw,'retired W6 compatibility helper returned after W8 contour freeze')
        req('draw_non_south_connected_contour' in draw,'W8 connected contour owner missing from cliff draw')
    else:
        req('draw_single_edge_compatibility_rim' in draw,'single-edge compatibility gate missing')
        req('Never\n        // stack two or three' in draw or 'Never\n        // stack two or three' in draw.replace('\r',''),'combined template overpaint guard missing')
    # Later passes may promote exact authored ramps/contours, but the fabricated W6
    # rounded-corner ramp compositor must never return.
    ramp_source=txt('crates/haven_game/src/runtime_structural_cliff_ramps.rs')
    req('draw_diagonal_cliff_face' not in ramp_source,'fake rounded-corner ramp compositor still active')
    req('SOUTH_EAST_DIAGONAL_FACE' not in ramp_source and 'SOUTH_WEST_DIAGONAL_FACE' not in ramp_source,'fake ramp flank source remains')

    shapes=txt('crates/haven_game/src/runtime_structural_cliff_shapes.rs')
    req('construction template' in shapes.lower(),'square-template compatibility warning missing')
    req('authored_body_rows(face_segments)' in shapes,'W5 authored height helper missing')

    for p in [
        'content/worldgen/structural_collision_cliff_assembly_authority_v0_1.json',
        'content/worldgen/elizawy_cliff_sheet_role_catalog_v0_1.json',
        'content/worldgen/elizawy_cliff_complete_mapping_v0_1.json'
    ]:
        body=txt(p)
        req('+2 rows per additional' not in body and 'adds two rock-body rows' not in body,f'stale W5 height multiplier remains in {p}')

    preview=ROOT/'docs/assets/previews/elizawy_cliff_connected_recipe_authority_pass167z109w6.png'
    req(preview.is_file() and preview.stat().st_size>1000,'W6 connected-recipe acceptance board missing')
    gen=txt('tools/automation/terrain/Generate-ElizaWyCliffConnectedRecipeAuthorityPass167Z109W6.py')
    for token in ['Image.Resampling.NEAREST','construction template','Rejected partial ramp interpretation']:
        req(token in gen,f'W6 acceptance generator token missing: {token}')

    registry=load('content/build/validator_registry_v3.json')
    source=[e for e in registry['validators'] if 'source' in e.get('profiles',[])]
    req(len(source)==10,f'source profile must stay at 10, got {len(source)}')
    ids={e['id'] for e in source}
    if any(i in ids for i in ['worldgen.lpc-directional-cliff-ramps-v167z109w7','worldgen.elizawy-generated-cliff-contours-v167z109w8','worldgen.elizawy-cliff-straight-face-anchor-v167z109w9','worldgen.elizawy-cliff-elevation-delta-anchor-v167z109w10','worldgen.elizawy-cliff-exact-visual-height-v167z109w11']):
        req('worldgen.elizawy-cliff-connected-recipes-v167z109w6' not in ids,'W6 should be historical/full after W7')
    else:
        req('worldgen.elizawy-cliff-connected-recipes-v167z109w6' in ids,'W6 validator not current source authority')
        req('worldgen.elizawy-cliff-vertical-modularity-v167z109w5' not in ids,'W5 validator should be historical/full after W6')

    readme=txt('README.md'); handoff=txt('docs/current/CURRENT_SOURCE_HANDOFF.md'); diag=txt('crates/haven_game/src/runtime_diagnostics.rs')
    req(any(p in readme for p in ['Pass167Z109W6','Pass167Z109W7','Pass167Z109W8','Pass167Z109W9','Pass167Z109W10','Pass167Z109W11']),'README predates W6')
    req(any(p in handoff for p in ['Pass167Z109W6','Pass167Z109W7','Pass167Z109W8','Pass167Z109W9','Pass167Z109W10','Pass167Z109W11']),'handoff predates W6')
    req(any(p in diag for p in ['Pass 167Z109W6','Pass 167Z109W7','Pass 167Z109W8','Pass 167Z109W9','Pass 167Z109W10','Pass 167Z109W11']),'runtime diagnostic predates W6')

    print('Pass167Z109W6 connected-recipe cliff source authority validated')
    print('- raw source cells remain addresses; runtime promotion is recipe-level')
    print('- combined square-template overpaint is retired')
    print('- fabricated front-facing ramp cliff art is retired')
    print('- W5 one-authored-middle-row-per-tier visual/collision contract is preserved')
    return 0

if __name__=='__main__':
    try: raise SystemExit(main())
    except Exception as e:
        print(f'Pass167Z109W6 validation FAILED: {e}')
        raise SystemExit(1)
