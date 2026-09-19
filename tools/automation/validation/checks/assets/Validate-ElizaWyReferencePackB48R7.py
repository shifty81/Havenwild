#!/usr/bin/env python3
"""Non-mutating B48R7 reference-pack / source-crop validator. No runtime promotion."""
import argparse, io, json, hashlib, sys, zipfile
from pathlib import Path

def digest(raw): return hashlib.sha256(raw).hexdigest()
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--repo',type=Path,default=Path(__file__).resolve().parents[5])
    ap.add_argument('--reference-zip',type=Path)
    ap.add_argument('--original-terrain-zip',type=Path)
    ap.add_argument('--original-test-scenes-zip',type=Path)
    args=ap.parse_args()
    src=args.repo/'content/assets/lpc/elizawy_waterfall_component_review_b48r7_v0_2.json'
    data=json.loads(src.read_text(encoding='utf-8'))
    assert data['schema']=='havenwild.elizawy.waterfall_component_review.v0_2'
    assert data['productionEnabled'] is False and data['doNotOverrideExistingRenderer'] is True
    cells=data['sourceComponents']
    assert len(cells)==28 and len([c for c in cells if c['id'].startswith('north_')])==4
    for c in cells:
        x,y,w,h=c['sourceRectPx']; assert x>=0 and y>=0 and w>0 and h>0
        assert x+w<=512 and y+h<=608
        assert c['individualRuntimePlacementAllowed'] is False
    assert data['gates']['runtimePromotion']=='blocked'
    crosswalk=json.loads((args.repo/'content/assets/lpc/elizawy_summer_atlas_source_crosswalk_b48r7_v0_1.json').read_text(encoding='utf-8'))
    assert crosswalk['count']==290 and len(crosswalk['entries'])==290
    assert crosswalk['unique']+crosswalk['ambiguous']+crosswalk['unmatched']==290
    assert all(e['roleCertified'] is False for e in crosswalk['entries'])
    assert data['animation']['frameCount']==4 and data['animation']['phaseLockAllParts'] is True
    print('PASS metadata: 28 components, four frames, north guarded, no runtime promotion')
    if not args.reference_zip or not args.original_terrain_zip:
        print('NOT RUN: source-image/pixel checks (pass both --reference-zip and --original-terrain-zip)')
        return 0
    try:from PIL import Image
    except ImportError:raise SystemExit('ERROR Pillow required for source pixel audit')
    with zipfile.ZipFile(args.reference_zip) as ref,zipfile.ZipFile(args.original_terrain_zip) as orig:
        a=ref.read('Terrain/Waterfall.png');b=orig.read('Terrain/Waterfall.png')
        assert digest(a)==data['source']['referenceWaterfallSha256']
        assert digest(b)==data['source']['sha256']
        i=Image.open(io.BytesIO(a)).convert('RGBA');j=Image.open(io.BytesIO(b)).convert('RGBA')
        assert i.size==(384,608) and j.size==(512,608)
        assert i.tobytes()==j.crop((0,0,384,608)).tobytes()
        assert len(ref.read('FX/Splash.png'))>0 # presence check
        for c in cells:
            x,y,w,h=c['sourceRectPx']
            if x+w<=384:
                assert i.crop((x,y,x+w,y+h)).tobytes()==j.crop((x,y,x+w,y+h)).tobytes()
        print('PASS exact-source audit: complete 384x608 overlap and every mapped crop match')
        atlases={}
        for e in crosswalk['entries']:
            if e['referencePath'] not in atlases:atlases[e['referencePath']]=Image.open(io.BytesIO(ref.read(e['referencePath']))).convert('RGBA')
            if e['mainAtlasPath'] not in atlases:atlases[e['mainAtlasPath']]=Image.open(io.BytesIO(orig.read(e['mainAtlasPath']))).convert('RGBA')
            rx,ry=e['referenceCell'];sample=atlases[e['referencePath']].crop((rx*32,ry*32,rx*32+32,ry*32+32)).tobytes()
            assert digest(sample)==e['referencePixelSha256']
            for tx,ty in e['exactMainAtlasCells']:
                other=atlases[e['mainAtlasPath']].crop((tx*32,ty*32,tx*32+32,ty*32+32)).tobytes()
                assert other==sample
        print('PASS source crosswalk: all 290 source cells and every declared main-atlas match validated')
        if args.original_test_scenes_zip:
            with zipfile.ZipFile(args.original_test_scenes_zip) as scenes:
                assert ref.read('DemoGame - Seasons.gif')==scenes.read('_ Test Scenes/DemoGame - Seasons.gif')
            print('PASS seasons GIF: identical bytes to existing artist demo archive')
        else:print('NOT RUN: GIF cross-archive comparison')
    return 0
if __name__=='__main__':
    try:sys.exit(main())
    except (AssertionError,KeyError,ValueError,zipfile.BadZipFile) as exc:
        print('FAIL source/metadata proof:',type(exc).__name__,str(exc));sys.exit(1)
