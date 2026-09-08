#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
POLICY = ROOT / "content/architecture/havenwild_source_rollup_policy_v1.json"
PACKAGE = ROOT / "tools/control/PackageProject.ps1"
SOURCE_ONLY = ROOT / "tools/automation/packaging/Create-SourceOnlyRollup.py"
CHAT = ROOT / "tools/automation/packaging/Create-ChatGPTSourceRollup.py"
HELPER = ROOT / "tools/automation/packaging/source_rollup_policy.py"
REGISTRY = ROOT / "tools/control/ProjectCommandRegistry.ps1"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit("FAIL: " + message)


data = json.loads(POLICY.read_text(encoding="utf-8"))
normal = data["normalRollup"]
exclude_prefixes = set(normal["excludePrefixes"])
exclude_exact = set(normal["excludeExactPaths"])
retain = set(normal["alwaysRetainPrefixes"])

require("assets/generated/" in exclude_prefixes, "generated runtime assets must be excluded from normal rollups")
require("assets/source/licensed/" in exclude_prefixes, "downloaded licensed dependency mounts must be excluded")
require("content/audio/music/frontend/Harp.ogg" in exclude_exact, "frontend music binary must be rebuildable")
require("content/assets/lpc/universal_lpc_equipment_action_catalog_v0_1.json" in exclude_exact, "ULPC equipment catalog must be rebuildable")
require("content/assets/lpc/lpc_slice_catalog_v0_1.json" in exclude_exact, "ElizaWy slice catalog must be rebuildable")
require("content/assets/lpc/lpc_character_repository_inventory_v0_1.json" in exclude_exact, "ElizaWy character inventory must be rebuildable")
require("content/assets/intake/external_pack_indexes/elizawy_lpc_main.json" in exclude_exact, "large ElizaWy external-pack index must be rebuildable")
require("content/assets/intake/external_sprite_library_catalog_v0_1.json" in exclude_exact, "machine-local sprite-library catalog must be excluded")
require("assets/source/original/" in retain, "Havenwild-owned source art must stay retained")
require("content/ui/" in retain, "Havenwild-owned player/frontend UI art must stay retained")

package = PACKAGE.read_text(encoding="utf-8")
require("havenwild_source_rollup_policy_v1.json" in package, "root PackageProject must consume lean rollup policy")
require("Get-RollupProjectFiles" in package, "rollup must have a dedicated filtered file lane")
require("havenwild_reproducible_lean_source_v1" in package, "rollup manifest must identify the lean source policy")

for script in (SOURCE_ONLY, CHAT):
    text = script.read_text(encoding="utf-8")
    require("iter_normal_rollup_files" in text, f"{script.name} must use shared rollup authority")
require("excluded_from_normal_rollup" in HELPER.read_text(encoding="utf-8"), "shared Python rollup helper is missing")
require("Package lean complete source rollup" in REGISTRY.read_text(encoding="utf-8"), "root menu must name the lean rollup behavior")

build_sh = (ROOT / "tools/build/Build.sh").read_text(encoding="utf-8")
build_ps1 = (ROOT / "tools/build/Build.ps1").read_text(encoding="utf-8")
for token in (
    "Ensure-FrontendMusicV167Z56.py",
    "Ensure-UniversalLpcGenerator.py",
    "Build-UniversalLpcCompleteRepositoryIndexV167Z7.py",
    "Build-LpcLegacyCharacterCatalogsV1.py",
    "Build-ElizaWyExternalPackIndexV1.py",
    "Promote-LpcRuntimeAssets.py",
):
    require(token in build_sh or token in build_ps1, f"bootstrap authority missing for {token}")

print("PASS: H21A14AB29 lean reproducible source-rollup authority")
print("- normal rollups exclude downloaded dependencies, generated caches, large external-library indexes, frontend music binary and historical package evidence")
print("- Havenwild-owned original/UI source art remains authoritative until a separate owned-content store exists")
print("- root utility and Python rollup helpers share one policy contract")
