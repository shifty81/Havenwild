#!/usr/bin/env python3
from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[5]
CONTRACT = ROOT / "content/worldgen/v7_tile_lane_isolation_contract_v0_1.json"
FAMILY_AUTHORITY = ROOT / "content/worldgen/terrain_visual_family_authority_v0_1.json"
BUILDER = ROOT / "tools/automation/terrain/Build-LpcMappedTerrainV7.py"
MANIFEST = ROOT / "assets/generated/worldgen_v0_1/terrain/lpc_mapped_terrain_v7_32.json"
ATLAS = ROOT / "assets/generated/worldgen_v0_1/terrain/lpc_mapped_terrain_v7_32.png"


def load(path: Path) -> dict:
    if not path.is_file():
        raise SystemExit(f"V7 isolation: missing {path.relative_to(ROOT)}")
    return json.loads(path.read_text(encoding="utf-8"))


def fail(message: str) -> None:
    raise SystemExit(f"V7 isolation: {message}")


def main() -> int:
    contract = load(CONTRACT)
    family = load(FAMILY_AUTHORITY)
    manifest = load(MANIFEST)
    if not ATLAS.is_file():
        fail("generated V7 atlas PNG is missing")

    allowed_root = contract["allowedSourceRoot"] + "/"
    for rel in contract["allowedSourceFiles"]:
        if not (ROOT / rel).is_file():
            fail(f"required V7 source is missing: {rel}")
        if not rel.startswith(allowed_root):
            fail(f"allowed source escaped V7 root: {rel}")

    builder = BUILDER.read_text(encoding="utf-8")
    forbidden_builder_fragments = [
        'COMMON_BASE_PNG',
        'COMMON_BASE_JSON',
        'Image.open(ROOT / "assets/source/licensed/lpc_revised',
        'Image.open(ROOT / "content/assets/lpc/source/open-game-art-terrain-pack',
    ]
    for fragment in forbidden_builder_fragments:
        if fragment in builder:
            fail(f"builder still imports a non-V7 pixel source: {fragment}")

    if manifest.get("stylePackLane") != "lpc_terrain_v7":
        fail("generated manifest does not identify the pure V7 style-pack lane")
    purity = manifest.get("sourcePurity", {})
    if purity.get("status") != "isolated":
        fail("generated manifest is not marked isolated")
    if manifest.get("source") != "content/assets/lpc/source/lpc-terrains-v7/terrain-map-v7.tsx":
        fail("generated manifest source is not terrain-map-v7.tsx")
    if manifest.get("version") != "0.4.0":
        fail(f"expected isolated V7 manifest version 0.4.0, found {manifest.get('version')}")

    source_sheets = {entry.get("sourceSheet", "terrain-map-v7.png") for entry in manifest.get("entries", [])}
    illegal_sheets = source_sheets - {"terrain-map-v7.png", "terrain-v7.png"}
    if illegal_sheets:
        fail(f"generated V7 atlas includes non-V7 source sheets: {sorted(illegal_sheets)}")
    if not manifest.get("entries"):
        fail("generated V7 manifest has no entries")

    # Pixel-level certification: every atlas cell must exactly equal its declared
    # crop from terrain-map-v7.png or terrain-v7.png. This catches disguised
    # substitutions even when paths and metadata look clean.
    map_png = ROOT / "content/assets/lpc/source/lpc-terrains-v7/terrain-map-v7.png"
    map_tsx = ROOT / "content/assets/lpc/source/lpc-terrains-v7/terrain-map-v7.tsx"
    variant_png = ROOT / "content/assets/lpc/source/lpc-terrains-v7/terrain-v7.png"
    variant_tsx = ROOT / "content/assets/lpc/source/lpc-terrains-v7/terrain-v7.tsx"
    map_columns = int(ET.parse(map_tsx).getroot().attrib["columns"])
    variant_columns = int(ET.parse(variant_tsx).getroot().attrib["columns"])
    with Image.open(ATLAS).convert("RGBA") as atlas_image, \
         Image.open(map_png).convert("RGBA") as map_image, \
         Image.open(variant_png).convert("RGBA") as variant_image:
        for entry in manifest["entries"]:
            sheet = entry.get("sourceSheet", "terrain-map-v7.png")
            source_id = int(entry.get("sourceTileId", entry["tileId"]))
            source_image = variant_image if sheet == "terrain-v7.png" else map_image
            columns = variant_columns if sheet == "terrain-v7.png" else map_columns
            sx = (source_id % columns) * 32
            sy = (source_id // columns) * 32
            expected = source_image.crop((sx, sy, sx + 32, sy + 32))
            ax, ay, aw, ah = entry["rect"]
            actual = atlas_image.crop((ax, ay, ax + aw, ay + ah))
            if actual.tobytes() != expected.tobytes():
                fail(
                    f"atlas entry {entry['tileId']} does not match declared {sheet} "
                    f"source tile {source_id}"
                )

    families = family.get("families", [])
    pure = next((item for item in families if item.get("id") == contract["styleFamily"]), None)
    if pure is None:
        fail("pure V7 style family is missing")
    if pure.get("stylePackLane") != "lpc_terrain_v7":
        fail("pure V7 family has the wrong lane id")
    if pure.get("crossFamilyFallbackAllowed") is not False:
        fail("pure V7 family still allows cross-family fallback")

    forbidden_tokens = tuple(token.lower() for token in contract["forbiddenSourceTokens"])
    for item in families:
        is_v7 = item.get("stylePackLane") == "lpc_terrain_v7" or "terrain_v7" in item.get("id", "")
        if not is_v7:
            continue
        text = json.dumps(item, sort_keys=True).lower()
        hits = [token for token in forbidden_tokens if token in text]
        if hits:
            fail(f"V7 family {item.get('id')} references forbidden sources: {hits}")
        sources = item.get("sources", [item.get("source")] if item.get("source") else [])
        for source in sources:
            if not source.startswith(allowed_root):
                fail(f"V7 family {item.get('id')} escaped V7 source root: {source}")

    if any(item.get("id") == "terrain_v7_highland_v1" for item in families):
        fail("ElizaWy cliff_summer is still mislabeled as a V7 highland family")
    legacy = next((item for item in families if item.get("id") == "legacy_mixed_mainland_v1"), None)
    if legacy is None or legacy.get("stylePackLane") != "legacy_mixed":
        fail("current mixed runtime is not quarantined as legacy_mixed")
    if family.get("activeOpenWorldFamily") != "lpc_terrain_v7_island_v1":
        fail("active runtime is not the source-pure V7 certification lane")

    print(
        "V7 tile lane isolation validated: "
        f"{len(manifest['entries'])} entries, source sheets {sorted(source_sheets)}, "
        "no ElizaWy/common-base pixel imports"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
