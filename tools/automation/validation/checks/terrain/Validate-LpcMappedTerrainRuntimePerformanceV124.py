#!/usr/bin/env python3
"""Guard mapped LPC terrain runtime lookup performance."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
def require_any(paths: list[Path], needles: list[str]) -> None:
    payloads = [(path, path.read_text(encoding="utf-8")) for path in paths]
    missing = [
        needle
        for needle in needles
        if not any(needle in payload for _, payload in payloads)
    ]
    if missing:
        joined = ", ".join(str(path.relative_to(ROOT)) for path, _ in payloads)
        raise SystemExit(f"V124: none of [{joined}] contain {missing}")


def main() -> int:
    source_path = ROOT / "crates/haven_assets/src/lpc_mapped_terrain.rs"
    tests_path = ROOT / "crates/haven_assets/src/lpc_mapped_terrain_tests.rs"
    source = source_path.read_text(encoding="utf-8")
    required = [
        "collections::HashMap",
        "lookup: HashMap<[LpcMappedTerrainMaterial; 4], Vec<usize>>",
        "enum LpcMappedTerrainMaterial",
        "lookup.entry(entry.corners).or_default().push(index)",
        "let matches = self.lookup.get(&corners)?;",
        "Some(LpcMappedTerrainMaterial::DirtTan)",
    ]
    missing = [needle for needle in required if needle not in source]
    if missing:
        raise SystemExit(f"V124: mapped terrain runtime performance guard missing {missing}")
    forbidden = [
        "self.entries.iter().filter",
        "let matches = ||",
        "matches().count()",
        "matches().nth",
        "Some(\"Dirt_Tan\")",
        "[\"Grass\"; 4]",
    ]
    present = [needle for needle in forbidden if needle in source]
    if present:
        raise SystemExit(
            "V124: mapped terrain lookup regressed to per-tile manifest scanning: "
            + ", ".join(present)
        )
    require_any(
        [source_path, tests_path],
        ["entry_for_corners([LpcMappedTerrainMaterial::Grass; 4], 0)"],
    )
    print("V124 OK: mapped LPC terrain runtime uses indexed typed-material lookup")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
