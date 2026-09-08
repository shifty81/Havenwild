"""Lock world-paint single-cell brush and owner-base overlay rendering."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[5]
def text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def require(path: str, needles: list[str]) -> str:
    payload = text(path)
    missing = [needle for needle in needles if needle not in payload]
    if missing:
        raise AssertionError(f"{path} missing required world-paint guard(s): {missing}")
    return payload


def reject(path: str, needles: list[str]) -> None:
    payload = text(path)
    present = [needle for needle in needles if needle in payload]
    if present:
        raise AssertionError(f"{path} contains obsolete world-paint behavior: {present}")


def main() -> int:
    require(
        "crates/haven_world/src/world_paint.rs",
        [
            "pub fn world_paint_cells_in_brush",
            "if radius == 1",
            "return vec![[center_x, center_y]];",
            "radius_one_world_paint_targets_only_the_clicked_cell",
        ],
    )
    require(
        "crates/haven_world/src/world_paint_material_state.rs",
        [
            "world_paint_cells_in_brush",
            "radius_one_material_state_targets_only_center_cell",
        ],
    )
    runtime_pass = require(
        "crates/haven_game/src/runtime_terrain_pass.rs",
        [
            "Project paint is an overlay pass",
            "self.draw_tile_base(map, tile, x, y, px, py);",
            "self.draw_world_paint_atlas_layers_if_bound(scene_id, x, y, px, py);",
        ],
    )
    base_pass = runtime_pass.split("// Project paint is an overlay pass", 1)[0]
    if "has_drawable_layers(scene_id, x, y)" in base_pass:
        raise AssertionError("base terrain pass still skips atlas-bound world-paint cells")
    reject(
        "crates/haven_game/src/runtime_draw.rs",
        ["draw_world_paint_atlas_layers_if_bound before fallback terrain"],
    )
    print("V125 OK: world-paint radius 1 is single-cell and atlas bindings overlay owner base")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
