#!/usr/bin/env python3
"""Validate the locked title, direct-source policy, rock extraction, and hydrology surface."""
from __future__ import annotations

import hashlib
import importlib.util
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[5]
TITLE = ROOT / "content/ui/havenwild_title_screen.png"
TITLE_SHA256 = "a6ee0a91ab5195695fd19d3552d1dcb412855cbfa75689fd043f753c5b4ca5d3"
TITLE_SIZE = (1672, 941)
REVISION = "167Z52-direct-source-title-rock-water-stabilization-v1"


def require(path: str) -> Path:
    candidate = ROOT / path
    if not candidate.is_file():
        raise SystemExit(f"missing required Z52 file: {path}")
    return candidate


def text(path: str) -> str:
    return require(path).read_text(encoding="utf-8")


def assert_contains(raw: str, tokens: list[str], label: str) -> None:
    missing = [token for token in tokens if token not in raw]
    if missing:
        raise SystemExit(f"{label} is missing: {', '.join(missing)}")


def assert_absent(raw: str, tokens: list[str], label: str) -> None:
    found = [token for token in tokens if token in raw]
    if found:
        raise SystemExit(f"{label} still contains retired source-rewriter markers: {', '.join(found)}")


def validate_title() -> None:
    if not TITLE.is_file():
        raise SystemExit("accepted Havenwild title image is missing")
    if hashlib.sha256(TITLE.read_bytes()).hexdigest() != TITLE_SHA256:
        raise SystemExit("accepted Havenwild title image checksum changed")
    with Image.open(TITLE) as image:
        if image.size != TITLE_SIZE:
            raise SystemExit(f"accepted Havenwild title dimensions changed: {image.size}")

    frontend = text("crates/haven_game/src/client_frontend.rs")
    draw = text("crates/haven_game/src/client_character_frontend_draw.rs")
    assert_contains(
        frontend,
        [
            'content/ui/havenwild_title_screen.png',
            "draw_title_menu_background",
            "main_continue_rect",
            "main_settings_rect",
            "main_multiplayer_rect",
            "draw_frontend_backdrop",
        ],
        "frontend title integration",
    )
    assert_contains(
        draw,
        [
            "const TITLE_SOURCE_W: f32 = 1672.0;",
            "const TITLE_SOURCE_H: f32 = 941.0;",
            "Rect::new(154.0, 320.0, 356.0, 92.0)",
            "Rect::new(154.0, 416.0, 356.0, 92.0)",
            "Rect::new(154.0, 513.0, 356.0, 90.0)",
            "Rect::new(154.0, 608.0, 356.0, 91.0)",
            "Rect::new(154.0, 704.0, 356.0, 91.0)",
            "Rect::new(154.0, 799.0, 356.0, 92.0)",
        ],
        "title hitbox mapping",
    )
    assert_absent(
        draw,
        ["YOUR HAVEN", "NEWS & UPDATES", "BEGIN YOUR STORY", "draw_main_menu_shell"],
        "active title renderer",
    )


def validate_direct_source_policy() -> None:
    retired = [
        "Repair-FrontendRuntimeSurfaceV167Z46.py",
        "Repair-HavenGameClippySurfaceV167Z48.py",
        "Repair-VisualRegressionSurfaceV167Z49.py",
        "Repair-VisualRegressionSurfaceV167Z50.py",
        "Repair-VisualRegressionSurfaceV167Z51.py",
    ]
    for path in ("tools/build/Build.sh", "tools/build/Build.ps1"):
        raw = text(path)
        assert_absent(raw, retired, path)
        assert_contains(raw, ["Active Rust sources are authoritative"], path)


