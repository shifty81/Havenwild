#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load(rel: str):
    return json.loads((ROOT / rel).read_text(encoding="utf-8-sig"))


def line_count(rel: str) -> int:
    return len((ROOT / rel).read_text(encoding="utf-8").splitlines())


def main() -> int:
    domain = load("content/architecture/master_domain_registry_v0_1.json")
    require(domain["revision"].startswith("167Z109Q"), "master domain registry is not Q authority")
    require(domain["policy"]["domainCount"] == 7, "normalization must stay at seven project foundations")
    require(len(domain["domains"]) == 7, "domain registry count drifted")
    require(domain["policy"]["noFeatureSpecificFrameworks"] is True, "scope guard regressed")

    current = ROOT / "docs/current"
    expected = {
        "README.md", "CURRENT_SOURCE_HANDOFF.md", "ROADMAP.md", "DEVELOPMENT_LAYOUT.md",
        "ROOT_LAYOUT.md", "SOURCE_ONLY_BOOTSTRAP.md", "SOURCE_PACKAGING.md", "VALIDATION_ARCHITECTURE.md",
    }
    require({p.name for p in current.iterdir() if p.is_file()} == expected, "docs/current must contain exactly eight current-state documents")
    require(not list(current.glob("PASS*.md")), "historical pass documents returned to docs/current")

    for retired in [
        "content/animation", "content/packs", "web/editor",
        "content/build/validator_registry_v2.json", "content/build/generated_output_registry_v1.json",
    ]:
        require(not (ROOT / retired).exists(), f"retired path still active: {retired}")

    split_files = [
        "crates/haven_game/src/runtime_world_map.rs",
        "crates/haven_game/src/runtime_world_map_game.rs",
        "crates/haven_game/src/runtime_world_map_helpers.rs",
        "crates/haven_game/src/runtime_surface_streaming.rs",
        "crates/haven_game/src/runtime_surface_streaming_residency.rs",
        "crates/haven_game/src/runtime_surface_streaming_structural.rs",
        "crates/haven_game/src/client_character_frontend_draw.rs",
        "crates/haven_game/src/client_character_frontend_preview.rs",
        "crates/haven_game/src/client_character_frontend_chrome.rs",
        "crates/haven_game/src/client_character_frontend_layout.rs",
        "crates/haven_world/src/island_pcg.rs",
        "crates/haven_world/src/island_pcg_tests.rs",
    ]
    for rel in split_files:
        require((ROOT / rel).is_file(), f"missing extracted source unit: {rel}")
        require(line_count(rel) <= 750, f"extracted source unit exceeds 750 lines: {rel}")

    registry = load("content/build/validator_registry_v3.json")
    source = [entry for entry in registry["validators"] if "source" in entry.get("profiles", [])]
    build = [entry for entry in registry["validators"] if "build" in entry.get("profiles", [])]
    require(len(source) == 10, f"source validation profile must contain 10 current-authority checks, got {len(source)}")
    require(len(build) == 2, f"build validation profile must contain 2 checks, got {len(build)}")
    require(registry["policy"]["sourceValidationValidatorCount"] == 10, "registry source count policy drifted")

    manifest = load("content/validation/validation_manifest_v1.json")
    require(manifest["policy"]["sourceValidationValidatorCount"] == 10, "validation manifest source count drifted")
    require(manifest["policy"]["normalBuildValidatorCount"] == 2, "validation manifest build count drifted")

    diagnostic = (ROOT / "crates/haven_game/src/runtime_diagnostics.rs").read_text(encoding="utf-8")
    require("Pass 167Z109Q" in diagnostic, "runtime diagnostic checkpoint not advanced to Q")

    print("Pass167Z109Q normalization A validated")
    print("- seven-domain ownership registry: present")
    print("- docs/current: exactly eight current-state documents")
    print("- retired duplicate/browser roots: absent")
    print("- architecture extraction units: all <= 750 lines")
    print("- validation profiles: build=2, source=10")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Pass167Z109Q validation FAILED: {exc}")
        raise SystemExit(1)
