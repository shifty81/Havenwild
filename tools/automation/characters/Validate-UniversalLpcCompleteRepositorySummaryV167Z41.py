#!/usr/bin/env python3
"""Validate the generated Universal LPC repository index summary.

This is intentionally lightweight. Build.sh uses it before trusting the
revision marker so a stale or legacy summary cannot bypass index rebuilding.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_EXPECTED = ROOT / "content/assets/lpc/universal_lpc_complete_repository_expected_summary_v0_1.json"
DEFAULT_SUMMARY = ROOT / "content/assets/lpc/universal_lpc_complete_repository_summary_v0_1.json"
DEFAULT_REVISION = ROOT / "WORKSPACE/generated/.universal_lpc_complete_repository_revision"
DEFAULT_INDEX = ROOT / "content/assets/lpc/universal_lpc_complete_repository_index_v0_1.json.gz"
DEFAULT_EQUIPMENT = ROOT / "content/assets/lpc/universal_lpc_equipment_action_catalog_v0_1.json"
DEFAULT_GAMEPLAY = ROOT / "content/assets/lpc/universal_lpc_gameplay_item_seed_catalog_v0_1.json"
REQUIRED_COUNT_KEYS = (
    "spritesheetPngFiles",
    "sheetDefinitionJsonFiles",
    "creditRecords",
)


def load_json(path: Path, label: str) -> dict[str, Any]:
    if not path.is_file():
        raise RuntimeError(f"{label} is missing: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception as error:  # noqa: BLE001
        raise RuntimeError(f"{label} is invalid JSON: {path}: {error}") from error
    if not isinstance(value, dict):
        raise RuntimeError(f"{label} must contain a JSON object: {path}")
    return value


def validate(
    *,
    expected_path: Path,
    summary_path: Path,
    revision_path: Path,
    index_path: Path,
    equipment_path: Path,
    gameplay_path: Path,
    require_artifacts: bool,
) -> dict[str, Any]:
    expected = load_json(expected_path, "locked Universal LPC expected summary")
    summary = load_json(summary_path, "generated Universal LPC summary")

    expected_commit = expected.get("commit")
    if not isinstance(expected_commit, str) or not expected_commit:
        raise RuntimeError("locked Universal LPC expected summary has no commit")

    if summary.get("schema") != "havenwild.universal_lpc.complete_repository_summary.v0_1":
        raise RuntimeError(
            "generated Universal LPC summary uses a stale or unsupported schema; "
            "the complete repository index must be rebuilt"
        )
    if summary.get("sourceCommit") != expected_commit:
        raise RuntimeError(
            "generated Universal LPC summary commit does not match the locked source; "
            "the complete repository index must be rebuilt"
        )
    if summary.get("strictCertified") is not True:
        raise RuntimeError(
            "generated Universal LPC summary is not strict-certified; "
            "the complete repository index must be rebuilt"
        )

    counts = summary.get("counts")
    expected_counts = expected.get("counts")
    if not isinstance(counts, dict):
        raise RuntimeError(
            "generated Universal LPC summary has no canonical counts object; "
            "the complete repository index must be rebuilt"
        )
    if not isinstance(expected_counts, dict):
        raise RuntimeError("locked Universal LPC expected summary has no counts object")
    for key in REQUIRED_COUNT_KEYS:
        actual = counts.get(key)
        locked = expected_counts.get(key)
        if actual != locked:
            raise RuntimeError(
                f"generated Universal LPC summary mismatch for {key}: {actual!r} != {locked!r}; "
                "the complete repository index must be rebuilt"
            )

    if not revision_path.is_file():
        raise RuntimeError(f"Universal LPC index revision marker is missing: {revision_path}")
    installed_revision = revision_path.read_text(encoding="utf-8").strip()
    if installed_revision != expected_commit:
        raise RuntimeError(
            f"Universal LPC index revision mismatch: {installed_revision!r} != {expected_commit!r}"
        )

    if require_artifacts:
        for path, label in (
            (index_path, "complete repository index"),
            (equipment_path, "equipment/action catalog"),
            (gameplay_path, "gameplay item seed catalog"),
        ):
            if not path.is_file() or path.stat().st_size <= 0:
                raise RuntimeError(f"Universal LPC {label} is missing or empty: {path}")

    return {
        "schema": "havenwild.universal_lpc.summary_validation.v167z41",
        "sourceCommit": expected_commit,
        "counts": {key: counts[key] for key in REQUIRED_COUNT_KEYS},
        "strictCertified": True,
        "artifactsValidated": require_artifacts,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--expected", type=Path, default=DEFAULT_EXPECTED)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--revision", type=Path, default=DEFAULT_REVISION)
    parser.add_argument("--index", type=Path, default=DEFAULT_INDEX)
    parser.add_argument("--equipment", type=Path, default=DEFAULT_EQUIPMENT)
    parser.add_argument("--gameplay", type=Path, default=DEFAULT_GAMEPLAY)
    parser.add_argument("--skip-artifacts", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    try:
        result = validate(
            expected_path=args.expected.resolve(),
            summary_path=args.summary.resolve(),
            revision_path=args.revision.resolve(),
            index_path=args.index.resolve(),
            equipment_path=args.equipment.resolve(),
            gameplay_path=args.gameplay.resolve(),
            require_artifacts=not args.skip_artifacts,
        )
    except Exception as error:  # noqa: BLE001
        if not args.quiet:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    if not args.quiet:
        print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
