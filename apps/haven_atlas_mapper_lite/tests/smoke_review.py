#!/usr/bin/env python3
"""Source-exact deterministic fixture for the mapper verifier; native Rust gate is separate."""
import argparse
import copy
import hashlib
import json
import pathlib
import sys
import zipfile
from PIL import Image
from io import BytesIO

TOOLS = pathlib.Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))
from verify_review import verify


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--terrain-zip", type=pathlib.Path, required=True)
    parser.add_argument("--reference-zip", type=pathlib.Path, required=True)
    parser.add_argument("--out", type=pathlib.Path, required=True)
    args = parser.parse_args()
    root = args.out.resolve()
    (root / "source").mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(args.terrain_zip) as z:
        cliff = z.read("Terrain/cliff_summer.png")
        credits = z.read("Terrain/Credits.txt")
    with zipfile.ZipFile(args.reference_zip) as z:
        matches = [name for name in z.namelist() if name.lower().endswith("mountain, waterfall transitions (summer).png")]
        assert matches, "Original recovered waterfall transitions source not found"
        transitions = z.read(matches[0])
    (root / "source/cliff_summer.png").write_bytes(cliff)
    (root / "source/waterfall_transitions_summer.png").write_bytes(transitions)
    (root / "source/CREDITS_ORIGINAL.txt").write_bytes(credits)
    sources = [
        {"id": "source:cliff_summer", "path": "source/cliff_summer.png", "file_name": "cliff_summer.png", "source_sha256": digest(cliff)},
        {"id": "source:waterfall_transitions", "path": "source/waterfall_transitions_summer.png", "file_name": "waterfall_transitions_summer.png", "source_sha256": digest(transitions)},
    ]
    im1 = Image.open(BytesIO(cliff)).convert("RGBA")
    im2 = Image.open(BytesIO(transitions)).convert("RGBA")
    # Select nonempty original 32x32 cells; no invented artwork, no inferred joins.
    def pick(sheet, n):
        chosen = []
        for y in range(sheet.height // 32):
            for x in range(sheet.width // 32):
                crop = sheet.crop((x*32,y*32,(x+1)*32,(y+1)*32))
                if crop.getchannel("A").getbbox() and crop.getchannel("A").getextrema()[1] == 255:
                    chosen.append((x,y))
                if len(chosen) >= n:
                    return chosen
        raise ValueError("Not enough original source tiles")
    cells = [(sources[0], im1, cell) for cell in pick(im1, 3)] + [(sources[1], im2, cell) for cell in pick(im2, 3)]
    placements = []
    output = Image.new("RGBA", (96,64))
    for i,(source,sheet,(x,y)) in enumerate(cells):
        dx, dy = i%3, i//3
        output.alpha_composite(sheet.crop((x*32,y*32,(x+1)*32,(y+1)*32)),(dx*32,dy*32))
        placements.append({"id":i+1,"source_tile_x":x,"source_tile_y":y,
                           "source_rect":[x*32,y*32,32,32],"canvas_grid_x":dx,
                           "canvas_grid_y":dy,"rotation_degrees":0,"flip_x":False,"flip_y":False,
                           "layer":0,"semantic_role":"unreviewed_source_sample",
                           "source_asset_id":source["id"]})
    ledger={"schema":"havenwild.atlas_mapper_review.v0_1",
            "approval":"unreviewed_source_assembly_not_for_runtime",
            "source_assets":sources,"placements":placements,
            "heightmap":[{"x":0,"y":0,"elevation":0,"water_surface":0},
                         {"x":1,"y":0,"elevation":1,"water_surface":None},
                         {"x":2,"y":0,"elevation":30,"water_surface":None}],
            "output_pixel_size":[96,64],"output_grid_origin":[0,0],
            "evidence_notes":["Source-only mapping smoke fixture; NOT a visually approved terrain assembly."]}
    png=root/'ELIZAWY_MAPPER_MULTISOURCE_SMOKE_UNREVIEWED.png'
    document=root/'ELIZAWY_MAPPER_MULTISOURCE_SMOKE_UNREVIEWED.review.json'
    output.save(png)
    document.write_text(json.dumps(ledger,indent=2)+'\n',encoding='utf-8')
    result=verify(document,png,root,root/'ELIZAWY_MAPPER_MULTISOURCE_SMOKE.source-proof.json')
    assert result["placement_count"]==6 and len(result["sources"])==2
    # Deliberate negative checks: any artwork mutation, status forgery, and height invalidation fail.
    forged=copy.deepcopy(ledger);forged["source_assets"][0]["source_sha256"]='0'*64
    test=root/'negative.review.json';test.write_text(json.dumps(forged))
    try: verify(test,png,root,root/'negative.receipt.json')
    except ValueError as error: assert 'HASH CHANGED' in str(error)
    else: raise AssertionError('FAIL hash mutation escaped')
    forged=copy.deepcopy(ledger);forged["heightmap"][1]["elevation"]=31
    test.write_text(json.dumps(forged))
    try: verify(test,png,root,root/'negative.receipt.json')
    except ValueError as error: assert '0..30' in str(error)
    else: raise AssertionError('FAIL invalid elevation escaped')
    forged=copy.deepcopy(ledger);forged["approval"]='runtime_certified'
    test.write_text(json.dumps(forged))
    try: verify(test,png,root,root/'negative.receipt.json')
    except ValueError as error: assert 'automatic approval' in str(error)
    else: raise AssertionError('FAIL forged runtime certification escaped')
    test.unlink()
    print('PASS original two-source smoke: 6 original cells, +0/+1/+30, byte SHA, replay PNG')
    print('PASS three negative mutation tests: source hash, elevation 31, forged approval')
    print('PNG:',png)

if __name__=='__main__': main()
