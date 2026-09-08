#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[3]
MANIFEST = ROOT / "content/worldgen/scene_rectangle_manifest_v0_8.json"
OUTPUT = ROOT / "content/worldgen/island_previews"
MAP_W = 96
MAP_H = 64
MASK = (1 << 64) - 1
GOLDEN_ANGLE = 2.3999631

COLORS = {
    "deep_water": (10, 48, 82, 255),
    "shallow_water": (31, 102, 135, 255),
    "sand": (201, 180, 121, 255),
    "grass": (80, 137, 76, 255),
}


def splitmix64(value: int) -> int:
    value &= MASK
    value = ((value ^ (value >> 30)) * 0xBF58476D1CE4E5B9) & MASK
    value = ((value ^ (value >> 27)) * 0x94D049BB133111EB) & MASK
    return (value ^ (value >> 31)) & MASK


class SeededLayoutRng:
    def __init__(self, seed: int) -> None:
        self.state = splitmix64(max(1, seed))

    def next_u64(self) -> int:
        self.state = splitmix64((self.state + 0x9E3779B97F4A7C15) & MASK)
        return self.state

    def next_unit(self) -> float:
        return (self.next_u64() & 0xFFFFFFFF) / 0xFFFFFFFF


def rerolled_seed(current_seed: int, reroll_index: int) -> int:
    return splitmix64(
        current_seed
        + max(1, reroll_index) * 0x9E3779B97F4A7C15
    )


def hash01(x: int, y: int, seed: int) -> float:
    value = (
        seed
        ^ ((x & MASK) * 0x9E3779B97F4A7C15)
        ^ ((y & MASK) * 0xC2B2AE3D27D4EB4F)
    ) & MASK
    return (splitmix64(value) & 0xFFFFFFFF) / 0xFFFFFFFF


def smoothstep(value: float) -> float:
    return value * value * (3.0 - 2.0 * value)


def smooth_noise(x: float, y: float, seed: int, scale: float) -> float:
    sx = x / max(scale, 1.0)
    sy = y / max(scale, 1.0)
    x0 = math.floor(sx)
    y0 = math.floor(sy)
    tx = smoothstep(sx - x0)
    ty = smoothstep(sy - y0)
    a = hash01(x0, y0, seed)
    b = hash01(x0 + 1, y0, seed)
    c = hash01(x0, y0 + 1, seed)
    d = hash01(x0 + 1, y0 + 1, seed)
    top = a + (b - a) * tx
    bottom = c + (d - c) * tx
    return top + (bottom - top) * ty


def slug(value: str) -> str:
    return "_".join(
        "".join(ch.lower() if ch.isalnum() else " " for ch in value).split()
    ) or "island"


