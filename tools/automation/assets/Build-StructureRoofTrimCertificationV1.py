#!/usr/bin/env python3
"""Build W45C2 exact wall-border runtime cache and roof-topology review state.

The only runtime visual promoted in W45C2 is the exact Formal Crown Molding
repeat cell. Roof sheets remain source-grammar authority until exact topology
regions are accepted; the roof topology contract forbids guessed cell promotion.
"""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
from PIL import Image

ROOT_DEFAULT=Path(__file__).resolve().parents[3]
SRC=Path('assets/source/licensed/lpc_revised/Structure/Wall Borders/Formal Crown Molding.png')
SRC_SHA256='96efe18d0e6f807a1e432f4a0611a94c5ba52aa47d493c8ec36f1199fff070e5'
CACHE=Path('assets/generated/havenwild_structure_roof_trim_w45c2.png')
META=Path('assets/generated/havenwild_structure_roof_trim_w45c2.json')

def sha256(p:Path)->str:
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''): h.update(b)
    return h.hexdigest()

def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument('--root',type=Path,default=ROOT_DEFAULT); ap.add_argument('--require-source',action='store_true'); args=ap.parse_args(); root=args.root.resolve()
    src=root/SRC
    if not src.is_file():
        if args.require_source or not (root/CACHE).is_file() or not (root/META).is_file():
            raise SystemExit(f'W45C2 source dependency missing: {SRC}')
        print('W45C2 raw wall-border dependency unavailable; retained checked-in deterministic cache')
        return 0
    actual=sha256(src)
    if actual!=SRC_SHA256: raise SystemExit(f'W45C2 pinned source hash drift: {actual} != {SRC_SHA256}')
    im=Image.open(src).convert('RGBA')
    # Bottom row c0-c3 are pixel-identical repeat cells. Preserve one exact source cell.
    crop=im.crop((0,64,32,96))
    atlas=Image.new('RGBA',(64,64),(0,0,0,0)); atlas.alpha_composite(crop,(0,0))
    (root/CACHE).parent.mkdir(parents=True,exist_ok=True); atlas.save(root/CACHE)
    meta={
      'schema':'havenwild.structure_roof_trim_runtime_cache.v1','pass':'167Z109W45C2','atlas':CACHE.as_posix(),'atlasSize':[64,64],
      'sourceAuthority':'ElizaWy/LPC pinned Structure source dependency','sourceHashes':{SRC.as_posix():SRC_SHA256},
      'entries':{'wall_border_formal_crown_repeat':{'cacheRect':[0,0,32,32],'sourcePath':SRC.as_posix(),'sourceRect':[0,64,32,32],'normalization':'exact_repeat_cell'}}
    }
    (root/META).write_text(json.dumps(meta,indent=2)+'\n',encoding='utf-8')
    print(f'W45C2 wall-border runtime cache: 1 exact component -> {CACHE}')
    return 0
if __name__=='__main__': raise SystemExit(main())
