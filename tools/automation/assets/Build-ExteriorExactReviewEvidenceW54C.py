#!/usr/bin/env python3
"""Build W54C machine-local exact exterior review evidence.

This is deliberately evidence-only. It labels source coordinates and records pixel
statistics from the pinned LPC mount, but never assigns semantic facings and never
publishes runtime assets.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import zipfile
from collections import defaultdict
from pathlib import Path

from PIL import Image, ImageDraw

ROOT_DEFAULT = Path(__file__).resolve().parents[3]
CONTRACT_REL = Path("content/buildings/exterior_exact_region_review_contract_v1.json")
OUT_REL = Path("WORKSPACE/generated/structure_review/w54c_exterior_exact")
ZIP_REL = Path("WORKSPACE/generated/structure_review/Havenwild_W54C_ExteriorExactEvidence.zip")
CELL = 32


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def rgba_digest(image: Image.Image) -> str:
    return hashlib.sha256(image.convert("RGBA").tobytes()).hexdigest()


def cell_record(image: Image.Image, col: int, row: int) -> dict:
    x, y = col * CELL, row * CELL
    crop = image.crop((x, y, min(x + CELL, image.width), min(y + CELL, image.height))).convert("RGBA")
    if crop.size != (CELL, CELL):
        padded = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
        padded.alpha_composite(crop)
        crop = padded
    alpha = crop.getchannel("A")
    bbox = alpha.getbbox()
    alpha_count = sum(1 for v in alpha.tobytes() if v)
    colors = crop.getcolors(maxcolors=CELL * CELL) or []
    return {
        "id": f"c{col}r{row}",
        "column": col,
        "row": row,
        "sourceRect": [x, y, CELL, CELL],
        "nonEmpty": bool(alpha_count),
        "alphaPixels": alpha_count,
        "alphaFraction": round(alpha_count / float(CELL * CELL), 6),
        "occupiedBoundsLocal": list(bbox) if bbox else None,
        "uniqueRgbaCount": len(colors),
        "rgbaSha256": rgba_digest(crop),
    }


def analyze(image: Image.Image) -> tuple[list[dict], list[dict]]:
    cols = math.ceil(image.width / CELL)
    rows = math.ceil(image.height / CELL)
    cells = [cell_record(image, c, r) for r in range(rows) for c in range(cols)]
    groups: dict[str, list[str]] = defaultdict(list)
    for c in cells:
        if c["nonEmpty"]:
            groups[c["rgbaSha256"]].append(c["id"])
    duplicates = [
        {"rgbaSha256": digest, "cellIds": ids, "count": len(ids)}
        for digest, ids in groups.items() if len(ids) > 1
    ]
    duplicates.sort(key=lambda g: (-g["count"], g["cellIds"][0]))
    return cells, duplicates


def make_board(image: Image.Image, out: Path, scale: int = 2) -> None:
    image = image.convert("RGBA")
    w, h = image.size
    scaled = image.resize((w * scale, h * scale), Image.Resampling.NEAREST)
    board = Image.new("RGBA", scaled.size, (24, 24, 24, 255))
    board.alpha_composite(scaled)
    draw = ImageDraw.Draw(board)
    for x in range(0, w + 1, CELL):
        draw.line((x * scale, 0, x * scale, h * scale), fill=(255, 48, 48, 235), width=1)
    for y in range(0, h + 1, CELL):
        draw.line((0, y * scale, w * scale, y * scale), fill=(255, 48, 48, 235), width=1)
    for r in range(math.ceil(h / CELL)):
        for c in range(math.ceil(w / CELL)):
            x, y = c * CELL * scale, r * CELL * scale
            draw.rectangle((x + 1, y + 1, x + 46, y + 15), fill=(0, 0, 0, 190))
            draw.text((x + 3, y + 2), f"c{c}r{r}", fill=(255, 240, 64, 255))
    out.parent.mkdir(parents=True, exist_ok=True)
    board.save(out)


def safe_name(family: str) -> str:
    return family.replace(".", "_").replace("/", "_").replace(" ", "_")


def process_source(root: Path, outroot: Path, entry: dict, reference_only: bool = False) -> dict | None:
    rel = entry["path"] if isinstance(entry, dict) else entry
    family = entry.get("family", Path(rel).stem) if isinstance(entry, dict) else Path(rel).stem
    role = entry.get("role", "building_reference") if isinstance(entry, dict) else "building_reference"
    status = entry.get("status", "reference_only") if isinstance(entry, dict) else "reference_only"
    path = root / rel
    if not path.is_file():
        return None
    image = Image.open(path).convert("RGBA")
    cells, duplicates = analyze(image)
    stem = safe_name(family)
    board_rel = OUT_REL / f"{stem}_grid_2x.png"
    cell_rel = OUT_REL / f"{stem}_cells.json"
    make_board(image, root / board_rel)
    payload = {
        "schema": "havenwild.exterior_source_cell_evidence.v1",
        "pass": "167Z109W54C",
        "family": family,
        "role": role,
        "status": status,
        "referenceOnly": bool(reference_only),
        "sourcePath": rel,
        "sourceSha256": sha256_file(path),
        "sourceSize": [image.width, image.height],
        "grid": [math.ceil(image.width / CELL), math.ceil(image.height / CELL)],
        "cellSize": [CELL, CELL],
        "cells": cells,
        "duplicatePixelGroups": duplicates,
        "warning": "Cell statistics and duplicate pixels never assign wall facing/topology. Human review is required."
    }
    (root / cell_rel).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return {
        "family": family,
        "role": role,
        "status": status,
        "referenceOnly": bool(reference_only),
        "sourcePath": rel,
        "sourceSha256": payload["sourceSha256"],
        "sourceSize": payload["sourceSize"],
        "grid": payload["grid"],
        "board": board_rel.as_posix(),
        "cellEvidence": cell_rel.as_posix(),
        "nonEmptyCells": sum(1 for c in cells if c["nonEmpty"]),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=ROOT_DEFAULT)
    ap.add_argument("--require-all", action="store_true")
    args = ap.parse_args()
    root = args.root.resolve()
    contract = json.loads((root / CONTRACT_REL).read_text(encoding="utf-8"))
    outroot = root / OUT_REL
    if outroot.exists():
        shutil.rmtree(outroot)
    outroot.mkdir(parents=True, exist_ok=True)

    present: list[dict] = []
    missing: list[str] = []
    for entry in contract.get("sources", []):
        rec = process_source(root, outroot, entry)
        if rec is None:
            missing.append(entry["path"])
        else:
            present.append(rec)
    for rel in contract.get("referenceOnlyBuildingSheets", []):
        rec = process_source(root, outroot, rel, reference_only=True)
        if rec is None:
            missing.append(rel)
        else:
            present.append(rec)

    if missing and args.require_all:
        raise SystemExit("W54C source dependency missing: " + ", ".join(missing))
    if not present:
        print("W54C exterior evidence deferred: pinned LPC source mount is unavailable")
        print("Run Control Center option 18 first on the Windows project, then rerun option 59.")
        return 0

    manifest = {
        "schema": "havenwild.exterior_exact_review_evidence.v1",
        "pass": "167Z109W54C",
        "sourceCommit": contract["sourceCommit"],
        "cellSize": [CELL, CELL],
        "sources": present,
        "missingSources": missing,
        "publicationAllowed": False,
        "reviewRule": "Human review assigns exact facade/topology roles. Whole-building sheets are composition references only."
    }
    (outroot / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    selection = {
        "schema": "havenwild.exterior_exact_region_selection_template.v1",
        "pass": "167Z109W54C",
        "instructions": [
            "Choose only exact source rectangles verified on the labelled boards.",
            "Do not rotate/mirror a front wall to manufacture side/back facings.",
            "Whole-house sheets are reference-only and cannot be selected as placeables.",
            "Selections remain evidence until a later source-controlled publication pass."
        ],
        "selections": [
            {"role": role, "family": None, "sourceRect": None, "cellIds": [], "reviewNote": ""}
            for role in contract.get("requiredExteriorRoles", [])
        ]
    }
    (outroot / "exterior_selection_template_v1.json").write_text(json.dumps(selection, indent=2) + "\n", encoding="utf-8")

    zip_path = root / ZIP_REL
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(outroot.rglob("*")):
            if p.is_file():
                z.write(p, p.relative_to(outroot.parent))
    print(f"W54C exterior exact-source evidence: {len(present)}/{len(contract.get('sources', [])) + len(contract.get('referenceOnlyBuildingSheets', []))} source sheet(s)")
    print(f"evidence: {OUT_REL}")
    print(f"upload bundle: {ZIP_REL}")
    if missing:
        print(f"missing source sheets: {len(missing)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
