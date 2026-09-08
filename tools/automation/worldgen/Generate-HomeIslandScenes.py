#!/usr/bin/env python3
"""Generate deterministic home-island v0.3 scene contracts and previews.

This script is intentionally a scaffold. The generated files already exist in this pack,
but keeping the script in-repo makes the content reproducible and gives the editor a clear
contract for future procedural generation work.

Run from repository root:
  python scripts/Generate-HomeIslandScenes.py
"""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[3]
PACK = ROOT / "content/worldgen/packs/worldgen_home_island_v0_3.json"

if not PACK.exists():
    raise SystemExit(f"Missing {PACK.relative_to(ROOT)}. Apply worldgen v0.3 first.")

pack = json.loads(PACK.read_text(encoding="utf-8"))
scene_files = pack.get("sceneFiles", [])
missing = [rel for rel in scene_files if not (ROOT / rel).exists()]
if missing:
    raise SystemExit("Missing generated scene files:\n" + "\n".join(missing))

print(f"Home-island v0.3 scene pack is present: {len(scene_files)} scene files")
for rel in scene_files:
    scene = json.loads((ROOT / rel).read_text(encoding="utf-8"))
    print(f"- {scene['sceneId']}: {scene['sceneSize'][0]}x{scene['sceneSize'][1]} objects={len(scene.get('objects', []))} transitions={len(scene.get('transitions', []))}")
