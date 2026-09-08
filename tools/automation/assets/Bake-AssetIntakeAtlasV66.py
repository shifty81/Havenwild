#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
CATALOG_PATH = ROOT / "content/assets/intake/asset_intake_catalog_v0_1.json"
EXPECTED_ATLAS = "assets/generated/user_imports/havenwild_intake_atlas_v0_1.png"
EXPECTED_MANIFEST = "assets/generated/user_imports/havenwild_intake_atlas_v0_1.json"
ALLOWED_LICENSES = {"project_owned", "cc0", "cc_by", "third_party_approved"}
ALLOWED_SOURCE_ROOTS = ("assets/source/intake/", "assets/source/original/")
PADDING = 2
EXTRUDE = 1
MAX_WIDTH = 1024


@dataclass(frozen=True)
class PreparedRecipe:
    record: dict
    image: Image.Image


def load_catalog() -> dict:
    if not CATALOG_PATH.is_file():
        raise ValueError(f"missing {CATALOG_PATH.relative_to(ROOT)}")
    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    if catalog.get("schema") != "havenwild.asset_intake_catalog.v0_1":
        raise ValueError(f"unsupported catalog schema {catalog.get('schema')}")
    if catalog.get("atlasOutput") != EXPECTED_ATLAS:
        raise ValueError(f"atlasOutput must be {EXPECTED_ATLAS}")
    if catalog.get("manifestOutput") != EXPECTED_MANIFEST:
        raise ValueError(f"manifestOutput must be {EXPECTED_MANIFEST}")
    return catalog


def validate_recipe(recipe: dict, seen_ids: set[str], seen_targets: set[str]) -> list[str]:
    errors: list[str] = []
    stable_id = str(recipe.get("stableId", ""))
    if not stable_id.startswith("import/"):
        errors.append(f"{stable_id or '<missing>'}: stableId must begin with import/")
    if stable_id in seen_ids:
        errors.append(f"{stable_id}: duplicate stableId")
    seen_ids.add(stable_id)

    source_path = str(recipe.get("sourcePath", "")).replace("\\", "/")
    if not source_path.startswith(ALLOWED_SOURCE_ROOTS):
        errors.append(f"{stable_id}: sourcePath must stay in approved source roots")
    source = ROOT / source_path
    if not source.is_file():
        errors.append(f"{stable_id}: missing source image {source_path}")

    target = recipe.get("target") or {}
    target_kind = target.get("kind")
    target_code = target.get("code")
    if target_kind not in {"tile", "object"} or not target_code:
        errors.append(f"{stable_id}: invalid target")
    target_id = f"{target_kind}/{target_code}"

    slice_rect = recipe.get("slice") or {}
    for key in ("x", "y", "width", "height"):
        if not isinstance(slice_rect.get(key), int):
            errors.append(f"{stable_id}: slice.{key} must be an integer")
    if int(slice_rect.get("width", 0)) <= 0 or int(slice_rect.get("height", 0)) <= 0:
        errors.append(f"{stable_id}: slice width and height must be positive")

    license_record = recipe.get("license") or {}
    if license_record.get("status") not in ALLOWED_LICENSES:
        errors.append(f"{stable_id}: license status does not permit promotion")
    if license_record.get("accepted") is not True:
        errors.append(f"{stable_id}: license acceptance is required")
    if license_record.get("status") == "cc_by" and not str(
        license_record.get("attribution", "")
    ).strip():
        errors.append(f"{stable_id}: CC-BY attribution is required")

    if recipe.get("promotionState") == "approved":
        if target_id in seen_targets:
            errors.append(f"{stable_id}: duplicate approved target {target_id}")
        seen_targets.add(target_id)
    return errors


def prepare_recipe(recipe: dict) -> PreparedRecipe:
    source = Image.open(ROOT / recipe["sourcePath"]).convert("RGBA")
    rect = recipe["slice"]
    x, y = rect["x"], rect["y"]
    width, height = rect["width"], rect["height"]
    if x < 0 or y < 0 or x + width > source.width or y + height > source.height:
        raise ValueError(
            f"{recipe['stableId']}: slice {(x, y, width, height)} exceeds source {source.size}"
        )
    return PreparedRecipe(recipe, source.crop((x, y, x + width, y + height)))


