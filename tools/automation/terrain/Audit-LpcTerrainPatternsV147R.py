#!/usr/bin/env python3
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
MAPPED = ROOT / "assets/generated/worldgen_v0_1/terrain/lpc_mapped_terrain_v7_32.json"
LIVE = ROOT / "assets/generated/worldgen_v0_1/terrain/live_autotile_16_32.json"
FAMILY_RS = ROOT / "crates/haven_world/src/autotile/terrain_family.rs"
CORE_RS = ROOT / "crates/haven_core/src/autotile_data.rs"
OUT_JSON = ROOT / "tools/automation/reports/lpc_terrain_pattern_audit_v147r.json"
OUT_MD = ROOT / "tools/automation/reports/lpc_terrain_pattern_audit_v147r.md"

SIX = {"Grass", "Sand", "Road", "StonePath", "ShallowWater", "DeepWater"}

def load(path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)

def main():
    mapped = load(MAPPED)
    live = load(LIVE)
    topology = Counter(entry.get("topology", "unknown") for entry in mapped.get("entries", []))
    corner_sets = Counter(tuple(sorted(set(entry.get("corners", {}).values()))) for entry in mapped.get("entries", []))
    groups = [group.get("id") for group in live.get("groups", [])]
    variants = Counter(item.get("group") for item in live.get("variants", []))
    family_text = FAMILY_RS.read_text(encoding="utf-8")
    core_text = CORE_RS.read_text(encoding="utf-8")
    collisions = []
    for needle, finding in [
        (r"TileKind::PebbleShore \| TileKind::StonePath => Self::PebblePath", "StonePath collapses into PebblePath"),
        (r"TileKind::Road \| TileKind::MountainPath \| TileKind::Bridge => Self::Road", "MountainPath and Bridge collapse into Road"),
    ]:
        if re.search(needle, family_text):
            collisions.append(finding)
    if "StonePath" in core_text and "MountainPath" in core_text and "TileAutoGroup::Road" in core_text:
        collisions.append("Multiple path TileKinds share TileAutoGroup::Road")
    required_groups = ["road", "stone_path", "mountain_path", "bridge"]
    missing_groups = [group for group in required_groups if group not in groups]
    report = {
        "schema": "havenwild.lpc_terrain_pattern_audit.v147r",
        "mappedEntryCount": len(mapped.get("entries", [])),
        "mappedTopologyCounts": dict(sorted(topology.items())),
        "uniqueCornerSignatures": len(corner_sets),
        "liveAutotileGroups": groups,
        "liveVariantCounts": dict(sorted(variants.items())),
        "identityCollisions": collisions,
        "missingDistinctPathGroups": missing_groups,
        "prototypeTerrains": sorted(SIX),
        "status": "blocked" if collisions or missing_groups else "ready"
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# LPC Terrain Pattern Audit — Pass 147R", "",
        f"- mapped entries: **{report['mappedEntryCount']}**",
        f"- unique corner signatures: **{report['uniqueCornerSignatures']}**",
        f"- live autotile groups: **{', '.join(groups)}**", "",
        "## Identity collisions", "",
    ]
    lines += [f"- {item}" for item in collisions] or ["- none"]
    lines += ["", "## Missing distinct path groups", ""]
    lines += [f"- {item}" for item in missing_groups] or ["- none"]
    lines += ["", "## Topology inventory", ""]
    lines += [f"- `{key}`: {value}" for key, value in sorted(topology.items())]
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Pass 147R terrain audit: {report['mappedEntryCount']} mapped entries, {len(collisions)} identity collisions, {len(missing_groups)} missing path groups")
    print(OUT_JSON.relative_to(ROOT))
    print(OUT_MD.relative_to(ROOT))
    return 1 if not mapped.get("entries") else 0

if __name__ == "__main__":
    raise SystemExit(main())
