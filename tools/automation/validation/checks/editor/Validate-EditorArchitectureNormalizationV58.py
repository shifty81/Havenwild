#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[5]
errors = []

def read(rel: str) -> str:
    path = ROOT / rel
    if not path.exists():
        errors.append(f"missing {rel}")
        return ""
    return path.read_text(encoding="utf-8")

workspace = read("Cargo.toml")
editor_manifest = read("crates/haven_editor/Cargo.toml")
render_manifest = read("crates/haven_render/Cargo.toml")
net_manifest = read("crates/haven_net/Cargo.toml")
authoring = read("crates/haven_authoring/src/lib.rs")
editor_command_shim = read("crates/haven_editor/src/command_bus.rs")
native_main = read("apps/haven_editor_native/src/main.rs")
app_mod = read("apps/haven_editor_native/src/app/mod.rs")
readme = read("README.md")

checks = [
    ('"apps/haven_editor_native"', workspace, "native editor app missing from workspace"),
    ('"crates/haven_authoring"', workspace, "headless authoring crate missing from workspace"),
    ('autobins = false', editor_manifest, "haven_editor still auto-builds a UI binary"),
    ('haven_authoring', editor_manifest, "haven_editor does not consume neutral authoring contracts"),
    ('haven_authoring', render_manifest, "renderer does not consume neutral authoring diagnostics"),
    ('haven_authoring', net_manifest, "networking does not consume neutral authoring commands"),
    ('pub mod command_bus;', authoring, "authoring command contract module missing"),
    ('pub mod diagnostics;', authoring, "authoring diagnostics module missing"),
    ('pub mod selection;', authoring, "authoring selection groundwork missing"),
    ('pub use haven_authoring', editor_command_shim, "editor command compatibility re-export missing"),
    ('mod canvas_controller;', app_mod, "native canvas controller module missing"),
    ('mod scene_authoring;', app_mod, "native scene authoring module missing"),
    ('cargo run -p haven_editor_native', readme, "README does not name the normalized editor app package"),
]
for needle, text, message in checks:
    if needle not in text:
        errors.append(message)

if 'haven_editor' in render_manifest:
    errors.append('haven_render still depends on the editor UI crate')
if 'haven_editor' in net_manifest:
    errors.append('haven_net still depends on the editor UI crate')
if 'macroquad.workspace' in editor_manifest:
    errors.append('headless haven_editor still depends on Macroquad')
if len(native_main.splitlines()) > 150:
    errors.append('native editor main.rs is not thin')
for rel in [
    'crates/haven_editor/src/main.rs',
    'crates/haven_editor/src/canvas_camera.rs',
    'crates/haven_editor/src/canvas_view.rs',
]:
    if (ROOT / rel).exists():
        errors.append(f'legacy native host path still exists: {rel}')

if errors:
    print('Editor architecture normalization validation failed:')
    for error in errors:
        print(' -', error)
    sys.exit(1)
print('Editor architecture normalization validation passed.')
