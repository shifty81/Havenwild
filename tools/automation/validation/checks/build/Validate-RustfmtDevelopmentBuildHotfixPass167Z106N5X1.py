from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]

def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")

shore_tests = read("crates/haven_world/src/autotile/shoreline_regression_tests.rs")
if "    #[test]\n" in shore_tests:
    raise SystemExit("legacy nested shoreline #[test] indentation remains")
if not shore_tests.startswith(
    "use super::super::shore_water_lifecycle::normalize_authored_depth_topology_region;\nuse super::*;\n"
):
    raise SystemExit("shoreline regression import boundary drifted")

shore_resolver = read("crates/haven_world/src/autotile/shoreline_resolver.rs")
needle = "use super::shore_water_lifecycle::{deep_variant, is_depth_water, shallow_variant};"
if shore_resolver.count(needle) != 1:
    raise SystemExit("shoreline lifecycle helper import must appear exactly once")
if "Press any key to continue" in shore_resolver:
    raise SystemExit("console text contaminated shoreline resolver source")

for rel in [
    "apps/haven_editor_native/src/app/canvas_controller.rs",
    "crates/haven_game/src/runtime_editor_shell.rs",
]:
    text = read(rel)
    if 'self.status_message = format!(\n                        "Terrain paint mode:' in text:
        raise SystemExit(f"known pre-rustfmt terrain status layout remains in {rel}")

print("Pass167Z106N5X1 rustfmt development-build hotfix regression: passed")
