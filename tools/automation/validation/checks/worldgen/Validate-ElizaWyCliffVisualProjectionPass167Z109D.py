#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[5]


def fail(message: str) -> None:
    raise SystemExit(f"ElizaWy cliff visual projection validation FAILED: {message}")


def load_json(rel: str):
    path = ROOT / rel
    if not path.is_file():
        fail(f"missing {rel}")
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read(rel: str) -> str:
    path = ROOT / rel
    if not path.is_file():
        fail(f"missing {rel}")
    return path.read_text(encoding="utf-8-sig")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require_tokens(source: str, tokens: tuple[str, ...], label: str) -> None:
    for token in tokens:
        if token not in source:
            fail(f"{label} missing {token}")


def main() -> None:
    contract = load_json("content/worldgen/elizawy_cliff_runtime_projection_v0_1.json")
    if contract.get("pass") not in {"167Z109D", "167Z109G"} or contract.get("status") != "active":
        fail("projection contract pass/status")

    authority = load_json("content/worldgen/structural_cliff_autotile_authority_v0_1.json")
    if authority.get("pass") not in {"167Z109D", "167Z109G"} or authority.get("status") != "active":
        fail("structural cliff authority pass/status")
    if authority["worldAuthority"]["sourceOfTruth"] != "TavernMap.structural_levels":
        fail("structural level authority changed")
    if authority["collisionAuthority"]["dependsOnArtwork"] is not False:
        fail("collision depends on artwork")

    output = ROOT / contract["runtimeProjection"]["path"]
    if not output.is_file():
        fail("runtime projection missing")
    if sha256(output) != contract["runtimeProjection"]["sha256"]:
        fail("runtime projection sha256")
    image = Image.open(output).convert("RGBA")
    if image.size != (512, 448):
        fail(f"runtime projection dimensions {image.size}")

    if contract.get("pass") == "167Z109G":
        # Z109G keeps the high/raised side of each rounded assembly visible in
        # V7's owner green and removes only the low receiver side. This catches
        # both the Z109C opaque foreign-green blocks and Z109D over-masking.
        v7_owner = tuple(contract["runtimeProjection"]["v7Source"]["grassOwnerRgb"])
        foreign_owner = (70, 130, 50)
        for column in (1, 3):
            crop = image.crop((column * 32, 6 * 32, (column + 1) * 32, 9 * 32))
            pixels = list(crop.get_flattened_data())
            if any(px[3] and px[:3] == foreign_owner for px in pixels):
                fail(f"foreign ElizaWy owner grass remains in c{column} diagonal")
            if not any(px[3] and px[:3] == v7_owner for px in pixels):
                fail(f"raised V7 owner grass missing in c{column} diagonal")
            if not any(px[3] == 0 for px in pixels):
                fail(f"low receiver transparency missing in c{column} diagonal")

        foot = image.crop((2 * 32, 8 * 32, 3 * 32, 9 * 32))
        grass_palette = {
            (70, 130, 50), (117, 167, 67), (48, 100, 47),
            (28, 69, 37), (37, 86, 46), (25, 51, 45),
        }
        if any(px[3] and px[:3] in grass_palette for px in foot.get_flattened_data()):
            fail("c2r8 straight foot still owns receiver grass")

        shapes = read("crates/haven_game/src/runtime_structural_cliff_shapes.rs")
        require_tokens(shapes, (
            "SOUTH_LIP_STRIP: Rect = source_crop(2, 7, 0, 24, 32, 8)",
            "body: source_cell(2, 3)",
            "foot: source_cell(2, 8)",
            "lip: source_cell(1, 6)",
            "shoulder: source_cell(1, 7)",
            "body: source_cell(1, 3)",
            "foot: source_cell(1, 8)",
            "CliffShape15::SouthWest => CliffVisualShape::SouthWestDiagonal",
            "CliffShape15::EastSouth => CliffVisualShape::SouthEastDiagonal",
        ), "Z109G shape recipes")

        draw = read("crates/haven_game/src/runtime_structural_cliff_draw.rs")
        require_tokens(draw, (
            "DiagonalFaceRecipe",
            "recipe.shoulder",
            "recipe.leading",
            "body_rows = 1 + extra_body_rows",
            "elizawy_cliff_runtime_overlay_summer.png",
        ), "Z109G renderer")

        generator = read("tools/automation/terrain/Build-ElizaWyCliffRuntimeOverlayPass167Z109D.py")
        require_tokens(generator, (
            "normalize_diagonal_receiver",
            "normalize_straight_foot_receiver",
            "adapt_owner_fill",
            "V7_GRASS_TILE_ID = 5",
            "STRAIGHT_FOOT_CELL = (2, 8)",
        ), "Z109G projection builder")

    print(f"ElizaWy cliff visual projection validation passed ({contract.get('pass')})")


if __name__ == "__main__":
    main()