def shelf_pack(prepared: list[PreparedRecipe]) -> tuple[int, int, list[tuple[int, int]]]:
    positions: list[tuple[int, int]] = []
    x = PADDING
    y = PADDING
    row_height = 0
    used_width = 1
    for item in prepared:
        cell_w = item.image.width + PADDING * 2
        cell_h = item.image.height + PADDING * 2
        if x > PADDING and x + cell_w > MAX_WIDTH:
            x = PADDING
            y += row_height
            row_height = 0
        positions.append((x + PADDING, y + PADDING))
        x += cell_w
        row_height = max(row_height, cell_h)
        used_width = max(used_width, x + PADDING)
    used_height = max(1, y + row_height + PADDING)
    return used_width, used_height, positions


def extrude(atlas: Image.Image, tile: Image.Image, x: int, y: int) -> None:
    atlas.alpha_composite(tile, (x, y))
    if EXTRUDE <= 0:
        return
    atlas.alpha_composite(tile.crop((0, 0, tile.width, 1)), (x, y - 1))
    atlas.alpha_composite(tile.crop((0, tile.height - 1, tile.width, tile.height)), (x, y + tile.height))
    atlas.alpha_composite(tile.crop((0, 0, 1, tile.height)), (x - 1, y))
    atlas.alpha_composite(tile.crop((tile.width - 1, 0, tile.width, tile.height)), (x + tile.width, y))
    atlas.putpixel((x - 1, y - 1), tile.getpixel((0, 0)))
    atlas.putpixel((x + tile.width, y - 1), tile.getpixel((tile.width - 1, 0)))
    atlas.putpixel((x - 1, y + tile.height), tile.getpixel((0, tile.height - 1)))
    atlas.putpixel((x + tile.width, y + tile.height), tile.getpixel((tile.width - 1, tile.height - 1)))


def bake(catalog: dict, validate_only: bool) -> tuple[int, int]:
    recipes = sorted(catalog.get("recipes", []), key=lambda item: item.get("stableId", ""))
    errors: list[str] = []
    seen_ids: set[str] = set()
    seen_targets: set[str] = set()
    for recipe in recipes:
        errors.extend(validate_recipe(recipe, seen_ids, seen_targets))
    approved = [recipe for recipe in recipes if recipe.get("promotionState") == "approved"]
    if not approved:
        errors.append("catalog has no approved recipes")
    prepared: list[PreparedRecipe] = []
    if not errors:
        for recipe in approved:
            try:
                prepared.append(prepare_recipe(recipe))
            except Exception as exc:
                errors.append(str(exc))
    if errors:
        raise ValueError("\n".join(errors))
    if validate_only:
        return len(recipes), len(approved)

    width, height, positions = shelf_pack(prepared)
    atlas = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    entries: list[dict] = []
    for item, (x, y) in zip(prepared, positions):
        extrude(atlas, item.image, x, y)
        recipe = item.record
        entries.append(
            {
                "stableId": recipe["stableId"],
                "displayName": recipe["displayName"],
                "target": recipe["target"],
                "rect": [x, y, item.image.width, item.image.height],
                "pivot": recipe["pivot"],
                "footprint": recipe["footprint"],
                "sourcePath": recipe["sourcePath"],
                "sourceRect": recipe["slice"],
                "license": recipe["license"],
            }
        )

    atlas_path = ROOT / catalog["atlasOutput"]
    manifest_path = ROOT / catalog["manifestOutput"]
    atlas_path.parent.mkdir(parents=True, exist_ok=True)
    atlas.save(atlas_path, optimize=False, compress_level=9)
    manifest = {
        "schema": "havenwild.user_asset_atlas.v0_1",
        "atlas": catalog["atlasOutput"],
        "sourceCatalog": str(CATALOG_PATH.relative_to(ROOT)).replace("\\", "/"),
        "generatedBy": "tools/automation/assets/Bake-AssetIntakeAtlasV66.py",
        "packing": {
            "algorithm": "stable_id_sorted_shelf",
            "paddingPx": PADDING,
            "edgeExtrudePx": EXTRUDE,
            "maxWidth": MAX_WIDTH,
        },
        "size": [width, height],
        "entries": entries,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return len(recipes), len(approved)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate and bake Havenwild asset-intake atlas")
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    try:
        catalog = load_catalog()
        recipes, approved = bake(catalog, args.validate_only)
    except Exception as exc:
        print(f"Asset intake bake failed:\n{exc}", file=sys.stderr)
        return 1
    verb = "validated" if args.validate_only else "baked"
    print(f"Asset intake {verb}: {recipes} recipes, {approved} approved")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
