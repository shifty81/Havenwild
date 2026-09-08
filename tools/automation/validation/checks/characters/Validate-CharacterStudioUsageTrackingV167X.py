#!/usr/bin/env python3
from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
def require(relative: str) -> Path:
    path = ROOT / relative
    if not path.is_file():
        raise FileNotFoundError(f"missing required file: {relative}")
    return path


def main() -> int:
    loader = require("crates/haven_assets/src/universal_lpc_character_authority.rs").read_text(encoding="utf-8")
    studio = require("apps/haven_editor_native/src/app/character_studio.rs").read_text(encoding="utf-8")
    app_mod = require("apps/haven_editor_native/src/app/mod.rs").read_text(encoding="utf-8")
    usage = require("tools/automation/characters/Build-UniversalLpcUsageManifestV167X.py")
    contract_path = require("content/editor/character_studio_universal_lpc_source_v0_1.json")
    contract = json.loads(contract_path.read_text(encoding="utf-8"))

    for token in [
        "UniversalLpcCharacterAuthority",
        "license_tier_counts",
        "share_alike_required",
        "DEFAULT_UNIVERSAL_LPC_AUTHORITY_PATH",
    ]:
        if token not in loader:
            raise ValueError(f"authority loader is missing {token}")

    for token in [
        "CharacterStudioMode",
        "Preferred Only",
        "Include CC-BY-SA",
        "CharacterAssetFilter",
        "draw_character_studio_workspace",
        "handle_character_studio_click",
    ]:
        if token not in studio and token not in app_mod:
            raise ValueError(f"live Character Studio is missing {token}")

    if "CharacterStudio" not in app_mod:
        raise ValueError("Character Studio is not registered as a native-editor viewport")

    ast.parse(usage.read_text(encoding="utf-8"), filename=str(usage))
    if contract.get("authorityOutput") != "WORKSPACE/generated/universal_lpc_character_authority_v167w.json":
        raise ValueError("Character Studio contract does not point to the v167w authority")
    if contract.get("usageManifestTool") != "tools/automation/characters/Build-UniversalLpcUsageManifestV167X.py":
        raise ValueError("Character Studio contract is missing the exact usage-manifest tool")

    print("Character Studio live authority and usage tracking validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
