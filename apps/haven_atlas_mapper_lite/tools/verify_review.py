#!/usr/bin/env python3
"""Independent source-byte and pixel replay check for Atlas Mapper review exports.

This is a verification companion of the existing Rust mapper, not a second scene
editor or a replacement renderer. Requires Pillow for pixel equality.
"""
import argparse
import hashlib
import json
import pathlib
import sys


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def verify(ledger_path: pathlib.Path, png_path: pathlib.Path, root: pathlib.Path, receipt_path: pathlib.Path):
    from PIL import Image, ImageChops
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    if ledger.get("schema") != "havenwild.atlas_mapper_review.v0_1":
        raise ValueError("Unknown review schema")
    if ledger.get("approval") != "unreviewed_source_assembly_not_for_runtime":
        raise ValueError("Review must not claim automatic approval")
    sources = {}
    source_proof = []
    for source in ledger["source_assets"]:
        sid = source["id"]
        if not sid or sid in sources:
            raise ValueError("Duplicate or empty source identity")
        source_path = pathlib.Path(source["path"])
        if not source_path.is_absolute():
            source_path = root / source_path
        data = source_path.read_bytes()
        digest = sha256(data)
        claimed_hash = source.get("source_sha256")
        if claimed_hash is not None and digest != claimed_hash:
            raise ValueError(f"SOURCE HASH CHANGED: {sid}")
        with Image.open(source_path) as image:
            sources[sid] = image.convert("RGBA")
        source_proof.append({"id": sid, "sha256": digest, "bytes": len(data),
                             "expected_hash_pinned": claimed_hash is not None})
    min_x, min_y = ledger["output_grid_origin"]
    width, height = ledger["output_pixel_size"]
    if not (0 < width <= 8192 and 0 < height <= 8192):
        raise ValueError("Invalid render dimensions")
    canvas = Image.new("RGBA", (width, height))
    ids = set()
    for piece in sorted(ledger["placements"], key=lambda p: (p["layer"], p["id"])):
        pid = piece["id"]
        if pid in ids:
            raise ValueError(f"Duplicate piece id {pid}")
        ids.add(pid)
        sheet = sources.get(piece["source_asset_id"])
        if sheet is None:
            raise ValueError(f"Missing source id for piece {pid}")
        x, y, w, h = piece["source_rect"]
        if not (w == 32 and h == 32 and x >= 0 and y >= 0 and x + w <= sheet.width and y + h <= sheet.height):
            raise ValueError(f"Invalid original source rectangle for piece {pid}")
        crop = sheet.crop((x, y, x + w, y + h))
        if piece["flip_x"]:
            crop = crop.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        if piece["flip_y"]:
            crop = crop.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
        rotation = piece["rotation_degrees"] % 360
        if rotation not in (0, 90, 180, 270):
            raise ValueError(f"Unsupported transform for piece {pid}")
        # Pillow positive rotation is CCW; the Rust image crate rotate90 is CW.
        if rotation:
            crop = crop.rotate(-rotation, expand=False)
        left = (piece["canvas_grid_x"] - min_x) * 32
        top = (piece["canvas_grid_y"] - min_y) * 32
        if not (0 <= left <= width - 32 and 0 <= top <= height - 32):
            raise ValueError(f"Tile {pid} outside output")
        canvas.alpha_composite(crop, (left, top))
    seen_cells = set()
    for cell in ledger.get("heightmap", []):
        x, y = cell["x"], cell["y"]
        if (x, y) in seen_cells:
            raise ValueError("Duplicate heightmap cell")
        seen_cells.add((x, y))
        level, water = cell["elevation"], cell.get("water_surface")
        if not (0 <= level <= 30 and (water is None or 0 <= water <= 30)):
            raise ValueError("Heightmap level outside 0..30")
    with Image.open(png_path) as actual:
        actual = actual.convert("RGBA")
    if actual.size != canvas.size or ImageChops.difference(actual, canvas).getbbox() is not None:
        raise ValueError("Pixel replay differs from source ledger; refuse review certification")
    result = {"schema": "havenwild.atlas_mapper_source_proof.v0_1",
              "status": "source_hash_and_png_replay_verified_NOT_VISUAL_OR_RUNTIME_CERTIFIED",
              "scene_review_png_sha256": sha256(png_path.read_bytes()),
              "sources": source_proof, "placement_count": len(ids),
              "heightmap_cells": len(seen_cells),
              "all_source_hashes_pinned": all(s["expected_hash_pinned"] for s in source_proof),
              "visualApproval": False, "runtimeCertified": False}
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--ledger", type=pathlib.Path, required=True)
    p.add_argument("--png", type=pathlib.Path, required=True)
    p.add_argument("--repo", type=pathlib.Path, default=pathlib.Path.cwd())
    p.add_argument("--receipt", type=pathlib.Path)
    a = p.parse_args()
    receipt = a.receipt or a.png.with_suffix(".source-proof.json")
    result = verify(a.ledger, a.png, a.repo.resolve(), receipt)
    print("PASS observed source SHA-256 + independent pixel replay; candidate only")
    print("source hashes pinned:", result["all_source_hashes_pinned"])
    print("sources:", len(result["sources"]), "placements:", result["placement_count"])
    print("receipt:", receipt)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print("FAIL mapper review verification:", error, file=sys.stderr)
        sys.exit(1)
