#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
REPORT = ROOT / "content/build/w56f_cliff_editor_runtime_parity_v1.json"


def load(rel: str):
    path = ROOT / rel
    if not path.is_file():
        raise AssertionError(f"missing {rel}")
    return json.loads(path.read_text(encoding="utf-8"))


def text(rel: str) -> str:
    path = ROOT / rel
    if not path.is_file():
        raise AssertionError(f"missing {rel}")
    return path.read_text(encoding="utf-8")


def req(ok: bool, message: str) -> None:
    if not ok:
        raise AssertionError(message)


def main() -> int:
    failures: list[str] = []

    try:
        contract = load("content/terrain/cliff_height_runtime_contract_v1.json")
        scene = load(
            "content/worldgen/scenes/world_asset_acceptance/"
            "cliff_height_w53d_acceptance_scene_v1.json"
        )

        req(
            contract["rules"]["oneStructuralLevelEqualsOneReceiverFaceRow"] is True,
            "level->face-row rule missing",
        )
        req(
            contract["rules"]["uniformAcrossStraightDiagonalTerminal"] is True,
            "uniform face-family height rule missing",
        )
        req(
            contract["caveMouth"]["widthTiles"] == 1
            and contract["caveMouth"]["apertureHeightLevels"] == 2,
            "cave must remain 1 wide x 2 tall",
        )

        levels = scene["layers"]["structuralLevels"]
        req(max(max(row) for row in levels) == 4, "acceptance scene never reaches Level 4")
        for expected, x0, x1 in [(1, 3, 10), (2, 13, 20), (3, 23, 30), (4, 33, 40)]:
            req(
                all(levels[12][x] == expected for x in range(x0, x1 + 1)),
                f"Level {expected} south host strip drifted",
            )
            req(
                all(levels[14][x] == 0 for x in range(x0, x1 + 1)),
                f"Level {expected} receiver is not Level 0",
            )

        acceptance = scene["acceptance"]
        x, y = acceptance["caveHost"]
        threshold_x, threshold_y = acceptance["caveThreshold"]
        req(
            (threshold_x, threshold_y) == (x, y + 1),
            "cave threshold must be one row below host",
        )
        req(
            levels[y][x] == 2 and levels[threshold_y][threshold_x] == 0,
            "cave host/threshold level delta is not 2",
        )
        req(
            acceptance["caveApertureTiles"] == [1, 2],
            "acceptance cave aperture drifted",
        )

        # W40+ normalized the actual visual grammar into haven_render. The old W53D
        # validator still inspected the runtime compatibility re-export and therefore
        # silently stopped validating the implementation once that migration happened.
        # W56F validates the shared owner directly and verifies both consumers use it.
        shared = text("crates/haven_render/src/structural_cliff_visual.rs")
        runtime_compat = text("crates/haven_game/src/runtime_structural_cliff_shapes.rs")
        runtime_draw = text("crates/haven_game/src/runtime_structural_cliff_draw.rs")
        editor_preview = text("apps/haven_editor_native/src/app/structural_cliff_preview.rs")
        editor_draw = text("apps/haven_editor_native/src/app/atlas_render.rs")

        for needle in (
            "pub const fn authored_body_rows",
            "pub const fn uniform_south_face_receiver_rows",
            "pub fn authored_face_segments_for_edge",
            "pub fn authored_south_face_segments",
            "pub fn resolve_cliff_visual_recipe_v1",
        ):
            req(needle in shared, f"shared cliff visual authority missing {needle}")

        req(
            "pub(super) use haven_render::structural_cliff_visual::*;" in runtime_compat,
            "runtime compatibility surface no longer delegates to shared haven_render cliff authority",
        )
        req(
            "resolve_cliff_visual_recipe_v1(center" in runtime_draw,
            "runtime cliff renderer does not resolve the shared visual recipe",
        )
        req(
            "authored_body_rows" in runtime_draw
            and "draw_diagonal_cliff_face" in runtime_draw
            and "draw_cliff_vertical_face" in runtime_draw,
            "runtime straight/diagonal height-aware face paths are incomplete",
        )
        req(
            "extra_authored_body_rows" in runtime_draw and "CAVE_NARROW_SOURCE" in runtime_draw,
            "runtime fixed-width cave projection is not using the shared height grammar",
        )

        req(
            "haven_render::resolve_cliff_visual_recipe_v1" in editor_preview,
            "native editor preview no longer resolves the shared cliff visual recipe",
        )
        req(
            "authored_body_rows" in editor_draw and "south_face_segments" in editor_draw,
            "native editor projection is not height-aware",
        )
        req(
            "SOUTH_WEST_DIAGONAL_FACE" in editor_draw
            and "SOUTH_EAST_DIAGONAL_FACE" in editor_draw
            and "SOUTH_TERMINAL_BODY_ROW" in editor_draw,
            "native editor does not expose the same straight/diagonal/terminal source families",
        )

    except Exception as exc:
        failures.append(str(exc))

    payload = {
        "schema": "havenwild.cliff_editor_runtime_parity.v1",
        "pass": "167Z109W56F",
        "status": "FAIL" if failures else "PASS",
        "authority": "haven_render::structural_cliff_visual",
        "acceptanceScene": "cliff_height_w53d_acceptance",
        "requiredDrops": [1, 2, 3, 4],
        "uniformFamilies": ["straight", "south_west_diagonal", "south_east_diagonal", "terminal"],
        "caveApertureTiles": [1, 2],
        "runtimeConsumer": "crates/haven_game/src/runtime_structural_cliff_draw.rs",
        "editorConsumers": [
            "apps/haven_editor_native/src/app/structural_cliff_preview.rs",
            "apps/haven_editor_native/src/app/atlas_render.rs",
        ],
        "failures": failures,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    if failures:
        print("FAIL W56F cliff/editor/runtime parity", file=sys.stderr)
        for failure in failures:
            print(f" - {failure}", file=sys.stderr)
        return 1

    print("PASS W56F cliff/editor/runtime parity")
    print("- discrete Level 1/2/3/4 drops remain present in the acceptance scene")
    print("- runtime and native editor both resolve the shared haven_render cliff grammar")
    print("- straight/diagonal/terminal families keep one receiver row per structural level")
    print("- ordinary cave aperture remains exactly 1 tile wide x 2 tiles tall")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
