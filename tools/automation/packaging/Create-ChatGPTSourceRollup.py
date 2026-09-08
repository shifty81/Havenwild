#!/usr/bin/env python3
from __future__ import annotations

import argparse
import zipfile
from datetime import datetime
from pathlib import Path

from source_rollup_policy import iter_normal_rollup_files

ROOT = Path(__file__).resolve().parents[3]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a compact reproducible Havenwild source handoff")
    parser.add_argument("--output", type=Path, default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output = args.output or ROOT.parent / f"Havenwild_ChatGPT_SourceRollup_{datetime.now():%Y%m%d_%H%M%S}.zip"
    output = output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    entries = list(iter_normal_rollup_files(ROOT, output=output))
    source_bytes = sum(path.stat().st_size for path in entries)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in entries:
            archive.write(path, path.relative_to(ROOT).as_posix())
    print(f"Created {output}")
    print(f"Included {len(entries)} files ({source_bytes} source bytes)")
    print("Policy: content/architecture/havenwild_source_rollup_policy_v1.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
