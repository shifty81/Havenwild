#!/usr/bin/env python3
"""Validate the Pass 133 LPC tuple coverage audit workflow."""
from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[5]
BUILD_SCRIPT = ROOT / "tools/automation/terrain/Build-LpcTupleCoverageAuditV133.py"
AUDIT_JSON = ROOT / "content/assets/lpc/lpc_tuple_coverage_audit_v0_1.json"
AUDIT_MD = ROOT / "docs/assets/LPC_TUPLE_COVERAGE_AUDIT_PASS133.md"
AUDIT_PREVIEW = ROOT / "docs/assets/previews/havenwild_lpc_tuple_coverage_pass133.png"


def require_tokens(path: Path, tokens: list[str]) -> None:
    text = path.read_text(encoding="utf-8")
    missing = [token for token in tokens if token not in text]
    if missing:
        raise SystemExit(f"V133: {path.relative_to(ROOT)} is missing {missing}")


def main() -> int:
    require_tokens(
        BUILD_SCRIPT,
        [
            "PRODUCTION_PAIRS",
            "all_audit_pairs",
            "binary_corner_patterns",
            "fallback_material",
            "Water_Shallows_Sand",
            "Water_Shallows_Dirt",
            "havenwild_lpc_tuple_coverage_pass133.png",
        ],
    )

    if not AUDIT_JSON.exists():
        raise SystemExit(f"V133: missing {AUDIT_JSON.relative_to(ROOT)}")
    if not AUDIT_MD.exists():
        raise SystemExit(f"V133: missing {AUDIT_MD.relative_to(ROOT)}")
    if not AUDIT_PREVIEW.exists():
        raise SystemExit(f"V133: missing {AUDIT_PREVIEW.relative_to(ROOT)}")

    audit = json.loads(AUDIT_JSON.read_text(encoding="utf-8"))
    if audit.get("kind") != "terrain_tuple_coverage_audit":
        raise SystemExit("V133: tuple coverage audit kind is incorrect")
    if len(audit.get("productionPairs", [])) < 20:
        raise SystemExit("V133: tuple coverage audit must keep production terrain pairs")
    if len(audit.get("auditPairs", [])) < 80:
        raise SystemExit("V133: tuple coverage audit must cover all current terrain material pairs")

    totals = audit.get("totals", {})
    if not {"exact", "fallback"}.issubset(totals):
        raise SystemExit("V133: tuple coverage audit must report exact and fallback totals")
    if int(totals.get("exact", 0)) <= 0:
        raise SystemExit("V133: tuple coverage audit found no exact tuples")
    if int(totals.get("fallback", 0)) <= 0:
        raise SystemExit("V133: tuple coverage audit found no fallback tuples to track")

    rows = audit.get("rows", [])
    if not rows:
        raise SystemExit("V133: tuple coverage audit has no rows")
    statuses = {
        pattern.get("status")
        for row in rows
        for pattern in row.get("patterns", [])
    }
    if not {"exact", "fallback"}.issubset(statuses):
        raise SystemExit("V133: tuple coverage audit rows must include exact and fallback patterns")

    with Image.open(AUDIT_PREVIEW) as preview:
        if preview.width < 700 or preview.height < 500:
            raise SystemExit("V133: tuple coverage preview is unexpectedly small")

    print("V133 OK: LPC tuple coverage audit and visual preview board are generated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
