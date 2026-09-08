#!/usr/bin/env python3
"""Hydrate W77 terrain-transition authoring documents when a clean checkout omits PNG caches.

The W77 workbench manifest and current terrain authorities are source-controlled,
while the generated pixel documents/layer PNGs may be absent in a GitHub ZIP.
This preflight is deliberately separate from validation: it checks the complete
authoring-document package and regenerates the deterministic W77 workbench only
when it is incomplete.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
WORKBENCH = ROOT / "content/editor/terrain_transition_workbench/terrain_transition_workbench_v1.json"
GENERATOR = ROOT / "tools/automation/terrain/Build-TerrainTransitionWorkbenchW77.py"
ATLAS_JSON = ROOT / "assets/generated/worldgen_v0_1/terrain/lpc_mapped_terrain_v7_32.json"
ATLAS_PNG = ROOT / "assets/generated/worldgen_v0_1/terrain/lpc_mapped_terrain_v7_32.png"

EXPECTED_LAYER_IDS = (
    "00_semantic_shape_template",
    "01_reference_a_style",
    "02_reference_b_style",
    "10_owner_fill",
    "20_boundary_shape",
    "30_shading_cleanup",
    "40_alpha_cleanup",
    "90_preview_only",
)


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return {}


def workbench_errors() -> list[str]:
    errors: list[str] = []
    wb = load_json(WORKBENCH)
    docs = list(wb.get("documents") or [])

    if wb.get("schema") != "havenwild.terrain_transition_workbench.w77_v1":
        errors.append("workbench manifest missing or schema mismatch")
        return errors
    if wb.get("materialCount") != 15:
        errors.append(f"materialCount {wb.get('materialCount')} != 15")
    if wb.get("completeDirectPairCount") != 48:
        errors.append(f"completeDirectPairCount {wb.get('completeDirectPairCount')} != 48")
    if wb.get("missingPairCount") != 57 or len(docs) != 57:
        errors.append(f"repair document count {len(docs)} / missingPairCount {wb.get('missingPairCount')} != 57")

    for doc in docs:
        rel = str(doc.get("pixelDocument") or "")
        if not rel:
            errors.append("repair document has no pixelDocument path")
            continue
        png = ROOT / rel
        side = png.with_suffix(".hhasset.json")
        desc = png.with_suffix(".transition.json")
        pkg = png.with_suffix(".hhpixel")

        for required in (png, side, desc):
            if not required.is_file():
                errors.append(f"missing {required.relative_to(ROOT)}")

        md = load_json(side) if side.is_file() else {}
        layers = {str(x.get("id")): x for x in (md.get("layers") or []) if isinstance(x, dict)}
        for layer_id in EXPECTED_LAYER_IDS:
            meta = layers.get(layer_id)
            if not meta:
                errors.append(f"{png.name}: missing layer metadata {layer_id}")
                continue
            image_path = str(meta.get("imagePath") or "")
            if not image_path:
                errors.append(f"{png.name}: layer {layer_id} has no imagePath")
                continue
            # imagePath is relative to the documents directory and begins with
            # <stem>.hhpixel/...
            layer_file = png.parent / image_path
            if not layer_file.is_file():
                errors.append(f"missing {layer_file.relative_to(ROOT)}")

    return errors


def main() -> int:
    errors = workbench_errors()
    if not errors:
        print("W77 transition workbench hydration: READY (57/57 repair documents)")
        return 0

    if not ATLAS_JSON.is_file() or not ATLAS_PNG.is_file():
        print("W77 transition workbench hydration cannot run until the mapped terrain atlas exists.", file=sys.stderr)
        for path in (ATLAS_JSON, ATLAS_PNG):
            if not path.is_file():
                print(f" - missing {path.relative_to(ROOT)}", file=sys.stderr)
        return 1
    if not GENERATOR.is_file():
        print(f"W77 workbench generator is missing: {GENERATOR}", file=sys.stderr)
        return 1

    print(f"W77 transition workbench incomplete ({len(errors)} issue(s)); regenerating deterministic authoring package")
    for error in errors[:8]:
        print(f" - {error}")
    if len(errors) > 8:
        print(f" - ... {len(errors) - 8} additional issue(s)")

    subprocess.run([sys.executable, str(GENERATOR)], cwd=ROOT, check=True)

    remaining = workbench_errors()
    if remaining:
        print("W77 transition workbench regeneration did not close the package:", file=sys.stderr)
        for error in remaining[:20]:
            print(f" - {error}", file=sys.stderr)
        return 1

    print("W77 transition workbench hydration: PASS (57/57 repair documents)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
