from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[5]
FOUNDATION = ROOT / "crates/haven_core/src/foundation.rs"
SCENE_WORLD = ROOT / "crates/haven_core/src/foundation/scene_world.rs"
SCENE_MIGRATION = ROOT / "crates/haven_core/src/foundation/scene_size_migration.rs"
RULES = ROOT / "crates/haven_core/src/foundation/starter_scene_rules.rs"

def fail(message: str) -> None:
    print(f"FAILED Pass167Z106N5C core-foundation module boundary hotfix: {message}")
    raise SystemExit(1)

for path in (FOUNDATION, SCENE_WORLD, SCENE_MIGRATION, RULES):
    if not path.is_file():
        fail(f"missing {path.relative_to(ROOT)}")

foundation = FOUNDATION.read_text(encoding="utf-8")
scene_world = SCENE_WORLD.read_text(encoding="utf-8")
migration = SCENE_MIGRATION.read_text(encoding="utf-8")

if "pub(super) use starter_scene_rules" in foundation or "pub use starter_scene_rules" in foundation:
    fail("foundation facade still re-exports private starter-scene implementation helpers")
if "rects_overlap" in re.search(r"use spatial_validation::\{.*?\};", foundation, re.S).group(0):
    fail("foundation facade still imports private rects_overlap helper it does not use")
if "validate_rect_bounds" in re.search(r"use spatial_validation::\{.*?\};", foundation, re.S).group(0):
    fail("foundation facade still imports private validate_rect_bounds helper it does not use")
required_scene_helpers = [
    "default_tile_rule", "default_tile_rules", "ensure_scene_access", "layered_scene_for",
    "starter_biome", "starter_transitions", "starter_zones", "tile_index",
]
for helper in required_scene_helpers:
    if helper not in scene_world:
        fail(f"scene_world.rs is missing direct starter_scene_rules import/use for {helper}")
if "use super::starter_scene_rules::starter_biome;" not in migration:
    fail("scene_size_migration.rs must import starter_biome directly from starter_scene_rules")

print("Pass167Z106N5C core-foundation module boundary hotfix validated")
