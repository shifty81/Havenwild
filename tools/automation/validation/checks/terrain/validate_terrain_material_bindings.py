#!/usr/bin/env python3
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
BINDINGS = ROOT / "content/assets/terrain_material_bindings_v0_2.json"
TSX = ROOT / "content/assets/lpc/source/lpc-terrains-v7/terrain-v7.tsx"


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    data = json.loads(BINDINGS.read_text(encoding="utf-8"))
    if data.get("schema") != "havenwild.terrain_material_bindings.v0_2":
        fail("unexpected binding schema")
    terrain_names = {
        node.attrib["name"]
        for node in ET.parse(TSX).getroot().findall("./terraintypes/terrain")
    }
    seen = set()
    for binding in data.get("bindings", []):
        tile = binding.get("tileKind")
        if not tile or tile in seen:
            fail(f"missing or duplicate tileKind: {tile!r}")
        seen.add(tile)
        mode = binding.get("renderMode")
        material = binding.get("material")
        overlay = binding.get("overlay")
        fallback = binding.get("tupleFallbackMaterial")
        if mode in {"corner_tuple", "generated_band"}:
            if material not in terrain_names:
                fail(f"{tile}: unknown terrain-v7 material {material!r}")
        if mode in {"generated_band", "overlay"} and not overlay:
            fail(f"{tile}: {mode} requires overlay recipe")
        if mode in {"overlay", "structure"} and material is not None:
            fail(f"{tile}: {mode} must not claim an ordinary canonical material")
        if fallback is not None and fallback not in terrain_names:
            fail(f"{tile}: unknown tuple compatibility fallback {fallback!r}")

    pairs = [("PebbleShore", "StonePath"), ("MountainPath", "Road")]
    by_tile = {item["tileKind"]: item for item in data["bindings"]}
    for left, right in pairs:
        if by_tile[left].get("material") == by_tile[right].get("material"):
            fail(f"semantic collision remains: {left} and {right}")

    print(f"OK: {len(seen)} terrain bindings validated against {len(terrain_names)} terrain-v7 materials")


if __name__ == "__main__":
    main()
