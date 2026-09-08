from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
TESTS = ROOT / "crates/haven_world/src/autotile/shoreline_regression_tests.rs"
LIFECYCLE = ROOT / "crates/haven_world/src/autotile/shore_water_lifecycle.rs"


def fail(message: str) -> None:
    print(f"FAILED Pass167Z106N5E shoreline regression import hotfix: {message}")
    raise SystemExit(1)


for path in (TESTS, LIFECYCLE):
    if not path.is_file():
        fail(f"missing {path.relative_to(ROOT)}")

tests = TESTS.read_text(encoding="utf-8")
lifecycle = LIFECYCLE.read_text(encoding="utf-8")
required_import = (
    "use super::super::shore_water_lifecycle::"
    "normalize_authored_depth_topology_region;"
)
if required_import not in tests:
    fail("shoreline_regression_tests.rs must import the private lifecycle topology helper explicitly")
if "normalize_authored_depth_topology_region(" not in tests:
    fail("shoreline regression tests no longer exercise authored depth topology normalization")
if "pub(super) fn normalize_authored_depth_topology_region(" not in lifecycle:
    fail("topology normalization helper must remain sibling-module visible via pub(super)")
if "pub fn normalize_authored_depth_topology_region(" in lifecycle:
    fail("topology normalization helper was widened to public API")

print("Pass167Z106N5E shoreline regression import hotfix validated")
