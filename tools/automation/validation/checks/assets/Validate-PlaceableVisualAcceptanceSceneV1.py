#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
SWEEP = ROOT / "content/asset_packs/havenwild_objects/placeable_visual_sweep_v1.json"
SCENE = ROOT / "content/worldgen/scenes/world_asset_acceptance/placeable_visual_acceptance_scene_v1.json"
PACK = ROOT / "content/worldgen/packs/worldgen_home_island_test_v0_11.json"
BUILDER = ROOT / "tools/automation/assets/Build-PlaceableVisualAcceptanceSceneV1.py"
MANIFEST = ROOT / "assets/generated/havenwild_lpc_objects_160x192_v2.json"


def need(v: bool, msg: str):
    if not v: raise SystemExit(f"FAIL W43D placeable visual acceptance: {msg}")


def load(p: Path):
    need(p.is_file(), f"missing {p.relative_to(ROOT)}")
    return json.loads(p.read_text(encoding="utf-8-sig"))


def main() -> int:
    sweep, scene, pack, manifest = load(SWEEP), load(SCENE), load(PACK), load(MANIFEST)
    need(BUILDER.is_file(), "builder missing")
    entries = sweep.get("entries", [])
    objects = scene.get("objects", [])
    kinds = [e.get("objectKind") for e in entries]
    scene_kinds = [o.get("objectKind") for o in objects]
    need(len(kinds) == 26 and len(set(kinds)) == 26, "visual sweep does not cover 26 unique ObjectKinds")
    need(scene_kinds == kinds, "acceptance scene does not preserve the complete ObjectKind sweep")
    need(len(set(scene_kinds)) == 26, "acceptance scene duplicates ObjectKinds")
    need(scene.get("role") == "diagnostic_only", "fixture must remain diagnostic only")
    need(scene.get("acceptance", {}).get("productionRegistered") is False, "fixture became production content")

    sweep_by = {e["objectKind"]: e for e in entries}
    manifest_by = {e["id"]: e for e in manifest.get("objects", [])}
    for obj in objects:
        kind = obj["objectKind"]
        src = sweep_by[kind]
        need(obj.get("acceptanceStatus") == src.get("status"), f"{kind} status drift")
        need(obj.get("acceptance", {}).get("runtimeBinding") == src.get("runtimeBinding"), f"{kind} runtime binding drift")
        if src.get("status") in {"REJECTED", "MISSING", "PLACEHOLDER"}:
            need(src.get("runtimeBinding") is None, f"{kind} must fail closed but still has runtime artwork")
            need(obj.get("acceptance", {}).get("failClosedExpected") is True, f"{kind} not marked fail-closed")

    crate = sweep_by["crate"]
    need(crate.get("runtimeBinding") == "crate_stack", "crate compatibility cache id changed unexpectedly")
    cache = manifest_by.get("crate_stack")
    need(cache is not None, "crate runtime cache missing")
    need(cache.get("sourceRect") == [0, 32, 32, 32], "crate is not the exact singular LPC source slice")
    need(cache.get("visualFootprintTiles") == [1, 1], "crate visual footprint is not singular")
    need(cache.get("collisionFootprintTiles") == [1, 1], "crate collision footprint is not singular")

    rel = SCENE.relative_to(ROOT).as_posix()
    need(rel in pack.get("sceneFiles", []), "fixture is not loadable from development test pack")
    need(rel in pack.get("smokeTests", []), "fixture is not in development smoke tests")
    need(pack.get("testWorld", {}).get("placeableVisualAcceptanceSceneId") == "placeable_visual_acceptance", "test pack lacks W43D scene id")
    print("PASS W43D complete placeable visual acceptance board")
    print(f"- {len(objects)} / 26 ObjectKinds have one diagnostic slot")
    print("- rejected/missing/placeholder kinds are represented fail-closed")
    print("- singular crate exact source slice is locked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
