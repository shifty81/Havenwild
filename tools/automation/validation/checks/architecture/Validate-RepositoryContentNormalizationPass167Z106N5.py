#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8-sig"))


def text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8-sig")


def sha256(path: str) -> str:
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def png_size(path: str) -> tuple[int, int]:
    data = (ROOT / path).read_bytes()[:24]
    require(data[:8] == b"\x89PNG\r\n\x1a\n", f"not a PNG: {path}")
    require(data[12:16] == b"IHDR", f"PNG missing IHDR: {path}")
    return struct.unpack(">II", data[16:24])


def scan_active_for(tokens: list[str]) -> list[str]:
    hits: list[str] = []
    roots = [ROOT / "apps", ROOT / "crates", ROOT / "content", ROOT / "tools/automation"]
    suffixes = {".rs", ".py", ".json", ".md", ".csv", ".ps1", ".sh", ".toml", ".txt", ".js", ".mjs"}
    for base in roots:
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in suffixes:
                continue
            rel = path.relative_to(ROOT)
            if "archive" in rel.parts:
                continue
            if rel.as_posix() in {
                "content/architecture/repository_content_normalization_v0_1.json",
                "tools/automation/validation/checks/architecture/Validate-RepositoryContentNormalizationPass167Z106N5.py",
            }:
                continue
            if path.stat().st_size > 8_000_000:
                continue
            try:
                content = path.read_text(encoding="utf-8-sig")
            except (UnicodeDecodeError, OSError):
                continue
            for token in tokens:
                if token in content:
                    hits.append(f"{rel.as_posix()}: {token}")
    return hits


