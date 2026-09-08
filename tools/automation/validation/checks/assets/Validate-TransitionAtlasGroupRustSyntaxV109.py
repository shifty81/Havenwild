#!/usr/bin/env python3
"""Guard the ordered-pair match-arm separators before Cargo formatting."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
PATH = ROOT / "crates/haven_world/src/autotile/transition_atlas_groups.rs"


def main() -> int:
    source = PATH.read_text(encoding="utf-8")
    broken = ') => Some("sand_bank_over_shallow")\n        (TerrainFamily::DeepWater'
    if broken in source:
        raise AssertionError("sand-bank match arm is missing its trailing comma")
    fixed = ') => Some("sand_bank_over_shallow"),\n        (TerrainFamily::DeepWater'
    if fixed not in source:
        raise AssertionError("expected adjacent sand-bank/deep-water match arms were not found")
    atlas_source = (
        ROOT / "crates/haven_world/src/autotile/transition_atlas.rs"
    ).read_text(encoding="utf-8")
    for required in ("let material = self.material?;", "let atlas_group = self.atlas_group?;"):
        if required not in atlas_source:
            raise AssertionError(f"strict-Clippy Option extraction missing: {required}")
    sync_source = (
        ROOT / "tools/automation/terrain/Sync-LpcSummerRuntimeMetadataV108.py"
    ).read_text(encoding="utf-8")
    if '"runtimeOuterMasks": True' not in sync_source:
        raise AssertionError("restored runtime transition families must enable outer masks")
    tests = (ROOT / "crates/haven_assets/src/autotile.rs").read_text(encoding="utf-8")
    for stale in (
        "assert_eq!(entry.variant_index, 99)",
        "assert_eq!(entry.variant_index, 143)",
        "assert_eq!(edge.variant_index, 35)",
    ):
        if stale in tests:
            raise AssertionError(f"atlas test still depends on unstable bake ordering: {stale}")
    print("V109 OK: transition atlas ordered-pair match arms are comma-separated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
