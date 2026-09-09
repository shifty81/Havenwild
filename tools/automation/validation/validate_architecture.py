#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CONFIG = ROOT / "content/architecture/rust_file_size_allowlist.json"


def line_count(path: Path) -> int:
    return len(path.read_text(encoding="utf-8", errors="strict").splitlines())


def fail(message: str, issues: list[str]) -> None:
    issues.append(message)




def require_source_tokens(rel: str, tokens: list[str], issues: list[str]) -> None:
    path = ROOT / rel
    if not path.exists():
        fail(f"spatial authority source is missing: {rel}", issues)
        return
    source = path.read_text(encoding="utf-8", errors="strict")
    for token in tokens:
        if token not in source:
            fail(f"{rel} is missing spatial authority token {token!r}", issues)

def main() -> int:
    issues: list[str] = []
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    default_limit = int(config["default_max_lines"])
    entrypoint_limit = int(config["entrypoint_max_lines"])
    exceptions = {entry["path"]: entry for entry in config.get("exceptions", [])}

    rust_files = sorted((ROOT / "crates").rglob("*.rs")) + sorted((ROOT / "apps").rglob("*.rs"))
    for path in rust_files:
        rel = path.relative_to(ROOT).as_posix()
        source = path.read_text(encoding="utf-8", errors="strict")
        for line_number, line in enumerate(source.splitlines(), start=1):
            if "/\\" in line or "\\/" in line:
                fail(
                    f"{rel}:{line_number} contains a mixed-separator path; use repository-relative forward slashes",
                    issues,
                )
        count = len(source.splitlines())
        exception = exceptions.get(rel)
        limit = int(exception["max_lines"]) if exception else default_limit
        if path.name == "main.rs" and exception is None:
            limit = min(limit, entrypoint_limit)
        if count > limit:
            fail(f"{rel} has {count} lines; limit {limit}", issues)

    for rel, entry in exceptions.items():
        path = ROOT / rel
        if not path.exists():
            fail(f"stale size exception references missing file: {rel}", issues)
            continue
        if not str(entry.get("reason", "")).strip():
            fail(f"size exception has no reason: {rel}", issues)
        target = int(entry.get("target_lines", entry["max_lines"]))
        if target > int(entry["max_lines"]):
            fail(f"size exception target exceeds temporary maximum: {rel}", issues)

    workspace = (ROOT / "Cargo.toml").read_text(encoding="utf-8")
    required_members = [
        '"apps/haven_editor_native"',
        '"crates/haven_authoring"',
        '"crates/haven_editor"',
    ]
    for member in required_members:
        if member not in workspace:
            fail(f"workspace missing member {member}", issues)

    editor_manifest = (ROOT / "crates/haven_editor/Cargo.toml").read_text(encoding="utf-8")
    if "autobins = false" not in editor_manifest:
        fail("haven_editor must be a headless library crate with autobins disabled", issues)
    if "macroquad.workspace" in editor_manifest:
        fail("haven_editor must not depend on Macroquad/windowing", issues)

    for crate in ("haven_render", "haven_net"):
        manifest = (ROOT / f"crates/{crate}/Cargo.toml").read_text(encoding="utf-8")
        if "haven_editor" in manifest:
            fail(f"{crate} must not depend on haven_editor", issues)
        if "haven_authoring" not in manifest:
            fail(f"{crate} must consume neutral haven_authoring contracts", issues)

    # HW-SPATIAL-01: placement meaning is a project-wide authority, not a
    # family of local +16/+0.5/-1 corrections. Terrain's half-tile tuple
    # presentation is intentionally retained, while structural stamps and
    # bottom-center physical roots use explicit independent contracts.
    for crate in ("haven_world", "haven_assets", "haven_render"):
        manifest = (ROOT / f"crates/{crate}/Cargo.toml").read_text(encoding="utf-8")
        if 'haven_spatial = { path = "../haven_spatial" }' not in manifest:
            fail(f"{crate} must consume the shared haven_spatial placement authority", issues)

    require_source_tokens(
        "crates/haven_spatial/src/lib.rs",
        [
            "pub struct TileCoord",
            "TerrainTuplePresentationOrigin",
            "StructuralHost",
            "StructuralReceiver",
            "tile_rect_bottom_center_tiles",
        ],
        issues,
    )
    require_source_tokens(
        "crates/haven_world/src/terrain_editor_bridge.rs",
        [
            "TERRAIN_TUPLE_PRESENTATION_OFFSET_TILES",
            "TileAnchor::TerrainTuplePresentationOrigin",
            "assert_ne!(terrain_tuple_render_origin_tiles(7, 11), (7.0, 11.0))",
        ],
        issues,
    )
    require_source_tokens(
        "crates/haven_assets/src/lpc_cliff_ramp_provider.rs",
        [
            "pub const fn stamp_origin",
            "(-1, 0)",
            "assert_ne!(origin, TileCoord::new(9, 19))",
        ],
        issues,
    )
    ramp_provider = (ROOT / "crates/haven_assets/src/lpc_cliff_ramp_provider.rs").read_text(encoding="utf-8")
    if "(-1, -1)" in ramp_provider:
        fail("directional cliff ramp provider reintroduced the retired one-row-up anchor", issues)

    require_source_tokens(
        "crates/haven_game/src/runtime_structural_cliff_ramps.rs",
        [
            "role.host_anchor_offset()",
            "global_y + i32::from(anchor_y)",
            "draw_cliff_source_rect",
        ],
        issues,
    )

    require_source_tokens(
        "crates/haven_render/src/lib.rs",
        [
            "tile_rect_bottom_center_tiles",
            "PLAYER_VISUAL_FOOT_OFFSET_Y: f32 = 18.0",
            "player_visual_foot_world(player).y",
        ],
        issues,
    )

    # Editor/client terrain parity: editor composition resolves the named tuple
    # origin helper; runtime consumes the exact same exported offset constant.
    for rel in (
        "apps/haven_editor_native/src/app/atlas_render.rs",
        "apps/haven_editor_native/src/app/prepared_canvas_composition.rs",
    ):
        require_source_tokens(rel, ["terrain_tuple_render_origin_tiles"], issues)
    require_source_tokens(
        "crates/haven_game/src/runtime_terrain_base_draw.rs",
        [
            "TERRAIN_TUPLE_RENDER_OFFSET_TILES",
            "TILE_SIZE * TERRAIN_TUPLE_RENDER_OFFSET_TILES",
        ],
        issues,
    )

    runtime_draw_source = (ROOT / "crates/haven_game/src/runtime_draw.rs").read_text(encoding="utf-8")
    if "screen.y + 18.0" not in runtime_draw_source and "PLAYER_VISUAL_FOOT_OFFSET_Y" not in runtime_draw_source:
        fail("runtime player composition no longer matches the certified 18px visual-foot authority", issues)

    # Camera-space guardrails. These adapters may differ by runtime smoothing,
    # but they must retain explicit conversion functions instead of mixing
    # screen/world coordinates inline in structural placement code.
    require_source_tokens(
        "crates/haven_game/src/runtime_scene_navigation.rs",
        ["fn runtime_world_to_screen", "fn world_to_screen", "local_world_to_runtime_world"],
        issues,
    )
    require_source_tokens(
        "apps/haven_editor_native/src/app/canvas_camera.rs",
        ["world_to_screen", "screen_to_world"],
        issues,
    )

    native_main = ROOT / "apps/haven_editor_native/src/main.rs"
    if line_count(native_main) > entrypoint_limit:
        fail("native editor main.rs exceeds entrypoint limit", issues)

    forbidden_old_host_files = [
        ROOT / "crates/haven_editor/src/main.rs",
        ROOT / "crates/haven_editor/src/canvas_camera.rs",
        ROOT / "crates/haven_editor/src/canvas_view.rs",
    ]
    for path in forbidden_old_host_files:
        if path.exists():
            fail(f"native editor host file still exists in headless crate: {path.relative_to(ROOT)}", issues)

    required_native_modules = [
        "apps/haven_editor_native/src/app/mod.rs",
        "apps/haven_editor_native/src/app/input.rs",
        "apps/haven_editor_native/src/app/canvas_controller.rs",
        "apps/haven_editor_native/src/app/draw.rs",
        "apps/haven_editor_native/src/app/scene_authoring.rs",
        "apps/haven_editor_native/src/app/canvas_camera.rs",
        "apps/haven_editor_native/src/app/canvas_view.rs",
        "apps/haven_editor_native/src/app/asset_palette_panel.rs",
        "apps/haven_editor_native/src/app/atlas_render.rs",
    ]
    for rel in required_native_modules:
        if not (ROOT / rel).exists():
            fail(f"missing native editor module {rel}", issues)

    if issues:
        print("Architecture validation FAILED")
        for issue in issues:
            print(f"- {issue}")
        return 1

    print(f"Architecture validation passed ({len(rust_files)} Rust files checked)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
