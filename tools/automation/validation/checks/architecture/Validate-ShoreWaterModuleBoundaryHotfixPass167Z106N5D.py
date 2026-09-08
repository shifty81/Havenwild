from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[5]
SHORE = ROOT / "crates/haven_world/src/autotile/shoreline_resolver.rs"
LIFECYCLE = ROOT / "crates/haven_world/src/autotile/shore_water_lifecycle.rs"

def fail(message: str) -> None:
    print(f"FAILED Pass167Z106N5D shore-water module boundary hotfix: {message}")
    raise SystemExit(1)

for path in (SHORE, LIFECYCLE):
    if not path.is_file():
        fail(f"missing {path.relative_to(ROOT)}")

shore = SHORE.read_text(encoding="utf-8")
lifecycle = LIFECYCLE.read_text(encoding="utf-8")

required_import = "use super::shore_water_lifecycle::{deep_variant, is_depth_water, shallow_variant};"
if required_import not in shore:
    fail("shoreline_resolver.rs must import the three private lifecycle helpers it consumes")
if "normalize_authored_depth_topology_region" in shore:
    fail("shoreline_resolver.rs still carries the stale unused normalize_authored_depth_topology_region import")
for helper in ("shallow_variant", "deep_variant", "is_depth_water"):
    if f"pub(super) fn {helper}(" not in lifecycle:
        fail(f"{helper} must remain sibling-module visible via pub(super), not public API")
    if not re.search(rf"\b{helper}\(", shore):
        fail(f"shoreline_resolver.rs no longer consumes expected helper {helper}")

if len(shore.splitlines()) > 750:
    fail("shoreline_resolver.rs exceeds the 750-line focused-module ceiling")

print("Pass167Z106N5D shore-water module boundary hotfix validated")
