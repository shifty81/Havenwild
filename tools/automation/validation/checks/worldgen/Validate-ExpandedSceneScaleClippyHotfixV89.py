#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
LOADER = ROOT / "crates/haven_core/src/worldgen_loader.rs"


def main() -> int:
    issues: list[str] = []
    source = LOADER.read_text(encoding="utf-8")

    forbidden = [
        "for y in 0..source_h {\n        let row = zone_rows[y]",
        "for x in 0..source_w {\n            let raw_zone = row[x]",
        "#[allow(clippy::needless_range_loop)]",
    ]
    for token in forbidden:
        if token in source:
            issues.append(f"worldgen_loader.rs retains forbidden clippy workaround/pattern: {token!r}")

    required = [
        "for (y, zone_row) in zone_rows.iter().enumerate().take(source_h)",
        "for (x, zone_cell) in row.iter().enumerate().take(source_w)",
        "if zone_rows.len() != source_h",
        "if row.len() != source_w",
        "TavernMap::idx(target_x, target_y)",
    ]
    for token in required:
        if token not in source:
            issues.append(f"worldgen_loader.rs missing clippy-safe zone migration token: {token}")

    if issues:
        print("Expanded scene scale clippy hotfix validation FAILED")
        for issue in issues:
            print(f"- {issue}")
        return 1

    print("Expanded scene scale clippy hotfix validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
