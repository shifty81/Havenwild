#!/usr/bin/env python3
"""Publish one W77 terrain transition document as a review-only candidate."""
from __future__ import annotations
import argparse,json
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[3]
AUTHOR=('10_owner_fill','20_boundary_shape','30_shading_cleanup','40_alpha_cleanup')
LOCKED=('00_semantic_shape_template','01_reference_a_style','02_reference_b_style','90_preview_only')

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('document',help='repair PNG or .transition.json path'); ns=ap.parse_args()
 p=(ROOT/ns.document) if not Path(ns.document).is_absolute() else Path(ns.document)
 if p.suffix=='.json' and p.name.endswith('.transition.json'):
  desc=json.load(open(p)); p=ROOT/desc['pixelDocument']
 side=p.with_suffix('.hhasset.json'); md=json.load(open(side))
 layers={x['id']:x for x in md['layers']}
 for lid in LOCKED:
  if not layers.get(lid,{}).get('locked',False): raise SystemExit(f'REFUSE: reference layer {lid} is not locked')
 out=Image.new('RGBA',(md['width'],md['height']),(0,0,0,0)); parent=side.parent
 for lid in AUTHOR:
  layer=layers.get(lid)
  if not layer: raise SystemExit(f'REFUSE: missing author layer {lid}')
  out.alpha_composite(Image.open(parent/layer['imagePath']).convert('RGBA'))
 stem=p.stem; target=ROOT/'content/editor/terrain_transition_workbench/candidates'/stem
 target.mkdir(parents=True,exist_ok=True); image=target/'corner_tuple16_candidate.png'; out.save(image)
 desc_path=p.with_suffix('.transition.json'); desc=json.load(open(desc_path))
 manifest={'schema':'havenwild.terrain_transition_candidate.w77_v1','status':'candidate_unpublished','pair':desc['pair'],'sourceDocument':str(p.relative_to(ROOT)).replace('\\','/'),'image':str(image.relative_to(ROOT)).replace('\\','/'),'authorLayers':list(AUTHOR),'runtimeBindingsChanged':False,'promotionRequirement':'explicit visual certification and registry promotion'}
 (target/'corner_tuple16_candidate.json').write_text(json.dumps(manifest,indent=2)+'\n')
 print(f'Published review-only candidate: {image.relative_to(ROOT)}')
if __name__=='__main__': main()