def rectangles_overlap_with_gap(
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


def collect_footprints(manifest: dict) -> list[dict]:
    grouped: dict[int, list[dict]] = defaultdict(list)
    for rectangle in manifest["scene_rectangles"]:
        if rectangle.get("grid_x") is None or rectangle.get("grid_y") is None:
            continue
        grouped[int(rectangle["landmass_id"])].append(rectangle)

    footprints = []
    for landmass_id, rectangles in sorted(grouped.items()):
        min_grid_x = min(int(entry["grid_x"]) for entry in rectangles)
        min_grid_y = min(int(entry["grid_y"]) for entry in rectangles)
        cell_width = max(int(entry["world_rect_preview_px"][2]) for entry in rectangles)
        cell_height = max(int(entry["world_rect_preview_px"][3]) for entry in rectangles)
        cells = []
        width = 1
        height = 1
        for rectangle in rectangles:
            local_x = (int(rectangle["grid_x"]) - min_grid_x) * cell_width
            local_y = (int(rectangle["grid_y"]) - min_grid_y) * cell_height
            width = max(width, local_x + int(rectangle["world_rect_preview_px"][2]))
            height = max(height, local_y + int(rectangle["world_rect_preview_px"][3]))
            cells.append((rectangle, local_x, local_y))
        footprints.append(
            {
                "id": landmass_id,
                "name": rectangles[0]["landmass_name"],
                "width": width,
                "height": height,
                "cells": cells,
            }
        )
    return footprints


def clamp_placement(
    candidate: tuple[int, int, int, int],
    canvas_width: int,
    canvas_height: int,
    margin: int,
) -> tuple[int, int, int, int]:
    x, y, width, height = candidate
    x = max(margin, min(canvas_width - margin - width, x))
    y = max(margin, min(canvas_height - margin - height, y))
    return x, y, width, height


def generate_layout(manifest: dict, seed: int) -> dict[int, tuple[int, int, int, int]]:
    generation = manifest.setdefault("archipelago_generation", {})
    canvas_width, canvas_height = generation.get("canvas_size_px", [1800, 1200])
    margin = max(0, int(generation.get("outer_margin_px", 70)))
    minimum_gap = max(0, int(generation.get("minimum_island_gap_px", 120)))
    footprints = collect_footprints(manifest)
    if not footprints:
        raise RuntimeError("archipelago has no exterior landmasses")

    main = next((entry for entry in footprints if entry["id"] == 0), footprints[0])
    if main["width"] + margin * 2 > canvas_width or main["height"] + margin * 2 > canvas_height:
        raise RuntimeError("mainland does not fit inside the configured archipelago canvas")

    placed: dict[int, tuple[int, int, int, int]] = {
        int(main["id"]): (
            (canvas_width - int(main["width"])) // 2,
            (canvas_height - int(main["height"])) // 2,
            int(main["width"]),
            int(main["height"]),
        )
    }
    others = [entry for entry in footprints if entry["id"] != main["id"]]
    rng = SeededLayoutRng(seed)
    phase = rng.next_unit() * math.tau
    island_count = max(1, len(others))

    for index, footprint in enumerate(others):
        width = int(footprint["width"])
        height = int(footprint["height"])
        if width + margin * 2 > canvas_width or height + margin * 2 > canvas_height:
            raise RuntimeError(f"{footprint['name']} does not fit inside the archipelago canvas")
        base_angle = (
            phase
            + math.tau * index / island_count
            + (rng.next_unit() - 0.5) * 0.30
        )
        chosen = None
        for attempt in range(360):
            ring = attempt // 72
            angle = base_angle + (attempt % 72) * GOLDEN_ANGLE
            radial = 0.82 + ring * 0.04 + (rng.next_unit() - 0.5) * 0.10
            radius_x = (canvas_width * 0.5 - margin - width * 0.5) * radial
            radius_y = (canvas_height * 0.5 - margin - height * 0.5) * radial
            center_x = canvas_width * 0.5 + math.cos(angle) * radius_x
            center_y = canvas_height * 0.5 + math.sin(angle) * radius_y
            candidate = clamp_placement(
                (
                    math.floor(center_x - width * 0.5 + 0.5),
                    math.floor(center_y - height * 0.5 + 0.5),
                    width,
                    height,
                ),
                canvas_width,
                canvas_height,
                margin,
            )
            if all(
                not rectangles_overlap_with_gap(candidate, existing, minimum_gap)
                for existing in placed.values()
            ):
                chosen = candidate
                break
        if chosen is None:
            max_x = canvas_width - margin - width
            max_y = canvas_height - margin - height
            for y in range(margin, max_y + 1, 20):
                for x in range(margin, max_x + 1, 20):
                    candidate = (x, y, width, height)
                    if all(
                        not rectangles_overlap_with_gap(candidate, existing, minimum_gap)
                        for existing in placed.values()
                    ):
                        chosen = candidate
                        break
                if chosen is not None:
                    break
        if chosen is None:
            raise RuntimeError(
                f"could not place {footprint['name']} with a {minimum_gap}px minimum gap"
            )
        placed[int(footprint["id"])] = chosen

    for footprint in footprints:
        placement_x, placement_y, _, _ = placed[int(footprint["id"])]
        for rectangle, local_x, local_y in footprint["cells"]:
            rectangle["world_rect_preview_px"][0] = placement_x + local_x
            rectangle["world_rect_preview_px"][1] = placement_y + local_y

    generation.update(
        {
            "seed": int(seed),
            "layout_version": 1,
            "canvas_size_px": [int(canvas_width), int(canvas_height)],
            "outer_margin_px": margin,
            "minimum_island_gap_px": minimum_gap,
            "placement_mode": "seeded_collision_safe_ring",
        }
    )
    generation.setdefault("reroll_index", 0)
    return placed


def profile(landmass_id: int, world_w: int, world_h: int, seed: int) -> dict[str, float]:
    id_seed = (seed ^ ((landmass_id & MASK) * 0x9E3779B9)) & MASK
    compactness = 0.965 if landmass_id == 0 else 0.90
    return {
        "center_x": world_w * 0.5 + (hash01(3, 7, id_seed) - 0.5) * world_w * 0.055,
        "center_y": world_h * 0.49 + (hash01(11, 5, id_seed) - 0.5) * world_h * 0.045,
        "radius_x": world_w * 0.49 * compactness,
        "radius_y": world_h * 0.48 * compactness,
        "exponent": 2.55 if landmass_id == 0 else 2.15 + hash01(2, 9, id_seed) * 0.65,
        "roughness": 0.080 if landmass_id == 0 else 0.105,
        "lobes": 0.045 if landmass_id == 0 else 0.070,
    }


def assembly_boundary_distance(
    grid_x: int,
    grid_y: int,
    local_x: float,
    local_y: float,
    occupied: set[tuple[int, int]],
) -> float:
    distances: list[float] = []
    if (grid_x - 1, grid_y) not in occupied:
        distances.append(local_x)
    if (grid_x + 1, grid_y) not in occupied:
        distances.append(MAP_W - local_x)
    if (grid_x, grid_y - 1) not in occupied:
        distances.append(local_y)
    if (grid_x, grid_y + 1) not in occupied:
        distances.append(MAP_H - local_y)
    return min(distances) if distances else math.inf


def tile_at(
    gx: float,
    gy: float,
    landmass_id: int,
    world_w: int,
    world_h: int,
    seed: int,
    grid_x: int,
    grid_y: int,
    local_x: float,
    local_y: float,
    occupied: set[tuple[int, int]],
) -> str:
    p = profile(landmass_id, world_w, world_h, seed)
    dx = (gx - p["center_x"]) / max(p["radius_x"], 1.0)
    dy = (gy - p["center_y"]) / max(p["radius_y"], 1.0)
    exponent = p["exponent"]
    base = (abs(dx) ** exponent + abs(dy) ** exponent) ** (1.0 / exponent)
    angle = math.atan2(dy, dx)
    lobes = math.sin(angle * 3.0 + seed * 0.000001) * p["lobes"]
    lobes += math.cos(angle * 5.0 + 1.7) * p["lobes"] * 0.45
    broad = smooth_noise(gx, gy, seed ^ 0xA5A5, 20.0) - 0.5
    medium = smooth_noise(gx, gy, seed ^ 0x9911, 9.0) - 0.5
    distance = base + broad * p["roughness"] + medium * p["roughness"] * 0.38 + lobes
    boundary = assembly_boundary_distance(grid_x, grid_y, local_x, local_y, occupied)
    if math.isfinite(boundary):
        assembly_edge = 1.08 - max(0.0, min(1.0, boundary / 10.0)) * 0.22
        distance = max(distance, assembly_edge)
    if distance > 1.055:
        return "deep_water"
    if distance > 0.985:
        return "shallow_water"
    if distance > 0.9006:
        return "sand"
    return "grass"


def generate_previews(manifest: dict) -> None:
    generation = manifest["archipelago_generation"]
    world_seed = int(generation["seed"])
    canvas_width, canvas_height = (int(value) for value in generation["canvas_size_px"])
    grouped: dict[int, list[dict]] = defaultdict(list)
    for rectangle in manifest["scene_rectangles"]:
        if rectangle.get("grid_x") is None or rectangle.get("grid_y") is None:
            continue
        grouped[int(rectangle["landmass_id"])].append(rectangle)

    OUTPUT.mkdir(parents=True, exist_ok=True)
    index = []
    generated_sources: dict[int, Image.Image] = {}
    landmass_preview_bounds: dict[int, tuple[int, int, int, int]] = {}
    harbor_preview_points: dict[int, tuple[int, int]] = {}

    for landmass_id, rectangles in sorted(grouped.items()):
        min_x = min(int(entry["grid_x"]) for entry in rectangles)
        max_x = max(int(entry["grid_x"]) for entry in rectangles)
        min_y = min(int(entry["grid_y"]) for entry in rectangles)
        max_y = max(int(entry["grid_y"]) for entry in rectangles)
        world_w = (max_x - min_x + 1) * MAP_W
        world_h = (max_y - min_y + 1) * MAP_H
        island_seed = world_seed ^ ((landmass_id & MASK) * 0x9E3779B97F4A7C15)
        image = Image.new("RGBA", (world_w, world_h), COLORS["deep_water"])
        pixels = image.load()
        occupied = {(int(entry["grid_x"]), int(entry["grid_y"])) for entry in rectangles}
        for entry in rectangles:
            grid_x = int(entry["grid_x"])
            grid_y = int(entry["grid_y"])
            origin_x = (grid_x - min_x) * MAP_W
            origin_y = (grid_y - min_y) * MAP_H
            for local_y in range(MAP_H):
                for local_x in range(MAP_W):
                    x = origin_x + local_x
                    y = origin_y + local_y
                    pixels[x, y] = COLORS[
                        tile_at(
                            x + 0.5,
                            y + 0.5,
                            landmass_id,
                            world_w,
                            world_h,
                            island_seed,
                            grid_x,
                            grid_y,
                            local_x + 0.5,
                            local_y + 0.5,
                            occupied,
                        )
                    ]
        name = rectangles[0]["landmass_name"]
        filename = f"{slug(name)}.png"
        generated_sources[landmass_id] = image.copy()
        min_preview_x = min(int(entry["world_rect_preview_px"][0]) for entry in rectangles)
        min_preview_y = min(int(entry["world_rect_preview_px"][1]) for entry in rectangles)
        max_preview_x = max(
            int(entry["world_rect_preview_px"][0]) + int(entry["world_rect_preview_px"][2])
            for entry in rectangles
        )
        max_preview_y = max(
            int(entry["world_rect_preview_px"][1]) + int(entry["world_rect_preview_px"][3])
            for entry in rectangles
        )
        landmass_preview_bounds[landmass_id] = (
            min_preview_x,
            min_preview_y,
            max_preview_x,
            max_preview_y,
        )
        max_grid_y = max(int(entry["grid_y"]) for entry in rectangles)
        center_grid_x = (
            min(int(entry["grid_x"]) for entry in rectangles)
            + max(int(entry["grid_x"]) for entry in rectangles)
        ) / 2.0
        harbor_rectangle = min(
            (entry for entry in rectangles if int(entry["grid_y"]) == max_grid_y),
            key=lambda entry: abs(int(entry["grid_x"]) - center_grid_x),
        )
        hx, hy, hw, hh = (int(value) for value in harbor_rectangle["world_rect_preview_px"])
        harbor_preview_points[landmass_id] = (hx + hw // 2, hy + int(hh * 0.78))
        image.resize((world_w * 4, world_h * 4), Image.Resampling.NEAREST).save(
            OUTPUT / filename
        )
        index.append(
            {
                "landmass_id": landmass_id,
                "name": name,
                "scene_cells": len(rectangles),
                "source_tile_size": [world_w, world_h],
                "preview_bounds_px": [
                    min_preview_x,
                    min_preview_y,
                    max_preview_x - min_preview_x,
                    max_preview_y - min_preview_y,
                ],
                "preview_png": f"content/worldgen/island_previews/{filename}",
                "phase": "seeded_structural_grass_coast_only",
            }
        )
        print(f"generated {filename}: {len(rectangles)} scene cells")

    archipelago = Image.new(
        "RGBA", (canvas_width, canvas_height), COLORS["deep_water"]
    )
    route_catalog_path = ROOT / "content/worldgen/harbor_routes_v0_1.json"
    custom_routes = []
    if route_catalog_path.exists():
        custom_routes = json.loads(route_catalog_path.read_text(encoding="utf-8")).get(
            "routes", []
        )
    route_pairs = {(0, landmass_id) for landmass_id in harbor_preview_points if landmass_id != 0}
    route_pairs.update(
        (int(route["from_landmass_id"]), int(route["to_landmass_id"]))
        for route in custom_routes
    )
    route_draw = ImageDraw.Draw(archipelago)
    for from_id, to_id in sorted(route_pairs):
        if from_id in harbor_preview_points and to_id in harbor_preview_points:
            route_draw.line(
                [harbor_preview_points[from_id], harbor_preview_points[to_id]],
                fill=(72, 190, 235, 180),
                width=3,
            )

    for landmass_id, source in generated_sources.items():
        left, top, right, bottom = landmass_preview_bounds[landmass_id]
        target_size = (max(1, right - left), max(1, bottom - top))
        island = source.resize(target_size, Image.Resampling.NEAREST)
        archipelago.alpha_composite(island, (left, top))

    archipelago.save(OUTPUT / "archipelago.png")
    (OUTPUT / "index.json").write_text(
        json.dumps(
            {
                "schema": "havenwild.island_preview_index.v002",
                "world_seed": world_seed,
                "minimum_island_gap_px": int(generation["minimum_island_gap_px"]),
                "canvas_size_px": [canvas_width, canvas_height],
                "archipelago_preview": "content/worldgen/island_previews/archipelago.png",
                "islands": index,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(
        f"generated {len(index)} structural island previews plus archipelago.png "
        f"for seed {world_seed}"
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate a collision-safe seeded Havenwild structural archipelago"
    )
    parser.add_argument("--seed", type=int, help="explicit shareable world seed")
    parser.add_argument(
        "--reroll", action="store_true", help="derive and persist the next seed"
    )
    parser.add_argument(
        "--write-manifest",
        action="store_true",
        help="persist generated island positions and seed to the scene manifest",
    )
    args = parser.parse_args()

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    generation = manifest.setdefault("archipelago_generation", {})
    current_seed = int(generation.get("seed", 1337))
    reroll_index = int(generation.get("reroll_index", 0))
    seed = current_seed if args.seed is None else int(args.seed)
    if args.reroll:
        reroll_index += 1
        seed = rerolled_seed(current_seed, reroll_index)
        generation["reroll_index"] = reroll_index

    generate_layout(manifest, seed)
    if args.write_manifest:
        MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    generate_previews(manifest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
