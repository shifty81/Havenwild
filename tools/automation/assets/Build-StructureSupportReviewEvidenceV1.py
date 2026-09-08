#!/usr/bin/env python3
"""Build deterministic W45D1 bridge/platform/pillar review evidence from the pinned LPC mount.

This tool is evidence-only. It never publishes support visuals. The portable bundle
is intended for visual review so W45D2 can source-control exact regions without
inventing coordinates or treating whole sheets as placeables.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import zipfile
from collections import defaultdict, deque
from pathlib import Path
from PIL import Image, ImageDraw

ROOT_DEFAULT = Path(__file__).resolve().parents[3]
OUT = Path("WORKSPACE/generated/structure_review/w45d_exact_support")
ZIP_OUT = Path("WORKSPACE/generated/structure_review/Havenwild_W45D_ExactStructureSupportEvidence.zip")
CELL = 32
SOURCES = [
    ("bridge.drawbridge_a", "bridge", "assets/source/licensed/lpc_revised/Structure/Bridges/Drawbridge A.png"),
    ("bridge.rope_a.no_rails", "bridge", "assets/source/licensed/lpc_revised/Structure/Bridges/Rope Bridge A - No Rails.png"),
    ("bridge.rope_a.rails", "bridge", "assets/source/licensed/lpc_revised/Structure/Bridges/Rope Bridge A - Rails.png"),
    ("bridge.wood_a.no_rails", "bridge", "assets/source/licensed/lpc_revised/Structure/Bridges/Wood Bridge A - No Rails.png"),
    ("bridge.wood_a.rails", "bridge", "assets/source/licensed/lpc_revised/Structure/Bridges/Wood Bridge A - Rails.png"),
    ("platform.cement_a", "platform", "assets/source/licensed/lpc_revised/Structure/Platforms/Cement Platform A.png"),
    ("platform.dais_steps_a", "platform", "assets/source/licensed/lpc_revised/Structure/Platforms/Dias with Steps A.png"),
    ("pillar.floral_a", "pillar", "assets/source/licensed/lpc_revised/Structure/Pillars/Floral Pillar A.png"),
    ("pillar.stone_a", "pillar", "assets/source/licensed/lpc_revised/Structure/Pillars/Stone Pillar A.png"),
]
ROLE_GROUPS = {
    "bridge": ["approach_a", "span_repeat", "approach_b", "rail_left", "rail_right", "end_cap_a", "end_cap_b", "support_or_post", "stateful_leaf"],
    "platform": ["field", "edge_north", "edge_east", "edge_south", "edge_west", "corner_nw", "corner_ne", "corner_sw", "corner_se", "step_access"],
    "pillar": ["base", "shaft", "shaft_repeat", "capital", "full_assembly"],
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def edge_contact(alpha: Image.Image) -> dict[str, bool]:
    px = alpha.load(); w, h = alpha.size
    return {
        "north": any(px[x, 0] for x in range(w)),
        "east": any(px[w - 1, y] for y in range(h)),
        "south": any(px[x, h - 1] for x in range(w)),
        "west": any(px[0, y] for y in range(h)),
    }


def analyze_cells(image: Image.Image) -> list[dict]:
    image = image.convert("RGBA")
    cols = math.ceil(image.width / CELL); rows = math.ceil(image.height / CELL)
    records = []
    for r in range(rows):
        for c in range(cols):
            box = (c * CELL, r * CELL, min((c + 1) * CELL, image.width), min((r + 1) * CELL, image.height))
            crop = image.crop(box)
            if crop.size != (CELL, CELL):
                padded = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0)); padded.alpha_composite(crop); crop = padded
            alpha = crop.getchannel("A")
            bbox = alpha.getbbox()
            count = sum(1 for v in alpha.getdata() if v)
            records.append({
                "id": f"c{c}r{r}", "column": c, "row": r,
                "sourceRect": [c * CELL, r * CELL, CELL, CELL],
                "nonEmpty": bool(count), "alphaPixels": count,
                "alphaFraction": round(count / float(CELL * CELL), 6),
                "occupiedBoundsLocal": list(bbox) if bbox else None,
                "edgeContact": edge_contact(alpha),
                "rgbaSha256": sha256_bytes(crop.tobytes()),
            })
    return records


def duplicate_groups(cells: list[dict]) -> list[dict]:
    groups = defaultdict(list)
    for cell in cells:
        if cell["nonEmpty"]:
            groups[cell["rgbaSha256"]].append(cell["id"])
    out = []
    for digest, ids in groups.items():
        if len(ids) > 1:
            out.append({"rgbaSha256": digest, "cellIds": ids, "count": len(ids)})
    out.sort(key=lambda g: (-g["count"], g["cellIds"][0]))
    return out


def connectivity_groups(cells: list[dict]) -> list[list[str]]:
    by_coord = {(c["column"], c["row"]): c for c in cells if c["nonEmpty"]}
    seen = set(); groups = []
    dirs = [(0,-1,"north","south"),(1,0,"east","west"),(0,1,"south","north"),(-1,0,"west","east")]
    for key in sorted(by_coord, key=lambda p: (p[1], p[0])):
        if key in seen: continue
        q = deque([key]); seen.add(key); ids = []
        while q:
            p = q.popleft(); cell = by_coord[p]; ids.append(cell["id"])
            for dx, dy, a, b in dirs:
                np = (p[0] + dx, p[1] + dy); other = by_coord.get(np)
                if other and np not in seen and cell["edgeContact"][a] and other["edgeContact"][b]:
                    seen.add(np); q.append(np)
        groups.append(sorted(ids, key=lambda s: (int(s.split("r")[1]), int(s[1:].split("r")[0]))))
    groups.sort(key=lambda g: (-len(g), g[0]))
    return groups


def make_board(image: Image.Image, out: Path, scale: int = 2) -> None:
    image = image.convert("RGBA"); w, h = image.size
    board = Image.new("RGBA", (w * scale, h * scale), (28, 28, 28, 255))
    board.alpha_composite(image.resize((w * scale, h * scale), Image.Resampling.NEAREST), (0, 0))
    draw = ImageDraw.Draw(board)
    for x in range(0, w + 1, CELL): draw.line((x * scale, 0, x * scale, h * scale), fill=(255, 55, 55, 230), width=1)
    for y in range(0, h + 1, CELL): draw.line((0, y * scale, w * scale, y * scale), fill=(255, 55, 55, 230), width=1)
    for r in range(math.ceil(h / CELL)):
        for c in range(math.ceil(w / CELL)):
            x = c * CELL * scale; y = r * CELL * scale
            draw.rectangle((x + 1, y + 1, x + 42, y + 15), fill=(0, 0, 0, 190))
            draw.text((x + 3, y + 2), f"c{c}r{r}", fill=(255, 240, 60, 255))
    out.parent.mkdir(parents=True, exist_ok=True); board.save(out)


def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--root", type=Path, default=ROOT_DEFAULT); ap.add_argument("--require-all", action="store_true")
    args = ap.parse_args(); root = args.root.resolve(); outroot = root / OUT
    available = []; missing = []
    for family, role, rel in SOURCES:
        p = root / rel
        (available if p.is_file() else missing).append((family, role, rel, p))
    if missing and args.require_all:
        raise SystemExit("W45D1 pinned structure support source missing: " + ", ".join(rel for _,_,rel,_ in missing))
    if not available:
        print("W45D1 exact structure support evidence deferred: pinned LPC source mount is unavailable")
        print("Run the normal LPC dependency sync on the Windows project, then rerun this command.")
        return 0
    if outroot.exists(): shutil.rmtree(outroot)
    outroot.mkdir(parents=True, exist_ok=True)
    sources = []
    for family, role, rel, path in available:
        image = Image.open(path).convert("RGBA")
        cells = analyze_cells(image)
        safe = family.replace(".", "_")
        board_rel = OUT / f"{safe}_grid_2x.png"
        make_board(image, root / board_rel)
        cell_rel = OUT / f"{safe}_cells.json"
        payload = {
            "schema": "havenwild.structure_support_source_cell_evidence.v1",
            "pass": "167Z109W45D1",
            "family": family, "role": role,
            "sourcePath": rel, "sourceSha256": sha256_file(path),
            "sourceSize": [image.width, image.height],
            "grid": [math.ceil(image.width / CELL), math.ceil(image.height / CELL)],
            "cellSize": [CELL, CELL], "cells": cells,
            "duplicatePixelGroups": duplicate_groups(cells),
            "alphaEdgeConnectedGroups": connectivity_groups(cells),
            "warning": "Connectivity and duplicate groups are review aids only; they do not assign semantic bridge/platform/pillar roles."
        }
        (root / cell_rel).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        sources.append({
            "family": family, "role": role, "sourcePath": rel,
            "sourceSha256": payload["sourceSha256"], "sourceSize": payload["sourceSize"],
            "grid": payload["grid"], "board": board_rel.as_posix(),
            "cellEvidence": cell_rel.as_posix(),
            "nonEmptyCells": sum(1 for c in cells if c["nonEmpty"])
        })
    manifest = {
        "schema": "havenwild.exact_structure_support_review_evidence.v1",
        "pass": "167Z109W45D1", "sourceCommit": "f07f7f5892e67c932c68f70bb04472f2c64e46bc",
        "cellSize": [CELL, CELL], "sources": sources,
        "missingSources": [rel for _,_,rel,_ in missing],
        "reviewRule": "Human visual review assigns topology roles. Cell analysis never auto-promotes bridge/platform/pillar art."
    }
    (outroot / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    selections = []
    for role, names in ROLE_GROUPS.items():
        for name in names:
            selections.append({"roleGroup": role, "role": name, "family": None, "sourceRect": None, "cellIds": [], "reviewNote": ""})
    selection = {
        "schema": "havenwild.structure_support_exact_region_selection_template.v1",
        "pass": "167Z109W45D1",
        "instructions": [
            "Choose only source regions visually verified on the labelled boards.",
            "A selection may be one 32x32 cell or a multi-cell rectangle/assembly.",
            "Do not infer roles from alpha occupancy or duplicate groups alone.",
            "Bridge walkable deck, rails, and bank sockets are reviewed separately.",
            "Accepted selections are copied into a source-controlled W45D2 publication manifest; this machine-local template is not authority."
        ],
        "selections": selections
    }
    (outroot / "structure_support_selection_template_v1.json").write_text(json.dumps(selection, indent=2) + "\n", encoding="utf-8")
    zip_path = root / ZIP_OUT; zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(outroot.rglob("*")):
            if p.is_file(): z.write(p, p.relative_to(outroot.parent))
    print(f"W45D1 exact structure support review evidence: {len(sources)}/{len(SOURCES)} source sheet(s)")
    print(f"evidence: {OUT}")
    print(f"upload bundle: {ZIP_OUT}")
    if missing: print(f"missing source sheets: {len(missing)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
