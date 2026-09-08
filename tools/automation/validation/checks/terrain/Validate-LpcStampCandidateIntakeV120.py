#!/usr/bin/env python3
"""Validate the Pass108 LPC stamp candidate intake queue."""

from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
INTAKE = ROOT / "content/assets/intake/havenwild_lpc_stamp_candidate_intake_pass108.json"

REQUIRED_FIELDS = {
    "number",
    "label",
    "sourcePack",
    "sourcePath",
    "sourceRect",
    "sourceKind",
    "previewGroup",
    "intendedObjectKinds",
    "promotionLane",
    "priority",
    "status",
    "licenseStatus",
    "license",
    "requiredBeforePromotion",
}

REQUIRED_BEFORE_PROMOTION = {
    "user_number_confirmation",
    "source_slice_rects",
    "stable_ids",
    "runtime_atlas_output",
    "visual_collision_interaction_footprints",
    "license_attribution_record",
}


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def require_text(path: str, needles: list[str]) -> None:
    payload = read(path)
    missing = [needle for needle in needles if needle not in payload]
    if missing:
        raise SystemExit(f"V120: {path} missing {missing}")


def main() -> int:
    document = json.loads(INTAKE.read_text(encoding="utf-8"))
    if document.get("version") != "0.1.0":
        raise SystemExit("V120: expected intake catalog version 0.1.0")
    if document.get("pass") != 108:
        raise SystemExit("V120: expected Pass108 intake catalog")

    preview_board = ROOT / document["previewBoard"]
    preview_index = ROOT / document["previewIndex"]
    if not preview_board.is_file():
        raise SystemExit(f"V120: missing preview board {preview_board}")
    if not preview_index.is_file():
        raise SystemExit(f"V120: missing preview index {preview_index}")

    records = document["records"]
    if len(records) != 24:
        raise SystemExit(f"V120: expected 24 candidate records, found {len(records)}")
    numbers = [record["number"] for record in records]
    if numbers != list(range(1, 25)):
        raise SystemExit(f"V120: candidate numbers must be 1..24, found {numbers}")

    with preview_index.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != len(records):
        raise SystemExit("V120: CSV preview index and JSON intake record counts differ")

    for record, row in zip(records, rows):
        missing = sorted(REQUIRED_FIELDS - set(record))
        if missing:
            raise SystemExit(f"V120: candidate {record.get('number')} missing {missing}")
        if int(row["number"]) != record["number"]:
            raise SystemExit("V120: CSV and JSON candidate order diverged")
        if record["status"] != "candidate_needs_user_confirmation_and_slice_metadata":
            raise SystemExit(f"V120: candidate {record['number']} has unsafe status {record['status']}")
        if record["licenseStatus"] != "allowed_with_attribution":
            raise SystemExit(f"V120: candidate {record['number']} is not allowed-with-attribution")
        if not record["intendedObjectKinds"]:
            raise SystemExit(f"V120: candidate {record['number']} has no intended object kinds")
        if set(record["requiredBeforePromotion"]) != REQUIRED_BEFORE_PROMOTION:
            raise SystemExit(f"V120: candidate {record['number']} has incomplete promotion gates")
        rect = record["sourceRect"]
        if len(rect) != 4 or rect[2] <= 0 or rect[3] <= 0:
            raise SystemExit(f"V120: candidate {record['number']} has invalid source rect {rect}")

    policy = document["sourcePolicy"]
    if not policy.get("noRuntimePromotionUntilConfirmed"):
        raise SystemExit("V120: source policy must block runtime promotion before confirmation")
    if not policy.get("rawPacksRemainExternal"):
        raise SystemExit("V120: raw packs must remain external to the source rollup")
    if not policy.get("unknownLicenseAssetsRemainQuarantined"):
        raise SystemExit("V120: unknown-license assets must remain quarantined")

    require_text(
        "docs/assets/HAVENWILD_LPC_STAMP_CANDIDATE_INTAKE_PASS108.md",
        [
            "Nothing here is promoted to runtime until confirmed and sliced",
            "Preview board:",
            "CSV index:",
        ],
    )
    require_text(
        "content/assets/lpc/lpc_placeable_object_promotion_plan_v0_1.json",
        [
            "The editor must not expose unverified source-pack assets as production placeables.",
            "cave_entrance",
            "stamp_required",
        ],
    )

    print("V120 OK: Pass108 stamp candidate intake queue is numbered, review-only, and promotion-gated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
