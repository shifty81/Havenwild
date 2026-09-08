#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
MANIFEST_PATH = ROOT / "content/worldgen/scene_rectangle_manifest_v0_8.json"
GENERATOR_PATH = ROOT / "tools/automation/worldgen/Generate-StructuralArchipelagoPreviews.py"


def bounds_by_landmass(manifest: dict) -> dict[int, tuple[int, int, int, int]]:
    grouped: dict[int, list[dict]] = defaultdict(list)
    for rectangle in manifest["scene_rectangles"]:
        if rectangle.get("grid_x") is None or rectangle.get("grid_y") is None:
            continue
        grouped[int(rectangle["landmass_id"])].append(rectangle)
    result = {}
    for landmass_id, rectangles in grouped.items():
        left = min(int(entry["world_rect_preview_px"][0]) for entry in rectangles)
        top = min(int(entry["world_rect_preview_px"][1]) for entry in rectangles)
        right = max(
            int(entry["world_rect_preview_px"][0]) + int(entry["world_rect_preview_px"][2])
            for entry in rectangles
        )
        bottom = max(
            int(entry["world_rect_preview_px"][1]) + int(entry["world_rect_preview_px"][3])
            for entry in rectangles
        )
        result[landmass_id] = (left, top, right - left, bottom - top)
    return result


def overlaps_with_gap(
    left: tuple[int, int, int, int],
    right: tuple[int, int, int, int],
    gap: int,
) -> bool:
    lx, ly, lw, lh = left
    rx, ry, rw, rh = right
    return not (
        lx + lw + gap <= rx
        or rx + rw + gap <= lx
        or ly + lh + gap <= ry
        or ry + rh + gap <= ly
    )


def validate_spacing(manifest: dict) -> None:
    generation = manifest.get("archipelago_generation")
    if not isinstance(generation, dict):
        raise SystemExit("scene rectangle manifest is missing archipelago_generation")
    if generation.get("placement_mode") != "seeded_collision_safe_ring":
        raise SystemExit("archipelago placement mode is not collision-safe seeded placement")
    if generation.get("canvas_size_px") != [1800, 1200]:
        raise SystemExit("archipelago canvas must remain 1800x1200 for this structural pass")
    gap = int(generation.get("minimum_island_gap_px", -1))
    if gap < 120:
        raise SystemExit("archipelago minimum gap must be at least 120px")
    margin = int(generation.get("outer_margin_px", -1))
    canvas_w, canvas_h = generation["canvas_size_px"]
    bounds = bounds_by_landmass(manifest)
    if len(bounds) != 10:
        raise SystemExit(f"expected 10 landmasses, found {len(bounds)}")
    for landmass_id, (x, y, width, height) in bounds.items():
        if x < margin or y < margin or x + width > canvas_w - margin or y + height > canvas_h - margin:
            raise SystemExit(f"landmass {landmass_id} violates the configured outer margin")
    ordered = sorted(bounds.items())
    for index, (left_id, left) in enumerate(ordered):
        for right_id, right in ordered[index + 1 :]:
            if overlaps_with_gap(left, right, gap):
                raise SystemExit(
                    f"landmasses {left_id} and {right_id} overlap or violate the {gap}px gap"
                )


def main() -> int:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    validate_spacing(manifest)

    spec = importlib.util.spec_from_file_location("havenwild_archipelago_preview", GENERATOR_PATH)
    if spec is None or spec.loader is None:
        raise SystemExit("could not load structural archipelago generator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    first = copy.deepcopy(manifest)
    second = copy.deepcopy(manifest)
    first_positions = module.generate_layout(first, 20260711)
    second_positions = module.generate_layout(second, 20260712)
    if first_positions == second_positions:
        raise SystemExit("different world seeds must produce different island placements")
    validate_spacing(first)
    validate_spacing(second)

    rust_layout = (ROOT / "crates/haven_world/src/archipelago_layout.rs").read_text(
        encoding="utf-8"
    )
    for marker in (
        "generate_archipelago_layout",
        "validate_archipelago_spacing",
        "rerolled_archipelago_seed",
        "seeded_layout_is_repeatable_and_collision_safe",
        "different_seeds_reposition_surrounding_islands",
    ):
        if marker not in rust_layout:
            raise SystemExit(f"Rust archipelago layout module is missing marker: {marker}")

    editor_source = (
        ROOT / "apps/haven_editor_native/src/app/island_authoring.rs"
    ).read_text(encoding="utf-8")
    for marker in (
        "regenerate_current_archipelago_seed",
        "reroll_structural_archipelago",
        "archipelago_generation.seed",
    ):
        if marker not in editor_source:
            raise SystemExit(f"native editor is missing seeded archipelago marker: {marker}")

    build_script = (ROOT / "tools/build/Build.sh").read_text(encoding="utf-8")
    if "island-reroll" not in build_script or "island-previews [seed]" not in build_script:
        raise SystemExit("tools/build/Build.sh is missing seeded archipelago commands")

    print("Seeded archipelago spacing / reroll validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
