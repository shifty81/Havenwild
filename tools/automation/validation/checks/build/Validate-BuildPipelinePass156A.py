#!/usr/bin/env python3
from pathlib import Path

root = Path(__file__).resolve().parents[3]
build = (root / "tools/build/Build.sh").read_text(encoding="utf-8")
suites = (root / "tools/automation/validation/run_capability_suites.py").read_text(encoding="utf-8")

for command in ("dev)", "all)", "cargo-only)", "legacy-audit)"):
    assert command in build, f"missing build mode: {command[:-1]}"
assert "run_capability_suites.py" in build
assert "validate_pre_cargo_rust_sources" not in build
assert not build.rstrip().endswith("Validate-VisibleTraversalTelemetryPass153V.py")
for suite in ("assets", "terrain-v7", "water", "character", "worldgen", "saves", "editor-runtime", "architecture", "licenses"):
    assert f'"{suite}"' in suites, f"missing current capability suite: {suite}"
print("Pass 156A OK: current capability suites replace mandatory historical pass gates; dev, all, cargo-only, and legacy-audit modes are available")
