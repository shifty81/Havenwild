#!/usr/bin/env python3
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[3]
ELIZAWY = ROOT / 'assets/generated/worldgen_v0_1/terrain/elizawy_cliff_runtime_overlay_summer.png'
LPC = ROOT / 'content/assets/oga_lpc/source/terrain/cliffs_grass_top/LPC_cliffs_grass.png'
OUT = ROOT / 'docs/assets/previews/elizawy_cliff_generated_contours_pass167z109w8.png'
CELL = 32
SCALE = 3
FONT = ImageFont.load_default()
BG = (24, 25, 28, 255)
PANEL = (38, 40, 45, 255)
FG = (242, 242, 244, 255)
MUTED = (186, 190, 198, 255)
GRID = (82, 84, 92, 170)
BASE = (69, 139, 63, 255)
LOW = (93, 122, 63, 255)
WARN = (225, 115, 86, 255)


def ecell(im, c, r):
    return im.crop((c * CELL, r * CELL, (c + 1) * CELL, (r + 1) * CELL))


def place_cell(dst, src, x, y):
    dst.alpha_composite(src, (x, y))


def panel_canvas(w=5, h=5):
    out = Image.new('RGBA', (w * CELL, h * CELL), (0, 0, 0, 0))
    d = ImageDraw.Draw(out)
    # High plateau host zone in upper-center; low receiver below.
    d.rectangle((0, 0, w * CELL, h * CELL), fill=LOW)
    d.rectangle((CELL, CELL, (w - 1) * CELL, 2 * CELL), fill=BASE)
    return out


def render_mask(elizawy, lpc, mask):
    out = panel_canvas()
    hx, hy = 2 * CELL, CELL
    if mask == 1:  # N
        place_cell(out, ecell(elizawy, 6, 5), hx, hy)
    elif mask == 2:  # E
        place_cell(out, ecell(elizawy, 7, 6), hx, hy)
    elif mask == 3:  # NE exact corner
        place_cell(out, ecell(elizawy, 7, 5), hx, hy)
    elif mask == 4:  # S straight
        place_cell(out, ecell(elizawy, 6, 7), hx, hy)
        for row, (c, r) in enumerate([(10, 9), (10, 10), (10, 11)]):
            place_cell(out, ecell(elizawy, c, r), hx, hy + (row + 1) * CELL)
    elif mask == 5:  # N+S opposite modules, disjoint alpha
        place_cell(out, ecell(elizawy, 6, 5), hx, hy)
        place_cell(out, ecell(elizawy, 6, 7), hx, hy)
        for row, (c, r) in enumerate([(10, 9), (10, 10), (10, 11)]):
            place_cell(out, ecell(elizawy, c, r), hx, hy + (row + 1) * CELL)
    elif mask == 6:  # SE rounded
        for row, (c, r) in enumerate([(3, 6), (3, 7), (3, 3), (3, 8)]):
            place_cell(out, ecell(elizawy, c, r), hx, hy + row * CELL)
    elif mask == 8:  # W
        place_cell(out, ecell(elizawy, 5, 6), hx, hy)
    elif mask == 9:  # NW exact corner
        place_cell(out, ecell(elizawy, 5, 5), hx, hy)
    elif mask == 10:  # E+W exact companion ridge row c8-c10 r2
        stamp = lpc.crop((8 * CELL, 2 * CELL, 11 * CELL, 3 * CELL))
        out.alpha_composite(stamp, (hx - CELL, hy))
    elif mask == 12:  # SW rounded
        for row, (c, r) in enumerate([(1, 6), (1, 7), (1, 3), (1, 8)]):
            place_cell(out, ecell(elizawy, c, r), hx, hy + row * CELL)
    return out


def alpha_overlap(elizawy, a, b):
    aa = ecell(elizawy, *a).getchannel('A')
    bb = ecell(elizawy, *b).getchannel('A')
    return sum(1 for x, y in zip(aa.getdata(), bb.getdata()) if x and y)


