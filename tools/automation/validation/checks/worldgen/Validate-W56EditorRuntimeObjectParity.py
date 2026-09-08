#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
REPORT = ROOT / "content/build/w56g_editor_runtime_object_parity_v1.json"


def read(rel: str) -> str:
    path = ROOT / rel
    if not path.is_file():
        raise AssertionError(f"missing {rel}")
    return path.read_text(encoding="utf-8")


def load(rel: str):
    return json.loads(read(rel))


def req(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    failures: list[str] = []
    tree_contract = None

    try:
        loader = read("crates/haven_core/src/worldgen_loader.rs")
        runtime = read("crates/haven_game/src/runtime_object_draw.rs")
        editor = read("apps/haven_editor_native/src/app/atlas_render.rs")
        shared = read("crates/haven_render/src/lib.rs")
        catalog = load("content/asset_packs/havenwild_objects/published_world_assets_v1.json")

        req(
            "StablePlaceableAssetRef::from_scene_asset_alias" in loader
            and "place_pack_defined_object(" in loader,
            "authored worldgen loader no longer preserves exact scene asset identity",
        )

        exact_ref_lookup = ".object_asset_ref(object.id)"
        req(
            exact_ref_lookup in runtime,
            "runtime object draw no longer resolves exact stable asset refs",
        )
        req(
            exact_ref_lookup in editor,
            "native editor draw no longer resolves exact stable asset refs",
        )
        req(
            "resolve_persistent_ref(asset_ref)" in runtime,
            "runtime exact asset refs do not pass through published persistent resolution",
        )
        req(
            "resolve_persistent_ref(asset_ref)" in editor,
            "editor exact asset refs do not pass through published persistent resolution",
        )

        req(
            "use haven_render::object_foot_world;" in runtime
            and "let foot = object_foot_world(object)" in runtime,
            "runtime placeable sprites no longer use the shared physical foot/root",
        )
        req(
            "let foot = object_foot_tiles(*object);" in editor,
            "native editor placeable sprites no longer use the shared physical foot/root",
        )
        req(
            "pub fn object_foot_world" in shared and "pub fn object_foot_tiles" in shared,
            "shared placeable foot/root authority is missing from haven_render",
        )

        entries = {entry["id"]: entry for entry in catalog["entries"]}
        tree = entries.get("tree_oak_mature_01")
        req(tree is not None, "published oak tree acceptance asset is missing")
        footprint = tree["footprint"]
        visual = tree["visual"]
        req(
            footprint["visual_offset"] == [-1, -3]
            and footprint["visual_size"] == [3, 4]
            and footprint["collision_size"] == [1, 1],
            "published mature-tree visual/collision footprint drifted",
        )
        req(
            visual["foot_anchor"] == [80, 192]
            and visual["frames"][0]["source_rect"][2:] == [160, 192],
            "published mature-tree bottom-center foot anchor drifted",
        )
        tree_contract = {
            "assetId": tree["id"],
            "visualTiles": footprint["visual_size"],
            "collisionTiles": footprint["collision_size"],
            "visualOffsetTiles": footprint["visual_offset"],
            "framePixels": visual["frames"][0]["source_rect"][2:],
            "footAnchorPixels": visual["foot_anchor"],
        }
    except Exception as exc:
        failures.append(str(exc))

    payload = {
        "schema": "havenwild.editor_runtime_object_parity.v1",
        "pass": "167Z109W56G",
        "status": "FAIL" if failures else "PASS",
        "assetIdentityAuthority": "StablePlaceableAssetRef -> PublishedWorldAssetRegistry",
        "anchorAuthority": "haven_render::object_foot_world/object_foot_tiles",
        "treeAcceptanceContract": tree_contract,
        "runtimeConsumer": "crates/haven_game/src/runtime_object_draw.rs",
        "editorConsumer": "apps/haven_editor_native/src/app/atlas_render.rs",
        "failures": failures,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    if failures:
        print("FAIL W56G editor/runtime object parity", file=sys.stderr)
        for failure in failures:
            print(f" - {failure}", file=sys.stderr)
        return 1

    print("PASS W56G editor/runtime object parity")
    print("- authored exact asset identity survives worldgen loading into both renderer paths")
    print("- runtime and native editor use the same collision-rooted physical foot anchor")
    print("- mature tree remains 3x4 visual, 1x1 collision, bottom-center [80,192] in a 160x192 frame")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
