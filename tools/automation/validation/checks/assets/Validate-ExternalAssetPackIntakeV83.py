#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
def require(path: str) -> Path:
    candidate = ROOT / path
    if not candidate.is_file():
        raise SystemExit(f"missing required file: {path}")
    return candidate


def main() -> None:
    contract = json.loads(require("content/assets/intake/external_asset_pack_contract_v0_1.json").read_text(encoding="utf-8"))
    if contract.get("schema") != "havenwild.external_asset_pack_contract.v0_1":
        raise SystemExit("external asset pack contract schema mismatch")
    if contract.get("rules", {}).get("rawAssetsAreCommitted") is not False:
        raise SystemExit("raw external assets must remain outside source rollups")
    require("content/assets/intake/external_asset_roots.example.json")
    require("tools/automation/assets/Prepare-ExternalAssetPack.py")
    require("tools/automation/packaging/Create-ChatGPTSourceRollup.py")
    require("content/architecture/chatgpt_source_rollup_policy_v0_1.json")
    build = require("tools/build/Build.sh").read_text(encoding="utf-8")
    for token in ("asset-pack-prepare", "asset-pack-catalog", "asset-pack-audit", "source-rollup"):
        if token not in build:
            raise SystemExit(f"tools/build/Build.sh is missing command: {token}")
    ignore = require(".gitignore").read_text(encoding="utf-8")
    if ".local/" not in ignore:
        raise SystemExit(".local must remain ignored")
    library = require("crates/haven_pixel/src/library.rs").read_text(encoding="utf-8")
    for token in ("External", "havenwild_external_asset_roots.json", "external://"):
        if token not in library:
            raise SystemExit(f"Pixel library external-root support missing token: {token}")
    print("External Asset Pack Intake V83 passed")


if __name__ == "__main__":
    main()