def main():
    elizawy = Image.open(ELIZAWY).convert('RGBA')
    lpc = Image.open(LPC).convert('RGBA')
    assert alpha_overlap(elizawy, (6, 5), (6, 7)) == 0, 'N/S opposite modules unexpectedly overlap'

    masks = [1, 2, 3, 4, 5, 6, 8, 9, 10, 12]
    names = {
        1: 'N straight', 2: 'E straight', 3: 'NE convex', 4: 'S straight',
        5: 'N+S ridge', 6: 'SE rounded', 8: 'W straight', 9: 'NW convex',
        10: 'E+W ridge', 12: 'SW rounded'
    }
    pw, ph = 5 * CELL * SCALE, 5 * CELL * SCALE
    canvas = Image.new('RGBA', (1660, 1260), BG)
    d = ImageDraw.Draw(canvas)
    d.text((20, 16), 'Pass167Z109W8 - fresh-PCG cliff grammar freeze', fill=FG, font=FONT)
    d.text((20, 36), 'Exact authored cells/stamps only. Stable generated masks: 1,2,3,4,5,6,8,9,10,12.', fill=MUTED, font=FONT)
    d.text((20, 54), 'Three/four-edge one-cell caps are removed by generated contour normalization; no fake replacement art is synthesized.', fill=MUTED, font=FONT)

    for i, mask in enumerate(masks):
        col, row = i % 5, i // 5
        x = 20 + col * (pw + 12)
        y = 86 + row * (ph + 64)
        d.rectangle((x - 2, y - 2, x + pw + 2, y + ph + 2), fill=PANEL)
        img = render_mask(elizawy, lpc, mask).resize((pw, ph), Image.Resampling.NEAREST)
        canvas.alpha_composite(img, (x, y))
        step = CELL * SCALE
        for gx in range(6): d.line((x + gx * step, y, x + gx * step, y + ph), fill=GRID, width=1)
        for gy in range(6): d.line((x, y + gy * step, x + pw, y + gy * step), fill=GRID, width=1)
        d.text((x, y + ph + 8), f'mask {mask:02d}  {names[mask]}', fill=FG, font=FONT)

    y0 = 86 + 2 * (ph + 64)
    d.text((20, y0), 'Generated-thin masks deliberately excluded from the fresh-PCG visual grammar', fill=FG, font=FONT)
    d.text((20, y0 + 22), '7 / 11 / 13 / 14 / 15 = one or zero same-tier cardinal supports. normalize_structural_contours removes them before cliff bake.', fill=WARN, font=FONT)
    d.text((20, y0 + 44), 'Explicit editor/player geometry may still create them, but the renderer is forbidden from inventing generic cap pixels.', fill=MUTED, font=FONT)

    # Cave width policy evidence.
    narrow = elizawy.crop((6 * CELL, 9 * CELL, 7 * CELL, 12 * CELL)).resize((CELL * 4, CELL * 12), Image.Resampling.NEAREST)
    wide = elizawy.crop((7 * CELL, 9 * CELL, 10 * CELL, 12 * CELL)).resize((CELL * 4 * 3, CELL * 12), Image.Resampling.NEAREST)
    cy = y0 + 92
    canvas.alpha_composite(narrow, (20, cy))
    canvas.alpha_composite(wide, (190, cy))
    d.text((20, cy + narrow.height + 8), 'DEFAULT cave: authored 1x3 mouth, always 1 tile wide', fill=FG, font=FONT)
    d.text((190, cy + wide.height + 8), 'RESERVED: authored 3x3 road/cart/major tunnel only', fill=MUTED, font=FONT)
    d.text((20, cy + narrow.height + 30), 'Taller cliffs insert normal authored rock continuation above the fixed cave mouth; height never widens the opening.', fill=MUTED, font=FONT)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert('RGB').save(OUT, optimize=True)
    print(OUT.relative_to(ROOT))

if __name__ == '__main__':
    main()
