#!/usr/bin/env python3
"""Validate the Pass 100 asset utilization audit workflow."""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
REPORT = ROOT / "docs/assets/HAVENWILD_ASSET_UTILIZATION_AUDIT_PASS100.md"


def text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def require(path: str, needles: list[str]) -> None:
    payload = text(path)
    missing = [needle for needle in needles if needle not in payload]
    if missing:
        raise SystemExit(f"V115: {path} missing {missing}")


def ensure_report() -> None:
    if REPORT.is_file():
        return
    builder = ROOT / "tools/automation/assets/Build-HavenwildAssetUtilizationAuditV115.py"
    subprocess.run([sys.executable, str(builder)], cwd=ROOT, check=True)


def main() -> int:
    require(
        "tools/automation/terrain/Promote-LpcTerrainFamiliesV90.py",
        [
            "REPEATABLE_FILL_ALIASES",
            '"natural": "grass"',
            "def repeatable_fill_id",
            '"version": "0.8.1"',
        ],
    )
    require(
        "tools/automation/assets/Build-HavenwildAssetUtilizationAuditV115.py",
        [
            "Havenwild Asset Utilization Audit",
            "canonical LPC source",
            "unknown_requires_review",
            "asset-utilization-audit",
        ],
    )
    ensure_report()
    require(
        "docs/assets/HAVENWILD_ASSET_UTILIZATION_AUDIT_PASS100.md",
        [
            "Havenwild Asset Utilization Audit",
            "Production plan",
            "canonical LPC source",
            "unknown_requires_review",
        ],
    )
    require("tools/build/Build.sh", ["asset-utilization-audit", "Build-HavenwildAssetUtilizationAuditV115.py"])
    require("tools/automation/validation/validate.py", ["Validate-HavenwildAssetUtilizationAuditV115.py"])
    print("V115 OK: asset utilization audit workflow and abstract LPC fill resolution are locked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
