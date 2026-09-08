#!/usr/bin/env python3
"""Build W45C exact LPC structural-surface runtime cache.

W45C promotes representative interior floor/wall/cutaway/window source regions
through PublishedWorldAssetRegistry. Raw LPC sources remain immutable external
dependencies. When they are mounted, hashes are verified and this cache is
rebuilt deterministically. Compact source rollups keep the checked-in cache.
"""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
from PIL import Image

ROOT_DEFAULT = Path(__file__).resolve().parents[3]
CACHE_PNG = Path("assets/generated/havenwild_structure_surfaces_w45c.png")
CACHE_JSON = Path("assets/generated/havenwild_structure_surfaces_w45c.json")
SOURCES = {
    "floor": (
        "assets/source/licensed/lpc_revised/Structure/Floor/Wood Floor B.png",
        "0c9e5393b22c3fb63f498d41b7ec6b61d441ca5b750f9f249635420943f498f0",
    ),
    "drywall": (
        "assets/source/licensed/lpc_revised/Structure/Walls/Drywall.png",
        "46a4e9502542f941551aa50d6cbbc7a73aaf3c1e5e56bcfdcd6ec5c9db7e9349",
    ),
    "cutaway": (
        "assets/source/licensed/lpc_revised/Structure/Walls/CutawayOverlay.png",
        "2f8f650d4b5323d469f321023f6d9d3d4f3399f9374526de00ac14b416419c26",
    ),
    "panels": (
        "assets/source/licensed/lpc_revised/Structure/Walls/Panels A.png",
        "3c61ce8ff88fd4bc97a3e3bd5af40b361afc697a06602024e9c7a14c131203e5",
    ),
    "windows": (
        "assets/source/licensed/lpc_revised/Structure/Windows/Ornamental Windows B.png",
        "688ea2b7aff0156021481d948d535d7f26a808a4719bea5a464f1850c7d6df56",
    ),
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def copy_rect(atlas: Image.Image, source: Image.Image, source_rect, cache_xy):
    x, y, w, h = source_rect
    crop = source.crop((x, y, x + w, y + h))
    atlas.alpha_composite(crop, cache_xy)
    return [cache_xy[0], cache_xy[1], w, h]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=ROOT_DEFAULT)
    ap.add_argument("--require-source", action="store_true")
    args = ap.parse_args()
    root = args.root.resolve()
    resolved = {k: (root / rel, rel, expected) for k, (rel, expected) in SOURCES.items()}
    missing = [rel for _, rel, _ in resolved.values() if not (root / rel).is_file()]
    if missing:
        if args.require_source or not (root / CACHE_PNG).is_file() or not (root / CACHE_JSON).is_file():
            raise SystemExit("W45C source dependency missing: " + ", ".join(missing))
        print(
            f"W45C raw LPC dependency unavailable ({len(missing)} file(s)); "
            "retained checked-in deterministic runtime cache"
        )
        return 0

    for path, rel, expected in resolved.values():
        actual = sha256(path)
        if actual != expected:
            raise SystemExit(f"W45C pinned source hash drift: {rel}: {actual} != {expected}")

    atlas = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    entries = {}

    floor = Image.open(resolved["floor"][0]).convert("RGBA")
    for name, source_rect, cache_xy in (
        ("floor_wood_herringbone_light", [0, 0, 32, 32], (0, 0)),
        ("floor_wood_herringbone_dark", [32, 0, 32, 32], (32, 0)),
    ):
        entries[name] = {
            "cacheRect": copy_rect(atlas, floor, source_rect, cache_xy),
            "sourcePath": resolved["floor"][1],
            "sourceRect": source_rect,
            "normalization": "exact_copy",
        }

    drywall = Image.open(resolved["drywall"][0]).convert("RGBA")
    source_rect = [192, 0, 32, 96]
    entries["wall_drywall_simple"] = {
        "cacheRect": copy_rect(atlas, drywall, source_rect, (64, 0)),
        "sourcePath": resolved["drywall"][1],
        "sourceRect": source_rect,
        "normalization": "exact_vertical_wall_strip",
    }

    panels = Image.open(resolved["panels"][0]).convert("RGBA")
    for name, source_rect, cache_xy in (
        ("wall_panel_ornate_gold", [0, 0, 32, 64], (96, 0)),
        ("wall_panel_ornate_blue", [32, 0, 32, 64], (128, 0)),
    ):
        entries[name] = {
            "cacheRect": copy_rect(atlas, panels, source_rect, cache_xy),
            "sourcePath": resolved["panels"][1],
            "sourceRect": source_rect,
            "normalization": "exact_wall_overlay",
        }

    cutaway = Image.open(resolved["cutaway"][0]).convert("RGBA")
    cutaway_rows = (
        ("wall_cutaway_cap_left", [0, 0, 32, 32], (160, 0), "west_end"),
        ("wall_cutaway_cap_center", [32, 0, 32, 32], (192, 0), "straight"),
        ("wall_cutaway_cap_right", [64, 0, 32, 32], (224, 0), "east_end"),
        ("wall_cutaway_cap_south", [0, 32, 32, 32], (160, 32), "south_face"),
    )
    for name, source_rect, cache_xy, topology in cutaway_rows:
        entries[name] = {
            "cacheRect": copy_rect(atlas, cutaway, source_rect, cache_xy),
            "sourcePath": resolved["cutaway"][1],
            "sourceRect": source_rect,
            "normalization": "exact_cutaway_overlay_cell",
            "topology": topology,
        }

    windows = Image.open(resolved["windows"][0]).convert("RGBA")
    window_states = (
        ("unlit", [0, 64, 32, 64], (0, 128)),
        ("day", [32, 64, 32, 64], (32, 128)),
        ("lit", [64, 64, 32, 64], (64, 128)),
    )
    for state, source_rect, cache_xy in window_states:
        key = f"window_ornamental_tall:{state}"
        entries[key] = {
            "cacheRect": copy_rect(atlas, windows, source_rect, cache_xy),
            "sourcePath": resolved["windows"][1],
            "sourceRect": source_rect,
            "normalization": "exact_two_cell_window",
        }

    (root / CACHE_PNG).parent.mkdir(parents=True, exist_ok=True)
    atlas.save(root / CACHE_PNG)
    metadata = {
        "schema": "havenwild.structure_surface_runtime_cache.v1",
        "pass": "167Z109W45C",
        "atlas": CACHE_PNG.as_posix(),
        "atlasSize": [256, 256],
        "sourceAuthority": "ElizaWy/LPC pinned Structure source dependency",
        "sourceHashes": {rel: expected for _, rel, expected in resolved.values()},
        "entries": entries,
    }
    (root / CACHE_JSON).write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print(f"W45C structure-surface runtime cache: {len(entries)} frame/component record(s) -> {CACHE_PNG}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
