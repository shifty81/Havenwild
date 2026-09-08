#!/usr/bin/env python3
"""Validate authored rock selection when an LPC sheet lacks a preferred silhouette."""
from __future__ import annotations

import importlib.util
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[5]
REVISION = "167Z53-authored-rock-variant-selection-v1"
R4F_REVISION = "AC3R4F-tree-visible-natural-object-rebuild-v1"


def load_promoter():
    path = ROOT / "tools/automation/assets/Promote-LpcRuntimeAssets.py"
    spec = importlib.util.spec_from_file_location("havenwild_lpc_promoter_z53", path)
    if spec is None or spec.loader is None:
        raise SystemExit("could not load LPC promoter")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def dimensions(component):
    bbox, _area = component
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def validate_missing_tall_preference(promoter) -> None:
    with tempfile.TemporaryDirectory() as temporary:
        path = Path(temporary) / "rocks_without_tall_slot.png"
        image = Image.new("RGBA", (160, 96), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        # Five distinct authored rocks, but no tall-and-narrow silhouette.
        draw.rectangle((4, 4, 23, 23), fill=(90, 80, 75, 255))
        draw.rectangle((36, 4, 89, 29), fill=(100, 90, 80, 255))
        draw.rectangle((96, 4, 151, 31), fill=(105, 93, 83, 255))
        draw.rectangle((4, 40, 51, 91), fill=(85, 78, 72, 255))
        draw.rectangle((64, 40, 127, 91), fill=(95, 84, 76, 255))
        image.save(path)

        variants = promoter.rock_variant_components(path)
        if len(variants) != 4 or any(item is None for item in variants):
            raise SystemExit("missing silhouette still prevents four stable rock variants")
        source_rects = {item[0] for item in variants}
        if len(source_rects) != 4:
            raise SystemExit("available authored rocks were aliased before distinct candidates were exhausted")
        if not any(w <= 32 and h <= 32 for w, h in map(dimensions, variants)):
            raise SystemExit("one-cell rock selection was lost")
        if not any(w > 32 or h > 32 for w, h in map(dimensions, variants)):
            raise SystemExit("multi-cell rock selection was lost")


def validate_small_source_alias(promoter) -> None:
    with tempfile.TemporaryDirectory() as temporary:
        path = Path(temporary) / "two_authored_rocks.png"
        image = Image.new("RGBA", (96, 64), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        draw.rectangle((4, 4, 23, 23), fill=(90, 80, 75, 255))
        draw.rectangle((36, 4, 87, 39), fill=(100, 90, 80, 255))
        image.save(path)

        variants = promoter.rock_variant_components(path)
        if len(variants) != 4 or any(item is None for item in variants):
            raise SystemExit("stable runtime rock IDs were not preserved for a small authored source")
        if len({item[0] for item in variants}) != 2:
            raise SystemExit("small-source aliases do not preserve the available authored components")


def main() -> int:
    promoter = load_promoter()
    if promoter.OBJECT_REVISION_ID not in {REVISION, R4F_REVISION}:
        raise SystemExit(f"unexpected object atlas revision: {promoter.OBJECT_REVISION_ID}")
    validate_missing_tall_preference(promoter)
    validate_small_source_alias(promoter)
    source = (ROOT / "tools/automation/assets/Promote-LpcRuntimeAssets.py").read_text(encoding="utf-8")
    for token in (
        "lpc_four_connected_authored_rock_alias",
        "rock_source_rects",
        "fewer than two distinct authored rock components",
        "cell.histogram()[0]",
    ):
        if token not in source:
            raise SystemExit(f"missing Z53 rock-selection contract token: {token}")
    print("Havenwild Z53 authored rock variant selection validated")
    print("- missing preferred silhouettes use remaining distinct authored components")
    print("- stable runtime IDs alias authored components only after distinct candidates are exhausted")
    print("- one-cell and multi-cell footprints remain derived from source rectangles")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
