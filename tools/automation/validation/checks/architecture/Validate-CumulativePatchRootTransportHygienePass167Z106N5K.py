#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]


def fail(message: str) -> None:
    raise SystemExit(f"N5K cumulative-patch root transport hygiene validation FAILED: {message}")


def read(relative: str) -> str:
    path = ROOT / relative
    if not path.is_file():
        fail(f"missing required source: {relative}")
    return path.read_text(encoding="utf-8")


def main() -> None:
    for helper in ("APPLY_HAVENWILD_PATCH.cmd", "APPLY_HAVENWILD_PATCH.md"):
        if (ROOT / helper).exists():
            fail(f"package-only helper must never persist at repository root: {helper}")

    launcher = read("tools/control/HavenwildTools.ps1")
    required_launcher = [
        "$packageTransportHelpers = @('APPLY_HAVENWILD_PATCH.cmd','APPLY_HAVENWILD_PATCH.md')",
        "Removed stale cumulative-patch transport helper",
        "foreach ($packageHelper in $packageTransportHelpers)",
    ]
    for fragment in required_launcher:
        if fragment not in launcher:
            fail(f"launcher stale-transport cleanup authority missing: {fragment}")

    packager = read("tools/control/PackageProject.ps1")
    forbidden = [
        "Join-Path $staging 'APPLY_HAVENWILD_PATCH.cmd'",
        "Join-Path $staging 'APPLY_HAVENWILD_PATCH.md'",
    ]
    for fragment in forbidden:
        if fragment in packager:
            fail(f"packager still emits repository-root transport helper: {fragment}")
    if "manifests\\removals\\PATCH_REMOVALS.txt" not in packager and "PATCH_REMOVALS.txt" not in packager:
        fail("cumulative removal manifest transport is missing")
    if "ApplyPatchRemovals.ps1" not in packager:
        fail("explicit tools/control removal retry authority is missing")

    print("N5K cumulative patch root transport hygiene validated")


if __name__ == "__main__":
    main()
