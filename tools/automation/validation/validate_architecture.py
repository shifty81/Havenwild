#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CONFIG = ROOT / "content/architecture/rust_file_size_allowlist.json"


def line_count(path: Path) -> int:
    return len(path.read_text(encoding="utf-8", errors="strict").splitlines())


def fail(message: str, issues: list[str]) -> None:
    issues.append(message)


def main() -> int:
    issues: list[str] = []
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    default_limit = int(config["default_max_lines"])
    entrypoint_limit = int(config["entrypoint_max_lines"])
    exceptions = {entry["path"]: entry for entry in config.get("exceptions", [])}

    rust_files = sorted((ROOT / "crates").rglob("*.rs")) + sorted((ROOT / "apps").rglob("*.rs"))
    for path in rust_files:
        rel = path.relative_to(ROOT).as_posix()
        source = path.read_text(encoding="utf-8", errors="strict")
        for line_number, line in enumerate(source.splitlines(), start=1):
            if "/\\" in line or "\\/" in line:
                fail(
                    f"{rel}:{line_number} contains a mixed-separator path; use repository-relative forward slashes",
                    issues,
                )
        count = len(source.splitlines())
        exception = exceptions.get(rel)
        limit = int(exception["max_lines"]) if exception else default_limit
        if path.name == "main.rs" and exception is None:
            limit = min(limit, entrypoint_limit)
        if count > limit:
            fail(f"{rel} has {count} lines; limit {limit}", issues)

    for rel, entry in exceptions.items():
        path = ROOT / rel
        if not path.exists():
            fail(f"stale size exception references missing file: {rel}", issues)
            continue
        if not str(entry.get("reason", "")).strip():
            fail(f"size exception has no reason: {rel}", issues)
        target = int(entry.get("target_lines", entry["max_lines"]))
        if target > int(entry["max_lines"]):
            fail(f"size exception target exceeds temporary maximum: {rel}", issues)

    workspace = (ROOT / "Cargo.toml").read_text(encoding="utf-8")
    required_members = [
        '"apps/haven_editor_native"',
        '"crates/haven_authoring"',
        '"crates/haven_editor"',
    ]
    for member in required_members:
        if member not in workspace:
            fail(f"workspace missing member {member}", issues)

    editor_manifest = (ROOT / "crates/haven_editor/Cargo.toml").read_text(encoding="utf-8")
    if "autobins = false" not in editor_manifest:
        fail("haven_editor must be a headless library crate with autobins disabled", issues)
    if "macroquad.workspace" in editor_manifest:
        fail("haven_editor must not depend on Macroquad/windowing", issues)

    for crate in ("haven_render", "haven_net"):
        manifest = (ROOT / f"crates/{crate}/Cargo.toml").read_text(encoding="utf-8")
        if "haven_editor" in manifest:
            fail(f"{crate} must not depend on haven_editor", issues)
        if "haven_authoring" not in manifest:
            fail(f"{crate} must consume neutral haven_authoring contracts", issues)

    native_main = ROOT / "apps/haven_editor_native/src/main.rs"
    if line_count(native_main) > entrypoint_limit:
        fail("native editor main.rs exceeds entrypoint limit", issues)

    forbidden_old_host_files = [
        ROOT / "crates/haven_editor/src/main.rs",
        ROOT / "crates/haven_editor/src/canvas_camera.rs",
        ROOT / "crates/haven_editor/src/canvas_view.rs",
    ]
    for path in forbidden_old_host_files:
        if path.exists():
            fail(f"native editor host file still exists in headless crate: {path.relative_to(ROOT)}", issues)

    required_native_modules = [
        "apps/haven_editor_native/src/app/mod.rs",
        "apps/haven_editor_native/src/app/input.rs",
        "apps/haven_editor_native/src/app/canvas_controller.rs",
        "apps/haven_editor_native/src/app/draw.rs",
        "apps/haven_editor_native/src/app/scene_authoring.rs",
        "apps/haven_editor_native/src/app/canvas_camera.rs",
        "apps/haven_editor_native/src/app/canvas_view.rs",
        "apps/haven_editor_native/src/app/asset_palette_panel.rs",
        "apps/haven_editor_native/src/app/atlas_render.rs",
    ]
    for rel in required_native_modules:
        if not (ROOT / rel).exists():
            fail(f"missing native editor module {rel}", issues)

    if issues:
        print("Architecture validation FAILED")
        for issue in issues:
            print(f"- {issue}")
        return 1

    print(f"Architecture validation passed ({len(rust_files)} Rust files checked)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
