#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"FAILED Pass167Z105A Rust format stability: {message}")


def main() -> None:
    contract = json.loads(
        (ROOT / "content/build/rust_format_stability_v167z105a.json").read_text(encoding="utf-8")
    )
    require(contract["schema"] == "havenwild.build.rust_format_stability.v167z105a", "contract schema")
    require(contract["pass"] == "167Z105A", "contract pass")
    require(contract["policy"]["normalizeBeforeReadOnlyValidation"] is True, "pre-validation normalization")
    require(contract["policy"]["normalizeAfterReadOnlyValidation"] is True, "post-validation normalization")
    require(contract["policy"]["strictFormatCheckAfterSecondNormalization"] is True, "strict fmt gate")
    require(contract["policy"]["sourceRewritersRemainDisabled"] is True, "source rewriters remain disabled")

    build = (ROOT / "tools/build/Build.sh").read_text(encoding="utf-8")
    require("normalize_rust_source_after_validation()" in build, "post-validation normalizer function")
    require('run_step "re-normalize Rust formatting after read-only validation" cargo fmt --all' in build, "post-validation cargo fmt command")
    require('run_step "cargo fmt --all -- --check" cargo fmt --all -- --check' in build, "strict cargo fmt check remains")
    require("Active Rust sources are authoritative; legacy build-time source rewriters are disabled" in build, "legacy source rewriters remain disabled")

    for command in ("dev", "all"):
        marker = f"  {command})"
        start = build.index(marker)
        end = build.index("    ;;", start)
        block = build[start:end]
        validate_at = block.index("validate_current_capabilities build")
        renormalize_at = block.index("normalize_rust_source_after_validation")
        rust_at = min(
            pos for token in ("rust_check", "rust_all")
            if (pos := block.find(token)) >= 0
        )
        require(validate_at < renormalize_at < rust_at, f"{command} post-validation normalization ordering")

    require("rust) ensure_lpc_dependency; ensure_direct_lpc_compatibility_assets; normalize_rust_source; validate_current_capabilities build; normalize_rust_source_after_validation; rust_all ;;" in build, "rust command ordering")
    require("check) normalize_rust_source; validate_current_capabilities build; normalize_rust_source_after_validation; rust_check ;;" in build, "check command ordering")

    address = (ROOT / "crates/haven_editor/src/world_surface_edit/address.rs").read_text(encoding="utf-8")
    normalized = """            let address =\n                resolve_world_surface_cell(manifest, assignments, world, landmass_id, global)\n                    .map_err(|error| {\n                        format!(\n"""
    stale = """            let address = resolve_world_surface_cell(\n                manifest,\n                assignments,\n                world,\n                landmass_id,\n                global,\n            )\n            .map_err(|error| {\n                format!(\n"""
    require(normalized in address, "address.rs carries workstation rustfmt-normalized shape")
    require(stale not in address, "stale pre-rustfmt address.rs shape absent")

    cmd = (ROOT / "tools/build/Build.cmd").read_text(encoding="utf-8")
    require('"%BASH_EXE%" "./tools/build/Build.sh" %*' in cmd, "Windows launcher still routes through Bash authority")
    print("Pass167Z105A Rust format stability validation passed")


if __name__ == "__main__":
    main()
