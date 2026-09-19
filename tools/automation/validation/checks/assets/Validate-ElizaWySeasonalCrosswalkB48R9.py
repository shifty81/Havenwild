#!/usr/bin/env python3
"""Read-only source-exact mapping validator. Does not promote gameplay assets."""
import argparse,collections,hashlib,io,json,zipfile
from pathlib import Path
TARGET='content/assets/lpc/elizawy_all_seasons_split_source_crosswalk_b48r9_v0_1.json'
SUMMARY='content/assets/lpc/elizawy_all_seasons_source_coverage_b48r9_v0_1.json'
def sha(b):return hashlib.sha256(b).hexdigest()
def run(args):
 d=json.loads((args.repo/TARGET).read_text()); s=json.loads((args.repo/SUMMARY).read_text())
 assert d['schema']=='havenwild.elizawy.reference_split_seasonal_source_crosswalk.b48r9'
 assert d['productionEnabled'] is False and d['rendererChanged'] is False
 assert len(d['sourceSheets'])==40 and len(d['entries'])==1781
 assert d['priorMappingsVerified']=={'b48r7SummerCells':290,'b48r8SummerWaterfallTransitionCells':42}
 assert {k:v for k,v in d.items() if k!='entries'}==s
 assert all(e['sourceAddressVerified'] and not e['semanticRoleVerified'] and not e['editorRuntimeBindingVerified'] and not e['collisionVerified'] for e in d['entries'])
 assert all(d['winterIceShorelineCandidateEvidence'][f]['matchedWinterIceAtlas']==36 for f in ('grass_shallows','dirt_shallows'))
 print('PASS metadata: 40 source sheets, 1781 cells; no runtime promotion')
 if not (args.reference_zip and args.original_terrain_zip):
  assert not args.reference_zip and not args.original_terrain_zip, 'supply BOTH original source ZIPs'
  print('NOT RUN: source-pixel verification (provide both source ZIP arguments)');return
 from PIL import Image
 with zipfile.ZipFile(args.reference_zip) as ref, zipfile.ZipFile(args.original_terrain_zip) as orig:
  main={n:Image.open(io.BytesIO(orig.read(n))).convert('RGBA') for n in orig.namelist() if n.lower().endswith('.png')}
  indexes={}
  for n,im in main.items():
   by_sha=collections.defaultdict(list)
   for y in range(im.height//32):
    for x in range(im.width//32):
     by_sha[sha(im.crop((x*32,y*32,x*32+32,y*32+32)).tobytes())].append([x,y])
   indexes[n]=by_sha
  ref_images={}
  for source in d['sourceSheets']:
   raw=ref.read(source['path']);assert sha(raw)==source['sourceByteSha256']
   im=Image.open(io.BytesIO(raw)).convert('RGBA')
   assert list(im.size)==source['pixelDimensions']
   ref_images[source['path']]=im
  for e in d['entries']:
   x,y=e['referenceCell'];im=ref_images[e['referencePath']]
   digest=sha(im.crop((x*32,y*32,x*32+32,y*32+32)).tobytes())
   assert digest==e['sourcePixelSha256']
   for target in e['targets']:
    path=target['canonicalAtlas'];actual=indexes.get(path,{}).get(digest,[]) if path else []
    assert actual==target['exactCanonicalCells']
   for m in e['exactGlobalCanonicalMatches']:
    assert m['cell'] in indexes[m['path']].get(digest,[])
  for family in ('grass_shallows','dirt_shallows'):
   winter=[e for e in d['entries'] if e['family']==family and any(t['season']=='winter' for t in e['targets'])]
   assert len(winter)==36 and all(indexes['Terrain/terrain_winter_ice.png'].get(e['sourcePixelSha256']) for e in winter)
  print('PASS pixel checks: 1781 source cells and every declared canonical address')
  print('PASS winter ice source identity: both shoreline families 36/36')
  if args.b48r7_patch:
   with zipfile.ZipFile(args.b48r7_patch) as z:
    old=json.loads(z.read('content/assets/lpc/elizawy_summer_atlas_source_crosswalk_b48r7_v0_1.json'))
   mapped={(e['referencePath'],tuple(e['referenceCell'])):e for e in d['entries']}
   for o in old['entries']:
    e=mapped[o['referencePath'],tuple(o['referenceCell'])]
    t=next(t for t in e['targets'] if t['season']=='summer')
    assert e['sourcePixelSha256']==o['referencePixelSha256'] and t['exactCanonicalCells']==o['exactMainAtlasCells']
   assert len(old['entries'])==290;print('PASS inherited B48R7: 290/290 cells')
  if args.b48r8_patch:
   with zipfile.ZipFile(args.b48r8_patch) as z:
    r8=json.loads(z.read('content/assets/lpc/elizawy_mountain_waterfall_transition_source_b48r8_v0_1.json'))
    raw=z.read('content/assets/lpc/source_blobs/elizawy_mountain_waterfall_transitions_summer.png.source')
   assert sha(raw)==r8['authority']['sourceSha256']
   row={tuple(e['referenceCell']):e for e in d['entries'] if e['referencePath']=='Terrain/Mountain, Waterfall Transitions (Summer).png'}
   assert len(row)==42
   for cell in r8['cells']:assert row[tuple(cell['grid'])]['sourcePixelSha256']==cell['pixelSha256']
   print('PASS inherited B48R8: 42/42 cells')
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__)
 for a in ['repo','reference-zip','original-terrain-zip','b48r7-patch','b48r8-patch']:
  p.add_argument('--'+a,type=Path,default=Path(__file__).resolve().parents[5] if a=='repo' else None)
 try:run(p.parse_args())
 except (AssertionError,KeyError,ValueError,zipfile.BadZipFile) as e:raise SystemExit('FAIL B48R9 source mapping: '+repr(e))
