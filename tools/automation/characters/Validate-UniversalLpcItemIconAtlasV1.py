#!/usr/bin/env python3
"""Validate that the generated Universal LPC item-icon atlas matches current item authority."""
from __future__ import annotations

import argparse
import gzip
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SEEDS = ROOT / "content/gameplay/universal_lpc_equipment_item_seed_catalog_v0_1.json"
NORMALIZED = ROOT / "content/assets/lpc/universal_lpc_normalized_character_catalog_v1.json.gz"
MANIFEST = ROOT / "assets/generated/lpc/item_icons/universal_lpc_item_icons_v1.json"
ATLAS = ROOT / "assets/generated/lpc/item_icons/universal_lpc_item_icons_v1.png"
REQUIRED_VISIBLE = {"item.ulpc.tools_tool_axe", "item.ulpc.tools_tool_pickaxe"}


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()
    errors: list[str] = []
    for path in (SEEDS, MANIFEST, ATLAS):
        if not path.exists():
            errors.append(f"missing {path.relative_to(ROOT)}")
    if errors:
        if not args.quiet:
            print("FAIL: Universal LPC item icon atlas")
            for error in errors:
                print("-", error)
        return 1

    seeds = load_json(SEEDS)
    manifest = load_json(MANIFEST)
    expected = {row.get("itemId") for row in seeds.get("items", []) if row.get("itemId")}
    entries = {row.get("itemId"): row for row in manifest.get("entries", []) if row.get("itemId")}
    actual = set(entries)
    missing = sorted(expected - actual)
    extra = sorted(actual - expected)
    if missing:
        errors.append(f"manifest missing {len(missing)} current item id(s): {', '.join(missing[:8])}")
    if extra:
        errors.append(f"manifest contains {len(extra)} stale item id(s): {', '.join(extra[:8])}")

    unresolved = set(manifest.get("missingItemIds", []))
    for item_id in REQUIRED_VISIBLE:
        row = entries.get(item_id)
        if row is None:
            errors.append(f"required player-facing icon missing entry: {item_id}")
            continue
        if item_id in unresolved or not row.get("sourcePng"):
            errors.append(f"required player-facing icon has no resolved source PNG: {item_id}")
        rect = row.get("rect")
        if not isinstance(rect, list) or len(rect) != 4 or min(rect[2:]) <= 0:
            errors.append(f"required player-facing icon has invalid atlas rect: {item_id}")

    if NORMALIZED.exists():
        try:
            with gzip.open(NORMALIZED, "rt", encoding="utf-8") as handle:
                normalized = json.load(handle)
            source_commit = normalized.get("sourceCommit")
            if source_commit and manifest.get("sourceCommit") != source_commit:
                errors.append("item-icon atlas source commit does not match normalized ULPC catalog")
        except Exception as exc:
            errors.append(f"could not inspect normalized ULPC catalog: {exc}")

    if manifest.get("itemCount") != len(expected):
        errors.append(
            f"itemCount {manifest.get('itemCount')} does not match current seed count {len(expected)}"
        )

    if errors:
        if not args.quiet:
            print("FAIL: Universal LPC item icon atlas")
            for error in errors:
                print("-", error)
        return 1
    if not args.quiet:
        print(f"PASS: Universal LPC item icon atlas current ({len(expected)} item icons)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
