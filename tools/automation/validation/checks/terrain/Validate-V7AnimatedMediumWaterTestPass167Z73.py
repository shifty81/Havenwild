#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
SOURCE = ROOT / "crates/haven_assets/src/lpc_mapped_terrain/tests.rs"


def fail(message: str) -> None:
    print(f"V7 animated medium-water test validation FAILED: {message}")
    raise SystemExit(1)


text = SOURCE.read_text(encoding="utf-8")
name = "fn ocean_depth_contact_uses_v7_medium_water_variant_without_losing_semantic_identity()"
start = text.find(name)
if start < 0:
    fail("updated ocean depth presentation regression test is missing")
end = text.find("\n    #[test]", start)
if end < 0:
    end = len(text)
block = text[start:end]

required = [
    'assert_eq!(map.get(4, 4), TileKind::OceanDeep);',
    'assert_eq!(mapped_terrain_at(&map, 4, 4), Some("Water"));',
    'filter(|entry| entry_matches(entry, ["Water"; 4]))',
    'assert!(medium_variants.len() > 1);',
    'assert!(medium_variants.contains(&medium_base.rect));',
    'assert!(!medium_base.is_mixed);',
    'assert!(overlay.is_mixed);',
    'assert!(deep_overlay.is_mixed);',
]
for token in required:
    if token not in block:
        fail(f"required contract token is missing: {token}")

retired = [
    'fn ocean_depth_contact_uses_medium_v7_rim_without_losing_semantic_identity()',
    'quiet_entry_for_corners(["Water"; 4])',
    'assert_eq!(medium_base.rect, expected_medium.rect);',
]
for token in retired:
    if token in block:
        fail(f"retired single-rectangle assumption remains: {token}")

print("V7 animated medium-water test validation passed")
