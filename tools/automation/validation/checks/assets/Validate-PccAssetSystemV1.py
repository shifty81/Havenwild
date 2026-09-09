#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path


def find_repo() -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "Cargo.toml").is_file() and (parent / "tools/automation/assets/pcc_assets").is_dir():
            return parent
    raise RuntimeError("Havenwild repository root not found")


def main() -> int:
    repo = find_repo()
    sys.path.insert(0, str(repo))
    from tools.automation.assets.pcc_assets.selftest import run_selftest

    result = run_selftest()
    print(json.dumps(result, indent=2))
    if result.get("status") != "PASS":
        return 1
    print("[PASS] PCC universal asset system V1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
