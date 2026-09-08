from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


build = read("tools/build/Build.sh")
start = build.index("  dev|all)")
end = build.index("    ;;", start)
fast = build[start:end]
if "cargo check --workspace --all-targets" not in fast:
    raise SystemExit("fast development build lost cargo workspace compile check")
if "cargo fmt" in fast or "rust_check_fast" in fast:
    raise SystemExit("fast development build must not block on formatting")
if "build_dev_apps" not in fast:
    raise SystemExit("fast development build no longer builds development apps")

ps1 = read("tools/build/Build.ps1")
all_line = next(line for line in ps1.splitlines() if line.strip().startswith('"all" {'))
if "Test-RustFormat" in all_line:
    raise SystemExit("PowerShell fast all path still blocks on Rust formatting")
if "Test-RustCheck" not in all_line or "Build-DevelopmentApplications" not in all_line:
    raise SystemExit("PowerShell fast all path lost compile/build gates")

tile_tests = read("crates/haven_core/src/foundation/tile_object_catalog_tests.rs")
if tile_tests.startswith("\n"):
    raise SystemExit("tile_object_catalog_tests.rs retains leading blank line rejected by rustfmt")

address = read("crates/haven_editor/src/world_surface_edit/address.rs")
expected = (
    "            let address =\n"
    "                resolve_world_surface_cell(manifest, assignments, world, landmass_id, global)\n"
    "                    .map_err(|error| {\n"
    "                        format!(\n"
)
if expected not in address:
    raise SystemExit("address.rs does not carry workstation rustfmt shape")

shore = read("crates/haven_world/src/autotile/shoreline_regression_tests.rs")
multiline = (
    "    normalize_shore_water_lifecycle_region(\n"
    "        &mut map,\n"
    "        0,\n"
    "        0,\n"
    "        MAP_W as i32 - 1,\n"
    "        MAP_H as i32 - 1,\n"
    "        3,\n"
    "    );\n"
)
if multiline in shore:
    raise SystemExit("shoreline regression tests retain rustfmt-rejected multiline lifecycle call")
if "    assert_eq!(map.get(MAP_W as i32 - 1, MAP_H as i32 - 1), TileKind::OceanDeep);" in shore:
    raise SystemExit("open-ocean regression assert retains rustfmt-rejected single-line form")

for rel in [
    "crates/haven_game/src/character_runtime_compositor.rs",
    "apps/haven_editor_native/src/app/world_surface_authoring.rs",
]:
    if len(read(rel).splitlines()) > 750:
        raise SystemExit(f"{rel} exceeds the 750-line focused-module ceiling")

for rel in [
    "crates/haven_game/src/character_runtime_compositor_tests.rs",
    "apps/haven_editor_native/src/app/world_surface_authoring_geometry.rs",
    "apps/haven_editor_native/src/app/world_surface_authoring_tests.rs",
]:
    if not (ROOT / rel).is_file():
        raise SystemExit(f"missing N5X2 focused module extraction: {rel}")

print("Pass167Z106N5X2 fast-development compile gate regression: passed")