def main() -> int:
    policy = load("content/architecture/repository_content_normalization_v0_1.json")
    require(policy["canonicalPaths"]["animations"] == "content/animations/", "animation canonical root regressed")
    require(policy["canonicalPaths"]["worldgenPacks"] == "content/worldgen/packs/", "worldgen-pack canonical root regressed")
    require(policy["documentationPolicy"]["currentDirectoryContainsCurrentStateOnly"] is True, "docs/current policy regressed")
    require(policy["foreignProjectPolicy"]["open2dSourceAllowedInHavenwild"] is False, "Open2D foreign-source boundary regressed")

    current_files = {p.name for p in (ROOT / "docs/current").iterdir() if p.is_file()}
    expected_current = {
        "README.md",
        "CURRENT_SOURCE_HANDOFF.md",
        "ROADMAP.md",
        "DEVELOPMENT_LAYOUT.md",
        "ROOT_LAYOUT.md",
        "SOURCE_ONLY_BOOTSTRAP.md",
        "SOURCE_PACKAGING.md",
        "VALIDATION_ARCHITECTURE.md",
    }
    require(current_files == expected_current, f"docs/current is not normalized: {sorted(current_files)}")
    require(not list((ROOT / "docs/current").glob("PASS*.md")), "historical pass docs remain under docs/current")
    require((ROOT / "docs/archive/pass_history/PASS167Z106N4_CORE_UI_WORLD_BUILDER_DECOMPOSITION.md").is_file(), "N4 pass history was not archived")
    source_truth = text("docs/source_of_truth/HAVENWILD_PROJECT_SOURCE_OF_TRUTH_REGENERATED.md")
    require(
        "Pass167Z106N5" in source_truth
        and "Pass167Z59" in source_truth
        and "Normalization milestone" in source_truth,
        "source of truth no longer preserves the N5 normalization/baseline authority",
    )
    require("Open2D Foundry" not in source_truth and "Travellers Rest-inspired" not in source_truth, "foreign/obsolete product source-of-truth content remains")

    # Canonical content paths must exist; retired live roots must be absent.
    for path in [
        "content/animations/animation_catalog_v0_1.json",
        "content/animations/animation_socket_table_v0_10.csv",
        "content/animations/character_animation_contract_v0_10.json",
        "content/worldgen/packs/worldgen_open_world_v0_1.json",
        "content/worldgen/packs/worldgen_open_world_test_v0_12.json",
    ]:
        require((ROOT / path).is_file(), f"missing canonical content path: {path}")
    for retired in ["content/animation", "content/packs", "web/editor", "archive/source/legacy_cpp_shell", "tools/automation/archive/foreign_open2d_menu"]:
        require(not (ROOT / retired).exists(), f"retired path still exists: {retired}")

    stale = scan_active_for(["content/animation/", "content/packs/worldgen_", "web/editor/"])
    require(not stale, "active source still references retired paths:\n" + "\n".join(stale[:30]))

    build_sh = text("tools/build/Build.sh")
    build_ps = text("tools/build/Build.ps1")
    require("web_check\n    build_apps" not in build_sh, "Build All still invokes legacy browser-editor validation")
    require("; Test-Web; Build-ApplicationBinaries" not in build_ps, "PowerShell Build All still invokes legacy browser-editor validation")
    require((ROOT / "archive/source/legacy_web_editor/README.md").is_file(), "legacy browser editor archive missing")

    require((ROOT / "content/build/archive/validator_registry_v2.json").is_file(), "old validator registry not archived")
    require((ROOT / "content/build/archive/generated_output_registry_v1.json").is_file(), "old output registry not archived")
    require(not (ROOT / "content/build/validator_registry_v2.json").exists(), "old validator registry remains active")
    require(not (ROOT / "content/build/generated_output_registry_v1.json").exists(), "old output registry remains active")
    inventory = load("content/build/validation_check_inventory_v0_1.json")
    require(inventory["policy"]["registeredValidatorsAreCurrentAuthority"] is True, "validator authority inventory regressed")

    generated = load("content/architecture/generated_data_ownership_v0_1.json")
    roots = {entry["path"]: entry for entry in generated["roots"]}
    require(roots["assets/generated"]["packagePolicy"] == "include", "runtime generated assets package policy regressed")
    require(roots["WORKSPACE/generated"]["packagePolicy"] == "exclude", "WORKSPACE generated cache policy regressed")
    rollup = load("content/architecture/chatgpt_source_rollup_policy_v0_1.json")
    require("WORKSPACE/generated/" in rollup["excludePrefixes"], "compact rollup still packages WORKSPACE/generated")
    package_ps = text("tools/control/PackageProject.ps1")
    for token in ["'WORKSPACE/generated'", "'WORKSPACE/test-output'", "'WORKSPACE/saves'", "'WORKSPACE/recovery'"]:
        require(token in package_ps, f"complete package exclusions missing {token}")
    tools_ps = text("tools/control/HavenwildTools.ps1")
    root_cmd = text("HavenwildTools.cmd")
    cleanup_ps = text("tools/control/ApplyPatchRemovals.ps1")
    require("manifests\\removals\\PATCH_REMOVALS.txt" in tools_ps, "HavenwildTools no longer detects cumulative patch removals")
    require("Patch cleanup was deferred" in tools_ps and "StartupWarnings" in tools_ps, "patch cleanup can terminate the control center again")
    require("APPLY_HAVENWILD_PATCH.cmd" in tools_ps and "APPLY_HAVENWILD_PATCH.md" in tools_ps, "package-only root helpers are no longer auto-cleaned after success")
    require("pause" in root_cmd.lower() and "failed to start or exited with code" in root_cmd.lower(), "root launcher can silently flash-close on bootstrap failure")
    require("Sort-Object -Property" in cleanup_ps and "failures" in cleanup_ps, "removal helper is not ordered/failure-aware")
    for bootstrap in ["HavenwildTools.cmd", "tools/control/HavenwildTools.ps1", "tools/control/ApplyPatchRemovals.ps1", "tools/control/ProjectCommandRegistry.ps1"]:
        require(bootstrap in package_ps, f"patch packager no longer forces bootstrap file: {bootstrap}")
    require("PATCH_REMOVALS.txt" in package_ps, "patch packager no longer emits its transport removal manifest")
    removal_manifest = ROOT / "manifests/removals/PASS167Z106N5_REPOSITORY_NORMALIZATION_REMOVALS.txt"
    require(removal_manifest.is_file(), "N5 intentional-removal audit manifest missing")
    removal_paths = [line.strip() for line in removal_manifest.read_text(encoding="utf-8").splitlines() if line.strip()]
    require(len(removal_paths) == 177, f"N5 intentional-removal path count changed: {len(removal_paths)}")
    require("content/animation/animation_socket_table_v0_10.csv" in removal_paths, "old animation root missing from N5 removal audit")
    require("web/editor/README.md" in removal_paths, "legacy browser editor missing from N5 removal audit")

    family = load("content/assets/lpc/victorian_building_source_family_v0_1.json")
    require(family["licenseRoute"]["selected"] == "CC-BY-SA-3.0", "Victorian family license route regressed")
    require(family["authoringPolicy"]["sourceGridIsNotWorldFootprint"] is True, "Victorian source-grid/footprint separation regressed")
    require(family["authoringPolicy"]["arbitrary32x32ChopForbidden"] is True, "Victorian arbitrary 32x32 chopping became allowed")
    expected = {
        "content/assets/lpc/source/victorian-buildings/victorian-mansion.png": ((1024, 2048), "69459d03fd1a4cefaa10df02fd3fc6cc0bd42b9661207327947ca176bea52c38"),
        "content/assets/lpc/source/victorian-buildings/victorian-tenement.png": ((682, 2048), "bcf5f743b7dc966261ca86490391a01a51d98afd97b8da5f27174aa88bd0b8ff"),
        "content/assets/lpc/source/victorian-buildings/victorian-accessories.png": ((819, 2048), "83e2e18eaf13d5ad3fd46c1fc812b7ba9b8a565fa632b3c459ca130ecdeba69b"),
        "content/assets/lpc/source/victorian-buildings/victorian-windows-doors.png": ((409, 2048), "e3369e867359610db7eea84e9d48ac67a63306ae8d44ab5b2b261d226cd06bba"),
    }
    for path, (size, digest) in expected.items():
        require((ROOT / path).is_file(), f"Victorian source missing: {path}")
        require(png_size(path) == size, f"Victorian source dimensions changed: {path}")
        require(sha256(path) == digest, f"Victorian source hash changed: {path}")
    require(sha256("content/assets/lpc/source/victorian-buildings/CREDITS-victorian.txt") == "2ca953ab1a6df842a41db13eada815c1761cf5336eba3f17293440d3e11a0690", "Victorian supplied credits changed")
    pack = load("content/asset_packs/lpc_victorian_buildings/pack.json")
    require(pack["production_enabled"] is False, "uncertified Victorian source family became runtime enabled")
    require(pack["license"]["license_id"] == "CC-BY-SA-3.0", "Victorian pack license route regressed")
    require(all(source.get("tile_size") is None for source in pack["sources"] if source["kind"] == "raw_sheet"), "Victorian raw sheets were incorrectly forced to a uniform tile size")

    tool_registry = load("tools/tool_registry.json")
    require(all("Open2D" not in entry.get("path", "") and "foreign_open2d" not in entry.get("path", "") for entry in tool_registry["entries"]), "foreign Open2D tool remains registered")

    print("Repository/content/documentation normalization validated")
    print(f"- current docs: {len(current_files)}")
    print("- canonical animation root: content/animations")
    print("- canonical worldgen-pack root: content/worldgen/packs")
    print("- legacy browser editor archived and removed from Build All")
    print("- WORKSPACE/generated classified as reproducible non-package cache")
    print("- cumulative patch removals: automatic and root-clean, 177 intentional retired paths")
    print("- Victorian source family: 4 exact multi-cell source sheets, runtime promotion disabled")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
