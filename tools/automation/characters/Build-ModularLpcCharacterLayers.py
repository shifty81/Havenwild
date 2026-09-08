"""Build the default modular LPC character layers used by creator and runtime.

This intentionally produces separate transparent walk/idle sheets instead of a
single precomposited mannequin. Additional catalog variants can be promoted by
extending COMPONENTS without changing the runtime contract.
"""
from __future__ import annotations
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "assets/source/licensed/lpc_revised/Characters"
OUT = ROOT / "assets/generated/lpc/characters/layers"
CELL=64; COLS=8; ROWS=4

COMPONENTS = {
    "body_male": [
        "Body/Body 02 - Masculine, Thin/Tan/Walk.png",
        "Head/Head 02 - Masculine/Tan/Walk.png",
    ],
    "eyes": ["Head/Head Overlay - Eyes/Brown/Walk.png"],
    "feet_boots": ["Clothing/Masculine, Thin/Feet/Shoes 01 - Shoes/Brown/Walk.png"],
    "legs_pants": ["Clothing/Masculine, Thin/Legs/Pants 03 - Pants/Green/Walk.png"],
    "torso_tshirt": ["Clothing/Masculine, Thin/Torso/Shirt 04 - T-shirt/Blue/Walk.png"],
    "hair_short_02_parted": ["Hair/Short 02 - Parted/Brown/Walk.png"],
    "eyebrows_01_thin": ["Eyebrows/Eyebrows 01 - Thin Eyebrows/Brown/Walk.png"],
}

def load(rel: str) -> Image.Image:
    path=SRC/rel
    if not path.is_file():
        raise FileNotFoundError(path)
    im=Image.open(path).convert("RGBA")
    if im.size != (COLS*CELL, ROWS*CELL):
        raise ValueError(f"{path} is {im.size}, expected {(COLS*CELL,ROWS*CELL)}")
    return im

def expand_walk(src: Image.Image) -> Image.Image:
    out=Image.new("RGBA",(9*CELL,ROWS*CELL),(0,0,0,0))
    for row in range(ROWS):
        frame=src.crop((0,row*CELL,CELL,(row+1)*CELL))
        out.alpha_composite(frame,(0,row*CELL))
        for col in range(COLS):
            frame=src.crop((col*CELL,row*CELL,(col+1)*CELL,(row+1)*CELL))
            out.alpha_composite(frame,((col+1)*CELL,row*CELL))
    return out

def idle_from_walk(src: Image.Image) -> Image.Image:
    out=Image.new("RGBA",(9*CELL,ROWS*CELL),(0,0,0,0))
    for row in range(ROWS):
        frame=src.crop((0,row*CELL,CELL,(row+1)*CELL))
        for col in range(9):
            out.alpha_composite(frame,(col*CELL,row*CELL))
    return out

def main() -> None:
    OUT.mkdir(parents=True,exist_ok=True)
    built=0
    for name,layers in COMPONENTS.items():
        try:
            composite=Image.new("RGBA",(COLS*CELL,ROWS*CELL),(0,0,0,0))
            for rel in layers:
                composite=Image.alpha_composite(composite,load(rel))
        except (FileNotFoundError,ValueError) as exc:
            print(f"SKIP modular layer {name}: {exc}")
            continue
        expand_walk(composite).save(OUT/f"havenwild_player_{name}_walk_64.png",compress_level=9)
        idle_from_walk(composite).save(OUT/f"havenwild_player_{name}_idle_64.png",compress_level=9)
        built += 1
    if built < 6:
        raise RuntimeError(f"only {built}/7 default modular character layers built")
    print(f"Built {built} default modular LPC character layers in {OUT.relative_to(ROOT)}")

if __name__ == '__main__': main()
