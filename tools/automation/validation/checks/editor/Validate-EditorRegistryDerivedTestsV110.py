#!/usr/bin/env python3
"""Prevent editor tests from depending on removed assets or optional manifests."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
def main() -> int:
    lib_tests = (ROOT / "crates/haven_editor/src/lib_tests.rs").read_text(encoding="utf-8")
    stamp_tests = (ROOT / "crates/haven_editor/src/stamp_edit.rs").read_text(encoding="utf-8")
    forbidden = (
        "Manifest: worldgen_asset_manifest_v0_1",
        '.entry("home_tavern_mountain_entrance")',
        '.expect("mountain tavern")',
    )
    combined = lib_tests + stamp_tests
    stale = [value for value in forbidden if value in combined]
    if stale:
        raise AssertionError(f"editor tests retain stale asset assumptions: {stale}")
    required = (
        'format!("Manifest: {}", registry.manifest_id())',
        '.entries()\n            .first()',
        '.visual_rect();',
    )
    missing = [value for value in required if value not in combined]
    if missing:
        raise AssertionError(f"registry-derived editor test coverage missing: {missing}")
    print("V110 OK: editor tests derive manifest and stamp expectations from live registries")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
