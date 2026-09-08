#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(
            f"FAILED Pass167Z92 native editor stamp-provider test contract: {message}"
        )


def main() -> None:
    quarantine = ROOT / "content/build/runtime_asset_integrity_cliff_quarantine_v167z96.json"
    if quarantine.is_file():
        contract = json.loads(quarantine.read_text(encoding="utf-8"))
        require(contract["pass"] == "167Z96", "Z96 quarantine pass")
        require(contract["runtimePolicy"]["proceduralCliffDrawing"] is False, "invalid renderer disabled")
        print("Pass167Z92 stamp-provider contract superseded by Pass167Z96 invalid-source quarantine")
        return
    contract_path = (
        ROOT / "content/editor/native_editor_stamp_provider_test_contract_v0_1.json"
    )
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    require(
        contract["schema"]
        == "havenwild.native_editor.stamp_provider_test_contract.v0_1",
        "schema",
    )
    require(contract["pass"] == "167Z92", "pass")
    require(contract["repair"]["runtimeBehaviorChanged"] is False, "no runtime change")
    require(contract["repair"]["lintSuppressionAdded"] is False, "no lint suppression")

    stamps = (ROOT / "crates/haven_assets/src/stamp_registry.rs").read_text(
        encoding="utf-8"
    )
    require(
        "default_registry_preserves_approved_lpc_and_structural_cliff_providers"
        in stamps,
        "current multi-provider test",
    )
    require(
        "default_registry_is_lpc_only_after_asset_policy_reset" not in stamps,
        "retired single-provider test removed",
    )
    require('entry("lpc_pond_grass_bank_a")' in stamps, "LPC pond required")
    require('Some("havenwild_objects")' in stamps, "pond pack identity")
    require('entry("oga_lpc.cliff.ladder")' in stamps, "cliff ladder required")
    require('Some("oga_lpc_cliffs")' in stamps, "cliff pack identity")
    require("replace('\\\\', \"/\")" in stamps, "cross-platform path normalization")
    require("entries().iter().all" not in stamps.split("#[cfg(test)]", 1)[1], "no open-ended sheet assertion")
    require("allow(clippy" not in stamps, "no Clippy suppression")

    pack = json.loads(
        (ROOT / "content/asset_packs/oga_lpc_cliffs/pack.json").read_text(
            encoding="utf-8"
        )
    )
    require(pack["id"] == "oga_lpc_cliffs", "cliff pack exists")
    require(pack["license"]["production_approved"] is True, "cliff license approved")

    current = (
        ROOT / "docs/archive/pass_history/PASS167Z92_NATIVE_EDITOR_STAMP_PROVIDER_TEST_CONTRACT.md"
    ).read_text(encoding="utf-8")
    require("multi-provider" in current, "current-pass explanation")

    roadmap = (
        ROOT
        / "docs/roadmaps/NATIVE_EDITOR_STAMP_PROVIDER_TEST_CONTRACT_PASS167Z92.md"
    ).read_text(encoding="utf-8")
    require("continuous Alderreach World Editor" in roadmap, "next editor lane")

    print("Pass167Z92 native editor stamp-provider test contract validation passed")


if __name__ == "__main__":
    main()
