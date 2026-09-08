#!/usr/bin/env python3
"""Validate Pass 167Z47 frontend/runtime Rust type repair and migration idempotence."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
REPAIR = ROOT / "tools/automation/project/Repair-FrontendRuntimeSurfaceV167Z46.py"


def require(path: Path, *needles: str) -> list[str]:
    errors: list[str] = []
    if not path.is_file():
        return [f"missing {path.relative_to(ROOT).as_posix()}"]
    text = path.read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text:
            errors.append(f"{path.relative_to(ROOT).as_posix()}: missing {needle}")
    return errors


def write_fixture(root: Path) -> None:
    files = {
        "crates/haven_game/src/client_character_frontend_draw.rs": """
use macroquad::prelude::*;
pub(crate) fn mouse_vec() -> Vec2 { vec2(0.0, 0.0) }
""",
        "crates/haven_game/src/character_creator_model.rs": """
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) enum HeadwearKind { None, Hat, Hood }
impl HeadwearKind { pub(crate) fn variant(self) -> &'static str { "none" } }
""",
        "crates/haven_game/src/client_frontend.rs": """
pub(crate) struct ClientFrontend;
""",
        "crates/haven_game/src/runtime_hud.rs": """
use super::*;
fn fixture(appearance: &RuntimeCharacterAppearance) {
    let frame = RuntimeCharacterAppearance::frame(vec2(0.0, 1.0), false, 0.0);
    appearance.draw_portrait(vec2(1.0, 2.0), 64.0, frame);
}
""",
        "crates/haven_game/src/character_runtime_compositor.rs": """
pub(crate) struct RuntimeCharacterAppearance;
impl RuntimeCharacterAppearance {
    pub(crate) fn load_profile_vitals() {}
    pub(crate) fn draw_portrait() {}
}
""",
        "crates/haven_save/src/lib.rs": """
pub struct ClientSavePaths { pub character_links: String }
fn fixture(root: std::path::PathBuf) { let _ = character_links: path_string(root.join("characters")); }
""",
    }
    for relative, text in files.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text.strip() + "\n", encoding="utf-8")


def main() -> int:
    errors: list[str] = []
    errors += require(
        ROOT / "crates/haven_save/src/lib.rs",
        "pub character_links: String",
        'character_links: path_string(root.join("characters"))',
        "create_dir_all(&self.character_links)",
    )
    errors += require(
        ROOT / "crates/haven_game/src/character_runtime_compositor.rs",
        "pub(crate) fn load_profile_vitals",
        "pub(crate) fn draw_portrait",
        'document.get("character_vitals")',
        "let crop_height: f32 = if source.h >= LPC_FRAME_HEIGHT",
    )
    errors += require(
        ROOT / "tools/build/Build.sh",
        "repair_frontend_runtime_surface",
        "Repair-FrontendRuntimeSurfaceV167Z46.py",
    )
    errors += require(
        ROOT / "tools/build/Build.ps1",
        "Repair-FrontendRuntimeSurface",
        "Repair-FrontendRuntimeSurfaceV167Z46.py",
    )
    errors += require(
        REPAIR,
        "repair_main_menu_rects",
        "repair_headwear_helpers",
        "repair_frontend_music_lifecycle",
        "repair_hud_portrait_call",
        "repair_compositor_numeric_types",
    )

    with tempfile.TemporaryDirectory(prefix="havenwild-z46-") as temp:
        fixture = Path(temp)
        write_fixture(fixture)
        command = [sys.executable, str(REPAIR), "--root", str(fixture)]
        first = subprocess.run(command, text=True, capture_output=True, check=False)
        second = subprocess.run(command, text=True, capture_output=True, check=False)
        if first.returncode != 0:
            errors.append(f"fixture repair failed: {first.stdout}{first.stderr}")
        if second.returncode != 0 or "already matches" not in second.stdout:
            errors.append(f"fixture repair was not idempotent: {second.stdout}{second.stderr}")
        if first.returncode == 0:
            draw = (fixture / "crates/haven_game/src/client_character_frontend_draw.rs").read_text()
            model = (fixture / "crates/haven_game/src/character_creator_model.rs").read_text()
            frontend = (fixture / "crates/haven_game/src/client_frontend.rs").read_text()
            hud = (fixture / "crates/haven_game/src/runtime_hud.rs").read_text()
            fixture_checks = {
                "main menu rectangles": all(name in draw for name in ("main_new_rect", "main_load_rect", "main_quit_rect")),
                "headwear cycle and label": "fn cycle" in model and "fn label" in model,
                "headwear nested const type": "const VALUES: &[HeadwearKind] = &[HeadwearKind::None" in model,
                "frontend music hooks": "start_frontend_music" in frontend and "stop_frontend_music" in frontend,
                "five-argument portrait frame": "None" in hud and "0.0" in hud,
                "normalized portrait call": "Rect::new(18.0, screen_height() - 102.0, 76.0, 76.0)" in hud,
            }
            for label, passed in fixture_checks.items():
                if not passed:
                    errors.append(f"fixture did not restore {label}")

    if errors:
        print("Pass 167Z46 frontend/runtime validation FAILED")
        for error in errors:
            print(f"- {error}")
        return 1
    print(json.dumps({
        "schema": "havenwild.frontend_runtime_surface_validation.v167z47",
        "pass": "167Z47",
        "clientSaveCharacterLinks": True,
        "profileVitalsLoader": True,
        "headShoulderPortrait": True,
        "frontendCompatibilityMigration": True,
        "idempotent": True,
        "rustNestedConstTypeSafe": True,
        "portraitCropNumericTypeExplicit": True,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
