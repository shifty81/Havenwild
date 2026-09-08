#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[5]
LOCK = ROOT / "content/assets/intake/lpc_source_lock_v0_1.json"
CONTRACT = ROOT / "content/assets/intake/lpc_expandable_terrain_families_v0_1.json"
MANIFEST = ROOT / "assets/generated/worldgen_v0_1/terrain/lpc_expandable_ponds_32.json"
PREVIEW = ROOT / "docs/assets/previews/havenwild_lpc_expandable_ponds_pass87.png"
PROMOTER = ROOT / "tools/automation/terrain/Promote-LpcExpandablePondsV87.py"


def fail(message: str, issues: list[str]) -> None:
    issues.append(message)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    issues: list[str] = []
    for path in [LOCK, CONTRACT, MANIFEST, PREVIEW, PROMOTER]:
        if not path.exists():
            fail(f"missing {path.relative_to(ROOT)}", issues)
    if issues:
        for issue in issues:
            print(f"- {issue}")
        return 1

    lock = json.loads(LOCK.read_text(encoding="utf-8"))
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if lock.get("schema") != "havenwild.lpc_source_lock.v0_1":
        fail("unexpected LPC source-lock schema", issues)
    if contract.get("schema") != "havenwild.lpc_expandable_terrain_families.v0_1":
        fail("unexpected expandable-family schema", issues)
    if manifest.get("schema") != "havenwild.stamp_manifest.v0_2":
        fail("unexpected generated pond stamp schema", issues)

    locked_files = lock.get("lockedFiles", [])
    terrain_lock = next(
        (entry for entry in locked_files if entry.get("projectPath") == contract.get("source")),
        None,
    )
    if terrain_lock is None:
        fail("terrain_summer.png is not pinned by the LPC source lock", issues)
    else:
        source = ROOT / terrain_lock["projectPath"]
        if not source.exists():
            fail("locked terrain source is missing", issues)
        else:
            if sha256(source) != terrain_lock.get("sha256"):
                fail("locked terrain source hash changed", issues)
            image = Image.open(source)
            if image.size != (terrain_lock.get("width"), terrain_lock.get("height")):
                fail(f"locked terrain dimensions changed: {image.size}", issues)

    families = contract.get("families", [])
    if len(families) != 14:
        fail(f"expected 14 mapped LPC expandable families, found {len(families)}", issues)
    ids = [family.get("id") for family in families]
    if len(ids) != len(set(ids)):
        fail("expandable-family IDs are not unique", issues)
    grid = contract.get("grid")
    for family in families:
        family_id = family.get("id", "<missing>")
        for key, expected in [("outerBlock", (3, 3)), ("innerCornerBlock", (2, 2))]:
            value = family.get(key)
            if not isinstance(value, list) or len(value) != 4:
                fail(f"{family_id} {key} is not a four-value block", issues)
                continue
            x, y, width, height = value
            if (width, height) != expected:
                fail(f"{family_id} {key} must be {expected[0]}x{expected[1]}", issues)
            if x < 0 or y < 0 or x + width > grid[0] or y + height > grid[1]:
                fail(f"{family_id} {key} is outside the source grid", issues)
        fill = family.get("baseFillCell")
        if not isinstance(fill, list) or len(fill) != 2:
            fail(f"{family_id} has no baseFillCell", issues)
        elif not (0 <= fill[0] < grid[0] and 0 <= fill[1] < grid[1]):
            fail(f"{family_id} baseFillCell is outside the source grid", issues)
        if family.get("minimumSize") != [3, 3]:
            fail(f"{family_id} minimum size must remain 3x3", issues)
        if family.get("supportsRectangle") is not True:
            fail(f"{family_id} is not rectangle-expandable", issues)
        if family.get("supportsFreeform") is not True:
            fail(f"{family_id} does not preserve inner-corner/freeform intent", issues)

    objects = manifest.get("objects", [])
    exposed_ids = {family["id"] for family in families if family.get("exposeAsStamp")}
    object_ids = {entry.get("id") for entry in objects}
    if object_ids != exposed_ids:
        fail("generated stamp IDs do not match exposed family IDs", issues)
    for entry in objects:
        expandable = entry.get("expandable")
        if not isinstance(expandable, dict):
            fail(f"{entry.get('id')} has no expandable stamp definition", issues)
            continue
        if expandable.get("outerBlock", [None, None, None, None])[2:] != [3, 3]:
            fail(f"{entry.get('id')} generated outer block is not 3x3", issues)
        if expandable.get("innerCornerBlock", [None, None, None, None])[2:] != [2, 2]:
            fail(f"{entry.get('id')} generated inner block is not 2x2", issues)
        if "baseFillCell" not in expandable:
            fail(f"{entry.get('id')} generated definition has no base fill", issues)
        if entry.get("visualFootprint") != [3, 3]:
            fail(f"{entry.get('id')} default footprint is not 3x3", issues)

    preview = Image.open(PREVIEW).convert("RGBA")
    if preview.width < 800 or preview.height < 1200:
        fail(f"expandable pond preview is unexpectedly small: {preview.size}", issues)
    if preview.getbbox() is None:
        fail("expandable pond preview is empty", issues)

    registry = (ROOT / "crates/haven_assets/src/stamp_registry.rs").read_text(encoding="utf-8")
    editor_render = (ROOT / "apps/haven_editor_native/src/app/atlas_render.rs").read_text(
        encoding="utf-8"
    )
    runtime_render = (ROOT / "crates/haven_game/src/runtime_stamp_draw.rs").read_text(
        encoding="utf-8"
    )
    editor_panel = (ROOT / "apps/haven_editor_native/src/app/object_inspector.rs").read_text(
        encoding="utf-8"
    )
    stamp_editor = (ROOT / "crates/haven_editor/src/stamp_inspector.rs").read_text(
        encoding="utf-8"
    )
    required_registry_tokens = [
        "ExpandableStampDefinition",
        "base_fill_tile",
        "inner_corner_tiles",
        "source_rect_for_rect_cell",
        "lpc_expandable_ponds_32.json",
    ]
    for token in required_registry_tokens:
        if token not in registry:
            fail(f"stamp registry missing {token}", issues)
    for path_name, text in [
        ("native atlas renderer", editor_render),
        ("runtime stamp renderer", runtime_render),
    ]:
        for token in ["base_fill_tile", "source_rect_for_rect_cell"]:
            if token not in text:
                fail(f"{path_name} missing {token}", issues)
    for token in ["Resize Pond", "resize_selected_stamp", "Reset expandable pond size"]:
        if token not in editor_panel:
            fail(f"native inspector missing {token}", issues)
    for token in ["update_scene_stamp", "RemoveStamp", "InsertStamp"]:
        if token not in stamp_editor:
            fail(f"headless stamp inspector missing {token}", issues)

    build_ps1 = (ROOT / "tools/build/Build.ps1").read_text(encoding="utf-8")
    build_sh = (ROOT / "tools/build/Build.sh").read_text(encoding="utf-8")
    for build_name, text in [("tools/build/Build.ps1", build_ps1), ("tools/build/Build.sh", build_sh)]:
        if "Promote-LpcExpandablePondsV87.py" not in text:
            fail(f"{build_name} does not regenerate expandable ponds", issues)

    deterministic_before = MANIFEST.read_bytes(), PREVIEW.read_bytes()
    completed = subprocess.run([sys.executable, str(PROMOTER)], cwd=ROOT, capture_output=True, text=True)
    if completed.returncode:
        fail(f"pond promoter failed: {completed.stderr or completed.stdout}", issues)
    deterministic_after = MANIFEST.read_bytes(), PREVIEW.read_bytes()
    if deterministic_before != deterministic_after:
        fail("pond promotion is not deterministic", issues)

    if issues:
        print("LPC expandable pond family validation FAILED")
        for issue in issues:
            print(f"- {issue}")
        return 1
    print(
        f"LPC expandable pond family validation passed "
        f"({len(families)} mapped families, {len(objects)} editor/runtime stamps)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