def load_promoter():
    path = require("tools/automation/assets/Promote-LpcRuntimeAssets.py")
    spec = importlib.util.spec_from_file_location("havenwild_lpc_promoter_z52", path)
    if spec is None or spec.loader is None:
        raise SystemExit("could not load LPC promoter")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate_rock_extraction() -> None:
    promoter = load_promoter()
    if promoter.OBJECT_REVISION_ID not in {REVISION, "167Z53-authored-rock-variant-selection-v1", "AC3R4F-tree-visible-natural-object-rebuild-v1"}:
        raise SystemExit("object atlas revision is not compatible with the Z52 visual baseline")
    if promoter.uses_grid_cell_authority("boulder"):
        raise SystemExit("boulders must not use one-cell crop authority")
    promoter_source = text("tools/automation/assets/Promote-LpcRuntimeAssets.py")
    assert_absent(
        promoter_source,
        ["candidates[min(rank, len(candidates) - 1)]"],
        "authored rock selection",
    )
    assert_contains(
        promoter_source,
        ["rock_variant_components", "return [None, None, None, None]"],
        "authored rock selection",
    )

    with tempfile.TemporaryDirectory() as temporary:
        path = Path(temporary) / "synthetic_rocks.png"
        image = Image.new("RGBA", (128, 96), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        # One 20x20 rock, one 54x28 rock, one 48x52 rock, and one tall rock.
        draw.rectangle((4, 4, 23, 23), fill=(90, 80, 75, 255))
        draw.rectangle((35, 4, 88, 31), fill=(100, 90, 80, 255))
        draw.rectangle((4, 38, 51, 89), fill=(85, 78, 72, 255))
        draw.rectangle((80, 40, 107, 91), fill=(95, 84, 76, 255))
        # Diagonal contact must not merge the first two components.
        image.putpixel((24, 24), (90, 80, 75, 255))
        image.putpixel((25, 25), (100, 90, 80, 255))
        image.save(path)
        components = promoter.rock_variant_components(path)
        if len(components) != 4 or any(component is None for component in components):
            raise SystemExit("synthetic rock audit did not fill all four fixed size slots")
        dimensions = {
            (bbox[2] - bbox[0], bbox[3] - bbox[1])
            for component in components
            for bbox, _area in [component]
        }
        if not any(width <= 32 and height <= 32 for width, height in dimensions):
            raise SystemExit("rock audit did not retain a one-cell authored rock")
        if not any(width > 32 or height > 32 for width, height in dimensions):
            raise SystemExit("rock audit did not retain a multi-cell authored rock")

    footprint = text("crates/haven_core/src/foundation/object_footprint.rs")
    entities = text("crates/haven_core/src/foundation/authored_entities.rs")
    assert_contains(
        footprint,
        ["footprint_for_cell", 'deterministic_object_variant("boulder"', "visual_w: 2"],
        "boulder footprint contract",
    )
    assert_contains(entities, ["kind.footprint_for_cell(x, y)"], "placed-object constructors")


def validate_hydrology() -> None:
    shoreline = text("crates/haven_world/src/autotile/shoreline_resolver.rs")
    lifecycle = text("crates/haven_world/src/autotile/shore_water_lifecycle.rs")
    family = shoreline + "\n" + lifecycle
    assert_contains(
        family,
        [
            "BinaryHeap",
            "const SHALLOW_BAND_COST: usize = 18;",
            ".is_some_and(|slot| !is_depth_water(snapshot[slot]))",
            "mainland_hydrology",
            "ShoreWaterDomain::Marine",
            "ShoreWaterDomain::Inland",
            "dominant_shallow_water_tile",
            "TileKind::OceanShallow",
            "TileKind::OceanDeep",
        ],
        "hydrology resolver module family",
    )


def main() -> int:
    validate_title()
    validate_direct_source_policy()
    validate_rock_extraction()
    validate_hydrology()
    print("Havenwild Z52 direct visual baseline validated")
    print(f"- title: {TITLE_SIZE[0]}x{TITLE_SIZE[1]} sha256 {TITLE_SHA256}")
    print("- build-time Rust source rewriters: disabled")
    print("- rocks: individual authored one-cell and multi-cell components")
    print("- water: marine/inland identity with distance-based shallow bands")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
