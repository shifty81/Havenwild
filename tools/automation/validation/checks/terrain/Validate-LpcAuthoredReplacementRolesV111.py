#!/usr/bin/env python3
"""Guard the Pass 97 complete-cell LPC transition model."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
def main() -> int:
    promoter = (ROOT / "tools/automation/terrain/Promote-LpcTerrainFamiliesV90.py").read_text(encoding="utf-8")
    required = (
        "if len(roles) != 1:",
        "return block[row][column].copy()",
        "return compound_fill.copy()",
        '"version": "0.8.1"',
        '"version": "havenwild.lpc_replacement_role.v0_2"',
        '"natural": "grass"',
        "def repeatable_fill_id",
    )
    missing = [value for value in required if value not in promoter]
    if missing:
        raise AssertionError(f"authored replacement-role baker missing: {missing}")
    validator = (ROOT / "tools/automation/validation/checks/terrain/Validate-LpcEdgeSignatureSeamsV108.py").read_text(encoding="utf-8")
    if "non-zero replacement role is empty" not in validator:
        raise AssertionError("compound-mask closure guard missing")
    contract = ROOT / "content/assets/tile_extraction/tile_extraction_workbench_contract_v0_1.json"
    if not contract.is_file():
        raise AssertionError("V55 tile-extraction workbench contract missing")
    print("V111 OK: LPC transitions use complete authored replacement roles without color-filtered composites")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
