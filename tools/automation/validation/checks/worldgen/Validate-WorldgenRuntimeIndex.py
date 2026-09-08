#!/usr/bin/env python3
"""Validate the v0.4 worldgen runtime/editor index.

Run from repo root:
  python scripts/Validate-WorldgenRuntimeIndex.py
"""
from __future__ import annotations
import json, re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[5]
REPORT = ROOT / "logs/worldgen_runtime_index_validation_report.json"
errors: list[str] = []
warnings: list[str] = []
checks: list[dict[str, Any]] = []

def check(name: str, status: str, detail: str = ""):
    checks.append({"name": name, "status": status, "detail": detail})

def load(rel: str):
    path = ROOT / rel
    if not path.exists():
        errors.append(f"Missing required file: {rel}")
        check(f"exists:{rel}", "error")
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        check(f"json:{rel}", "ok")
        return data
    except Exception as exc:  # noqa: BLE001
        errors.append(f"Invalid JSON {rel}: {exc}")
        check(f"json:{rel}", "error", str(exc))
        return None

def version_key(path: Path) -> tuple[int, ...]:
    m = re.search(r"v(\d+(?:_\d+)*)", path.stem)
    return tuple(int(part) for part in m.group(1).split("_")) if m else (0,)

def select_pack() -> Path | None:
    packs = sorted((ROOT / "content/packs").glob("worldgen_home_island_v0_*.json"), key=version_key)
    if not packs:
        errors.append("No worldgen home island pack found")
        return None
    pack = packs[-1]
    check("pack:selected", "ok", str(pack.relative_to(ROOT)))
    return pack

def in_bounds(rect, w, h):
    return isinstance(rect, list) and len(rect) == 4 and all(isinstance(v, int) for v in rect) and rect[0] >= 0 and rect[1] >= 0 and rect[2] >= 0 and rect[3] >= 0 and rect[0] + rect[2] <= w and rect[1] + rect[3] <= h

def main() -> int:
    pack_path = select_pack()
    if not pack_path:
        return finish()
    pack = load(str(pack_path.relative_to(ROOT)))
    if not pack:
        return finish()
    required_keys = ["runtimeIndex", "runtimeLoadOrder", "assetLookup", "objectFootprintRegistry", "transitionRegistry", "navigationGraph", "collisionInteractionOverlay", "cameraCompositionProfile", "validationProfile"]
    for key in required_keys:
        if not pack.get(key):
            errors.append(f"Pack missing v0.4 key: {key}")
        elif not (ROOT / pack[key]).exists():
            errors.append(f"Pack key {key} points to missing file: {pack[key]}")
        else:
            check(f"pack-key:{key}", "ok", pack[key])

    runtime = load(pack.get("runtimeIndex", "")) if pack.get("runtimeIndex") else None
    lookup = load(pack.get("assetLookup", "")) if pack.get("assetLookup") else None
    footprints = load(pack.get("objectFootprintRegistry", "")) if pack.get("objectFootprintRegistry") else None
    transitions = load(pack.get("transitionRegistry", "")) if pack.get("transitionRegistry") else None
    graph = load(pack.get("navigationGraph", "")) if pack.get("navigationGraph") else None
    overlay = load(pack.get("collisionInteractionOverlay", "")) if pack.get("collisionInteractionOverlay") else None
    load_order = load(pack.get("runtimeLoadOrder", "")) if pack.get("runtimeLoadOrder") else None

    if lookup:
        if lookup.get("coverage", {}).get("runtimeTileKinds") != 25:
            errors.append("Expected 25 runtime TileKind lookup entries")
        else:
            check("lookup:runtime tile count", "ok", "25")
        placeholders = lookup.get("coverage", {}).get("scenePlaceholderObjects", 0)
        if placeholders:
            warnings.append(f"{placeholders} scene placeholder object assets still need production atlas art")
        for tid, rec in lookup.get("runtimeTileKindLookup", {}).items():
            if not rec.get("rect"):
                errors.append(f"Runtime tile {tid} has no atlas rect")

    if transitions:
        bad = [r for r in transitions.get("returnValidation", []) if not r.get("ok")]
        if bad:
            errors.append(f"Missing return transitions: {len(bad)}")
        else:
            check("transitions:return validation", "ok", str(len(transitions.get("returnValidation", []))))

    scene_ids = set()
    scene_sizes = {}
    for rel in pack.get("sceneFiles", []):
        scene = load(rel)
        if not scene:
            continue
        sid = scene.get("sceneId")
        scene_ids.add(sid)
        w, h = scene.get("sceneSize", [0, 0])
        scene_sizes[sid] = (w, h)
        terrain = scene.get("layers", {}).get("terrain", [])
        if len(terrain) != h or any(not isinstance(row, list) or len(row) != w for row in terrain):
            errors.append(f"Scene {sid} terrain grid does not match sceneSize")
        for obj in scene.get("objects", []):
            if not in_bounds(obj.get("visualRect"), w, h): errors.append(f"Scene {sid} object {obj.get('id')} visualRect invalid")
            if not in_bounds(obj.get("collisionRect"), w, h): errors.append(f"Scene {sid} object {obj.get('id')} collisionRect invalid")
        for tr in scene.get("transitions", []):
            if tr.get("toScene") not in scene_ids and tr.get("toScene") not in [s.get("sceneId") for s in [load(r) for r in pack.get("sceneFiles", [])] if s]:
                errors.append(f"Scene {sid} transition {tr.get('id')} targets missing scene {tr.get('toScene')}")

    if graph:
        nodes = {n.get("sceneId") for n in graph.get("nodes", [])}
        if scene_ids and nodes != scene_ids:
            errors.append(f"Navigation graph nodes do not match scene files: graph={sorted(nodes)} scenes={sorted(scene_ids)}")
        else:
            check("graph:scene coverage", "ok", str(len(nodes)))

    if overlay:
        overlay_scenes = {s.get("sceneId") for s in overlay.get("scenes", [])}
        if scene_ids and overlay_scenes != scene_ids:
            errors.append("Collision/interaction overlay scene coverage mismatch")
        else:
            check("overlay:scene coverage", "ok", str(len(overlay_scenes)))

    if load_order:
        for phase in load_order.get("phases", []):
            if phase.get("required"):
                missing = [rel for rel in phase.get("files", []) if not (ROOT / rel).exists()]
                if missing:
                    errors.append(f"Load-order phase {phase.get('id')} missing files: {missing}")
        check("load-order:required phases", "ok")

    if runtime:
        summary = runtime.get("summary", {})
        if summary.get("sceneCount") != len(scene_ids):
            errors.append("Runtime index sceneCount does not match scene files")
        else:
            check("runtime:scene count", "ok", str(summary.get("sceneCount")))

    return finish()

def finish() -> int:
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    report = {"status": "pass" if not errors else "fail", "errorCount": len(errors), "warningCount": len(warnings), "errors": errors, "warnings": warnings, "checks": checks}
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if not errors else 1

if __name__ == "__main__":
    raise SystemExit(main())
