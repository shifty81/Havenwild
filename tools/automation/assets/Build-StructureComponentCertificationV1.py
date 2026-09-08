#!/usr/bin/env python3
"""Build the W45B exact LPC structure-component runtime cache.

Raw LPC sources remain an external dependency. When the pinned files are present,
this builder verifies their hashes and deterministically rebuilds the compact
runtime atlas. A compact checkout may retain the checked-in generated cache.
"""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
from PIL import Image
import numpy as np

ROOT_DEFAULT = Path(__file__).resolve().parents[3]
CACHE_PNG = Path('assets/generated/havenwild_structure_components_w45b.png')
CACHE_JSON = Path('assets/generated/havenwild_structure_components_w45b.json')
SOURCES = {
 'door': ('assets/source/licensed/lpc_revised/Structure/Doors/32x48px Doors/12 Panel Door A.png','6618554708d2f3a56079bc2c9bc6b3ea68ec479c7649531614611a68bab643e6'),
 'stairs': ('assets/source/licensed/lpc_revised/Structure/Stairs/Short Steps A.png','55cc3b06a3026d2132253f266d7317181dda97b8e6fe2e765d24cbba1a5a99e4'),
 'fence': ('assets/source/licensed/lpc_revised/Structure/Fences/Plain Fence A.png','75c4675199e3bac5f60ebab6092b64f05b285dc68397595d80be119635599c2f'),
 'sign_bg': ('assets/source/licensed/lpc_revised/Structure/Signs/Sign Backgrounds A.png','9508252c25b2d3640decbb19a32d59617d81d33a80a1c253d7256db18a9b6123'),
 'sign_icons': ('assets/source/licensed/lpc_revised/Structure/Signs/Sign Icons A.png','60b5ade8f65fafc32f48292e20398df33e1e39a6614ec5ad3a8c9135c7f15f21'),
}

def sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1<<20),b''): h.update(block)
    return h.hexdigest()

def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument('--root',type=Path,default=ROOT_DEFAULT); ap.add_argument('--require-source',action='store_true'); args=ap.parse_args()
    root=args.root.resolve()
    resolved={k:(root/rel,rel,expected) for k,(rel,expected) in SOURCES.items()}
    missing=[rel for _,rel,_ in resolved.values() if not (root/rel).is_file()]
    if missing:
        if args.require_source or not (root/CACHE_PNG).is_file() or not (root/CACHE_JSON).is_file():
            raise SystemExit('W45B source dependency missing: '+', '.join(missing))
        print(f'W45B raw LPC dependency unavailable ({len(missing)} file(s)); retained checked-in deterministic runtime cache')
        return 0
    for _,(path,rel,expected) in resolved.items():
        actual=sha256(path)
        if actual!=expected: raise SystemExit(f'W45B pinned source hash drift: {rel}: {actual} != {expected}')

    atlas=Image.new('RGBA',(256,256),(0,0,0,0)); entries={}
    door=Image.open(resolved['door'][0]).convert('RGBA')
    names=['open_left','swing_left_2','swing_left_1','closed','swing_right_1','swing_right_2','open_right']
    for i,name in enumerate(names):
        slot=door.crop((i*64,0,i*64+64,96)); arr=np.array(slot); ys,xs=np.where(arr[:,:,3]>0)
        bbox=(int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)); crop=slot.crop(bbox)
        frame=Image.new('RGBA',(32,64),(0,0,0,0)); frame.alpha_composite(crop,((32-crop.width)//2,64-crop.height)); x=i*32
        atlas.alpha_composite(frame,(x,0)); entries[f'door_12panel_oak:{name}']={'cacheRect':[x,0,32,64],'sourcePath':resolved['door'][1],'sourceSlotRect':[i*64,0,64,96],'sourceAlphaRect':[i*64+bbox[0],bbox[1],bbox[2]-bbox[0],bbox[3]-bbox[1]],'normalization':'alpha_crop_bottom_center_into_32x64'}
    stairs=Image.open(resolved['stairs'][0]).convert('RGBA'); atlas.alpha_composite(stairs.crop((64,0,96,160)),(0,64)); atlas.alpha_composite(stairs.crop((64,64,96,96)),(32,64))
    entries['stairs_short_steps_gray_run']={'cacheRect':[0,64,32,160],'sourcePath':resolved['stairs'][1],'sourceRect':[64,0,32,160],'normalization':'exact_copy'}
    entries['stairs_short_steps_gray_single']={'cacheRect':[32,64,32,32],'sourcePath':resolved['stairs'][1],'sourceRect':[64,64,32,32],'normalization':'exact_copy'}
    fence=Image.open(resolved['fence'][0]).convert('RGBA')
    for idx,(name,rect) in enumerate([('fence_plain_horizontal',[32,0,32,32]),('fence_plain_vertical',[96,32,32,32]),('fence_plain_post',[0,96,32,32])]):
        x,y,w,h=rect; xo=64+idx*32; atlas.alpha_composite(fence.crop((x,y,x+w,y+h)),(xo,64)); entries[name]={'cacheRect':[xo,64,32,32],'sourcePath':resolved['fence'][1],'sourceRect':rect,'normalization':'exact_copy'}
    bg=Image.open(resolved['sign_bg'][0]).convert('RGBA').crop((0,0,32,32)); icons=Image.open(resolved['sign_icons'][0]).convert('RGBA')
    for idx,name in enumerate(['sword','shield','potion','inn','pub']):
        comp=bg.copy(); comp.alpha_composite(icons.crop((idx*32,0,idx*32+32,32))); xo=64+idx*32; atlas.alpha_composite(comp,(xo,96)); entries[f'sign_wall_{name}']={'cacheRect':[xo,96,32,32],'sourceLayers':[{'id':'background','sourcePath':resolved['sign_bg'][1],'sourceRect':[0,0,32,32]},{'id':'icon','sourcePath':resolved['sign_icons'][1],'sourceRect':[idx*32,0,32,32]}],'normalization':'alpha_composite_icon_over_background'}
    (root/CACHE_PNG).parent.mkdir(parents=True,exist_ok=True); atlas.save(root/CACHE_PNG)
    meta={'schema':'havenwild.structure_component_runtime_cache.v1','pass':'167Z109W45B','atlas':CACHE_PNG.as_posix(),'atlasSize':[256,256],'sourceAuthority':'ElizaWy/LPC Structure source dependency','sourceHashes':{rel:expected for _,rel,expected in resolved.values()},'entries':entries}
    (root/CACHE_JSON).write_text(json.dumps(meta,indent=2)+'\n',encoding='utf-8')
    print(f'W45B structure runtime cache: {len(entries)} cache frame/component record(s) -> {CACHE_PNG.as_posix()}')
    return 0
if __name__=='__main__': raise SystemExit(main())
