#!/usr/bin/env python3
"""Validate generated worldgen assets without third-party dependencies.

Run from the repository root:
  python scripts/Validate-WorldgenAssets.py

v0.3 behavior: automatically selects the newest content/worldgen/packs/worldgen_home_island_v0_*.json pack.
"""
from __future__ import annotations

import json
import re
import struct
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[5]
REPORT_PATH = ROOT / "logs/worldgen_asset_validation_report.json"
CORE_PATH = ROOT / "crates/haven_core/src/lib.rs"

errors: list[str] = []
warnings: list[str] = []
checks: list[dict[str, Any]] = []

NON_WALKABLE = {"Wall", "Cliff", "MountainRock", "CaveWall", "Water", "ShallowWater", "DeepWater"}
KNOWN_EDGE_TYPES = {"forest", "coast", "mountain", "city", "field", "interior_black_void", "cave_darkness", "cliff"}


def add_check(name: str, status: str, detail: str = "") -> None:
    checks.append({"name": name, "status": status, "detail": detail})


def version_key(path: Path) -> tuple[int, ...]:
    m = re.search(r"v(\d+(?:_\d+)*)", path.stem)
    if not m:
        return (0,)
    return tuple(int(part) for part in m.group(1).split("_"))


def select_pack() -> Path | None:
    packs = sorted((ROOT / "content/packs").glob("worldgen_home_island_v0_*.json"), key=version_key)
    if not packs:
        errors.append("No worldgen_home_island_v0_*.json content pack found")
        return None
    path = packs[-1]
    add_check("pack:selected", "ok", str(path.relative_to(ROOT)))
    return path


