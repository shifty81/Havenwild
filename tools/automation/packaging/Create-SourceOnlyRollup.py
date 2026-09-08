#!/usr/bin/env python3
"""Create the normal lean, reproducible Havenwild Complete Source Rollup."""
from __future__ import annotations

import argparse
import zipfile
from datetime import datetime
from pathlib import Path

from source_rollup_policy import iter_normal_rollup_files

ROOT = Path(__file__).resolve().parents[3]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    output = args.output
    if output is None:
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        output = ROOT / "WORKSPACE" / "exports" / f"Havenwild_LeanSource_{stamp}.zip"
    elif not output.is_absolute():
        output = ROOT / output
    output.parent.mkdir(parents=True, exist_ok=True)

    entries = list(iter_normal_rollup_files(ROOT, output=output))
    raw_bytes = sum(path.stat().st_size for path in entries)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in entries:
            archive.write(path, path.relative_to(ROOT).as_posix())

    print(f"Lean source rollup: {output}")
    print(f"Files: {len(entries):,}")
    print(f"Source bytes: {raw_bytes:,}")
    print(f"Archive bytes: {output.stat().st_size:,}")
    print("Downloaded dependencies, rebuildable caches, and historical package evidence excluded.")
    print("Havenwild-owned source art remains until a separate recoverable owned-content store exists.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
