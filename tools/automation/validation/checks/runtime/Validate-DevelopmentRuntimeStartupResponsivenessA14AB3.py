#!/usr/bin/env python3
"""Validate development runtime startup stays visible and avoids full-world synchronous structural bake."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[5]
client = (ROOT / "crates/haven_game/src/client_entry.rs").read_text(encoding="utf-8")
residency = (ROOT / "crates/haven_game/src/runtime_surface_streaming_residency.rs").read_text(encoding="utf-8")
bootstrap = (ROOT / "crates/haven_game/src/game_bootstrap.rs").read_text(encoding="utf-8")
build = (ROOT / "tools/build/Build.sh").read_text(encoding="utf-8")
errors = []

for marker in [
    "draw_runtime_startup_stage(",
    '"Opening Development World"',
    '"Preparing local terrain, structures, and spawn..."',
    '"Runtime startup phase: assets',
    "game.prepare_initial_surface_structures();",
]:
    if marker not in client:
        errors.append(f"client startup is missing marker: {marker}")

if "game.rebuild_active_surface_structures();" in client:
    errors.append("client startup still performs direct full-world synchronous structural rebuild")

for marker in [
    "pub(super) fn prepare_initial_surface_structures(&mut self)",
    "self.active_surface_chunk_coord().is_some()",
    "self.surface_chunks.structural_rebuild_needed = true;",
    "self.update_surface_chunk_jobs();",
    'full-world synchronous structural bake skipped',
]:
    if marker not in residency:
        errors.append(f"residency startup authority is missing marker: {marker}")

# Preserve compatibility for genuinely non-streamed/legacy exterior scenes.
if "self.rebuild_active_surface_structures();" not in residency:
    errors.append("non-streamed compatibility structural rebuild fallback was removed")

for marker in [
    "Runtime bootstrap timing: load startup world",
    "Runtime bootstrap timing: content authority",
    "Runtime bootstrap timing: building placement/interior authority",
    "Runtime bootstrap timing: active-scene autotile cache",
]:
    if marker not in bootstrap:
        errors.append(f"runtime bootstrap timing is missing marker: {marker}")

if "Validate-DevelopmentRuntimeStartupResponsivenessA14AB3.py" not in build:
    errors.append("A14AB3 runtime startup responsiveness validator is not registered in Full Quality Gate")

if errors:
    print("A14AB3 Development Runtime Startup Responsiveness validation FAILED")
    for error in errors:
        print(f"- {error}")
    sys.exit(1)

print("PASS: A14AB3 development runtime startup responsiveness")