def load_json(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        add_check(f"json:{path.relative_to(ROOT)}", "ok")
        return data
    except Exception as exc:  # noqa: BLE001
        errors.append(f"Invalid JSON {path.relative_to(ROOT)}: {exc}")
        add_check(f"json:{path.relative_to(ROOT)}", "error", str(exc))
        return None


def png_size(path: Path) -> tuple[int, int] | None:
    try:
        with path.open("rb") as f:
            header = f.read(24)
        if len(header) < 24 or header[:8] != b"\x89PNG\r\n\x1a\n":
            raise ValueError("not a PNG file")
        width, height = struct.unpack(">II", header[16:24])
        return width, height
    except Exception as exc:  # noqa: BLE001
        errors.append(f"Invalid PNG {path.relative_to(ROOT)}: {exc}")
        add_check(f"png:{path.relative_to(ROOT)}", "error", str(exc))
        return None


def image_for_json(json_path: Path) -> Path:
    return json_path.with_suffix(".png")


def validate_rects(json_path: Path, data: Any) -> None:
    if not isinstance(data, dict):
        return
    image_path = image_for_json(json_path)
    if not image_path.exists():
        if data.get("kind") in {"tilesheet", "autotile_sheet", "animated_tilesheet", "object_atlas", "border_tilesheet"}:
            errors.append(f"Missing PNG for atlas manifest: {image_path.relative_to(ROOT)}")
        return
    size = png_size(image_path)
    if size is None:
        return
    width, height = size
    add_check(f"png:{image_path.relative_to(ROOT)}", "ok", f"{width}x{height}")

    rect_sources: list[dict[str, Any]] = []
    keys = ("objects", "borders", "variants") if data.get("kind") == "animated_tilesheet" else ("tiles", "objects", "borders", "variants")
    for key in keys:
        value = data.get(key)
        if isinstance(value, list):
            rect_sources.extend([item for item in value if isinstance(item, dict)])
    if data.get("kind") == "animated_tilesheet":
        for tile in data.get("tiles", []):
            for frame in tile.get("frames", []):
                if isinstance(frame, dict):
                    rect_sources.append(frame)

    for item in rect_sources:
        rect = item.get("rect")
        item_id = item.get("id", f"frame_{item.get('frame', '?')}")
        if not isinstance(rect, list) or len(rect) != 4:
            warnings.append(f"{json_path.relative_to(ROOT)} item {item_id} has no rect")
            continue
        x, y, w, h = rect
        if x < 0 or y < 0 or w <= 0 or h <= 0 or x + w > width or y + h > height:
            errors.append(f"{json_path.relative_to(ROOT)} item {item_id} rect {rect} exceeds image {width}x{height}")


def parse_rust_tile_kinds() -> set[str]:
    if not CORE_PATH.exists():
        warnings.append("Could not find crates/haven_core/src/lib.rs to validate TileKind bindings")
        return set()
    text = CORE_PATH.read_text(encoding="utf-8")
    match = re.search(r"pub enum TileKind \{(?P<body>.*?)\n\}", text, re.S)
    if not match:
        warnings.append("Could not parse TileKind enum")
        return set()
    names = set(re.findall(r"^\s*([A-Z][A-Za-z0-9_]*),", match.group("body"), re.M))
    add_check("rust:TileKind enum parsed", "ok", f"{len(names)} variants")
    return names


def in_bounds(rect: list[Any], width: int, height: int) -> bool:
    if not isinstance(rect, list) or len(rect) != 4:
        return False
    x, y, w, h = rect
    return all(isinstance(v, int) for v in rect) and x >= 0 and y >= 0 and w > 0 and h > 0 and x + w <= width and y + h <= height


def validate_scene(path: Path, rust_tiles: set[str]) -> dict[str, Any] | None:
    scene = load_json(path)
    if not isinstance(scene, dict):
        return None
    sid = scene.get("sceneId", path.stem)
    size = scene.get("sceneSize")
    layers = scene.get("layers", {})
    terrain = layers.get("terrain") if isinstance(layers, dict) else None
    if not (isinstance(size, list) and len(size) == 2 and isinstance(terrain, list)):
        errors.append(f"Scene {path.relative_to(ROOT)} missing sceneSize or layers.terrain")
        return scene
    width, height = size
    if len(terrain) != height:
        errors.append(f"Scene {sid} height mismatch: expected {height}, got {len(terrain)}")
    for y, row in enumerate(terrain):
        if not isinstance(row, list) or len(row) != width:
            errors.append(f"Scene {sid} row {y} width mismatch: expected {width}, got {len(row) if isinstance(row, list) else 'non-list'}")
            continue
        unknown = [tile for tile in row if rust_tiles and tile not in rust_tiles]
        if unknown:
            errors.append(f"Scene {sid} row {y} references unknown TileKind(s): {', '.join(sorted(set(unknown)))}")
    zones = layers.get("zones") if isinstance(layers, dict) else None
    if isinstance(zones, list):
        if len(zones) != height:
            errors.append(f"Scene {sid} zones height mismatch")
        for y, row in enumerate(zones):
            if not isinstance(row, list) or len(row) != width:
                errors.append(f"Scene {sid} zones row {y} width mismatch")
    for obj in scene.get("objects", []):
        oid = obj.get("id", "<unnamed>")
        if not in_bounds(obj.get("visualRect"), width, height):
            errors.append(f"Scene {sid} object {oid} visualRect invalid/out of bounds: {obj.get('visualRect')}")
        if not in_bounds(obj.get("collisionRect"), width, height):
            errors.append(f"Scene {sid} object {oid} collisionRect invalid/out of bounds: {obj.get('collisionRect')}")
        for interaction in obj.get("interactions", []):
            if "rect" in interaction and not in_bounds(interaction.get("rect"), width, height):
                errors.append(f"Scene {sid} object {oid} interaction rect invalid/out of bounds: {interaction.get('rect')}")
    for tr in scene.get("transitions", []):
        if not in_bounds(tr.get("rect"), width, height):
            errors.append(f"Scene {sid} transition {tr.get('id')} rect invalid/out of bounds: {tr.get('rect')}")
        spawn = tr.get("toSpawn")
        if not isinstance(spawn, list) or len(spawn) != 2:
            errors.append(f"Scene {sid} transition {tr.get('id')} missing toSpawn")
    for spawn in scene.get("spawns", []):
        tile = spawn.get("tile")
        if not isinstance(tile, list) or len(tile) != 2 or not (0 <= tile[0] < width and 0 <= tile[1] < height):
            errors.append(f"Scene {sid} spawn {spawn.get('id')} is outside scene: {tile}")
        elif terrain[tile[1]][tile[0]] in NON_WALKABLE:
            warnings.append(f"Scene {sid} spawn {spawn.get('id')} is on non-walkable tile {terrain[tile[1]][tile[0]]}")
    edge = scene.get("edgePolicy", {}).get("resolvedBorders", {}) if isinstance(scene.get("edgePolicy"), dict) else {}
    for direction in ("north", "south", "east", "west"):
        value = edge.get(direction)
        if not value:
            errors.append(f"Scene {sid} edge {direction} is unresolved")
        elif value == "void":
            errors.append(f"Scene {sid} edge {direction} resolves to raw void")
    add_check(f"scene:{sid}", "ok", f"{width}x{height} objects={len(scene.get('objects', []))} transitions={len(scene.get('transitions', []))}")
    return scene


def validate_return_transitions(scenes: dict[str, dict[str, Any]]) -> None:
    transition_ids = {sid: {tr.get("id") for tr in scene.get("transitions", [])} for sid, scene in scenes.items()}
    for sid, scene in scenes.items():
        for tr in scene.get("transitions", []):
            if tr.get("returnRequired"):
                target = tr.get("toScene")
                return_id = tr.get("returnTransitionId")
                if target not in scenes:
                    errors.append(f"Scene {sid} transition {tr.get('id')} targets missing scene {target}")
                elif return_id not in transition_ids.get(target, set()):
                    errors.append(f"Scene {sid} transition {tr.get('id')} requires return {return_id} in {target}, but it was not found")
    add_check("scene:return transitions", "ok")


def main() -> int:
    pack_path = select_pack()
    if not pack_path:
        return finish()
    pack = load_json(pack_path)
    if not pack:
        return finish()

    manifest_path = ROOT / pack["masterManifest"]
    manifest = load_json(manifest_path)
    if manifest:
        for rel in manifest.get("atlases", []):
            path = manifest_path.parent / rel
            if not path.exists():
                errors.append(f"Missing atlas manifest listed by master manifest: {path.relative_to(ROOT)}")
                continue
            data = load_json(path)
            validate_rects(path, data)
        for rel in manifest.get("biomes", []):
            path = manifest_path.parent / rel
            if path.exists():
                load_json(path)
            else:
                errors.append(f"Missing biome manifest: {path.relative_to(ROOT)}")
        for rel in manifest.get("tests", []):
            path = manifest_path.parent / rel
            if path.exists():
                load_json(path)
            else:
                errors.append(f"Missing smoke test: {path.relative_to(ROOT)}")

    for key in ("worldSurface", "placementRules", "autotileRules", "editorLayerRegistry", "biomePalette", "edgeBorderResolution", "islandTemplates", "runtimeIndex", "runtimeLoadOrder", "assetLookup", "objectFootprintRegistry", "transitionRegistry", "navigationGraph", "collisionInteractionOverlay", "cameraCompositionProfile", "validationProfile"):
        rel = pack.get(key)
        if rel:
            path = ROOT / rel
            if path.exists():
                load_json(path)
            else:
                errors.append(f"Missing {key}: {rel}")

    for rel in pack.get("sceneContracts", []):
        path = ROOT / rel
        if path.exists():
            load_json(path)
        else:
            errors.append(f"Missing scene contract: {path.relative_to(ROOT)}")

    bindings_path = ROOT / pack["runtimeBindings"]
    bindings = load_json(bindings_path) if bindings_path.exists() else None
    if not bindings_path.exists():
        errors.append(f"Missing runtime bindings: {bindings_path.relative_to(ROOT)}")
    rust_tiles = parse_rust_tile_kinds()
    if bindings and rust_tiles:
        mapped = {b.get("tileKind") for b in bindings.get("bindings", []) if isinstance(b, dict)}
        missing = sorted(rust_tiles - mapped)
        extra = sorted(mapped - rust_tiles)
        if missing:
            errors.append(f"Missing runtime bindings for TileKind variants: {', '.join(missing)}")
        if extra:
            errors.append(f"Runtime bindings reference unknown TileKind variants: {', '.join(extra)}")
        add_check("runtime:TileKind bindings", "ok" if not missing and not extra else "error", f"mapped={len(mapped)}")

    scenes: dict[str, dict[str, Any]] = {}
    for rel in pack.get("sceneFiles", []):
        path = ROOT / rel
        if not path.exists():
            errors.append(f"Missing scene file: {rel}")
            continue
        scene = validate_scene(path, rust_tiles)
        if scene:
            scenes[scene.get("sceneId", path.stem)] = scene
    if scenes:
        validate_return_transitions(scenes)

    for rel in pack.get("previews", []):
        path = ROOT / rel
        if not path.exists():
            errors.append(f"Missing preview: {rel}")
        elif png_size(path):
            add_check(f"preview:{path.relative_to(ROOT)}", "ok")

    smoke_paths = [ROOT / rel for rel in pack.get("smokeTests", [])]
    for path in smoke_paths:
        if not path.exists() or str(path).endswith("_scene_v0_3.json"):
            continue
        smoke = load_json(path)
        if isinstance(smoke, dict):
            size = smoke.get("sceneSize")
            tiles = smoke.get("tiles")
            if isinstance(size, list) and len(size) == 2 and isinstance(tiles, list):
                expected_w, expected_h = size
                if len(tiles) != expected_h:
                    errors.append(f"Smoke test {path.relative_to(ROOT)} height mismatch: expected {expected_h}, got {len(tiles)}")
                for idx, row in enumerate(tiles):
                    if len(row) != expected_w:
                        errors.append(f"Smoke test {path.relative_to(ROOT)} row {idx} width mismatch: expected {expected_w}, got {len(row)}")
                add_check(f"smoke:{path.relative_to(ROOT)} scene size", "ok", f"{expected_w}x{expected_h}")

    return finish()


def finish() -> int:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "status": "pass" if not errors else "fail",
        "errorCount": len(errors),
        "warningCount": len(warnings),
        "errors": errors,
        "warnings": warnings,
        "checks": checks,
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
