#!/usr/bin/env python3
"""Build Havenwild's lossless normalized metadata mirror of the pinned ULPC repository.

The upstream source remains immutable. This generator mirrors JSON definitions, palette
metadata and credits into a deterministic gzip catalog for Rust/editor/runtime ingestion.
"""
from __future__ import annotations

import csv
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SOURCE_ROOT = ROOT / "assets/source/licensed/universal_lpc_generator"
SHEET_DEFS = SOURCE_ROOT / "sheet_definitions"
PALETTE_DEFS = SOURCE_ROOT / "palette_definitions"
CREDITS = SOURCE_ROOT / "CREDITS.csv"
SOURCE_LOCK = ROOT / "content/assets/intake/universal_lpc_generator_source_lock_v0_1.json"
OUT = ROOT / "content/assets/lpc/universal_lpc_normalized_character_catalog_v1.json.gz"
SUMMARY = ROOT / "content/assets/lpc/universal_lpc_normalized_character_catalog_summary_v1.json"
SCHEMA = "havenwild.universal_lpc.normalized_character_catalog.v1"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def stable_id(path: Path) -> str:
    rel = path.relative_to(SHEET_DEFS).with_suffix("").as_posix()
    return rel.replace("/", "_")


def collect_json(root: Path, id_kind: str):
    rows = []
    for path in sorted(root.rglob("*.json"), key=lambda p: p.as_posix().lower()):
        raw = load_json(path)
        rel = path.relative_to(SOURCE_ROOT).as_posix()
        row = {"sourcePath": rel, "definition": raw}
        if id_kind == "sheet":
            row["itemId"] = stable_id(path)
        rows.append(row)
    return rows


def read_credits():
    if not CREDITS.exists():
        return []
    with CREDITS.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> int:
    missing = [p for p in (SHEET_DEFS, PALETTE_DEFS, CREDITS, SOURCE_LOCK) if not p.exists()]
    if missing:
        raise SystemExit("Missing pinned ULPC inputs: " + ", ".join(str(p.relative_to(ROOT)) for p in missing))

    source_lock = load_json(SOURCE_LOCK)
    source_commit = source_lock.get("commit") or source_lock.get("sourceCommit") or source_lock.get("pinnedCommit")
    if not source_commit:
        raise SystemExit("Universal LPC source lock does not expose a pinned commit")

    sheets = collect_json(SHEET_DEFS, "sheet")
    palettes = collect_json(PALETTE_DEFS, "palette")
    credits = read_credits()
    payload = {
        "schema": SCHEMA,
        "sourceCommit": source_commit,
        "sourceRoot": "assets/source/licensed/universal_lpc_generator",
        "sourcePolicy": "immutable_upstream",
        "sheetDefinitions": sheets,
        "paletteDefinitions": palettes,
        "credits": credits,
    }
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    digest = hashlib.sha256(encoded).hexdigest()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("wb") as raw_handle:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw_handle, compresslevel=9, mtime=0) as handle:
            handle.write(encoded)

    summary = {
        "schema": "havenwild.universal_lpc.normalized_character_catalog_summary.v1",
        "sourceCommit": source_commit,
        "catalog": str(OUT.relative_to(ROOT)).replace("\\", "/"),
        "uncompressedSha256": digest,
        "sheetDefinitionCount": len(sheets),
        "paletteDefinitionCount": len(palettes),
        "creditRecordCount": len(credits),
        "itemDefinitionCount": sum(1 for r in sheets if r["definition"].get("name") and r["definition"].get("layer_1")),
        "multiLayerItemCount": sum(1 for r in sheets if r["definition"].get("layer_2")),
        "customAnimationItemCount": sum(1 for r in sheets if any(isinstance(r["definition"].get(f"layer_{i}"), dict) and r["definition"][f"layer_{i}"].get("custom_animation") for i in range(1,10))),
    }
    SUMMARY.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"PASS: normalized ULPC catalog: {len(sheets)} sheet defs, {len(palettes)} palettes, {len(credits)} credits")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
