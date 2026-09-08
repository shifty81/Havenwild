from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
SCENE_TESTS = ROOT / "crates/haven_editor/src/scene_edit_tests.rs"
SCENE_EDIT = ROOT / "crates/haven_editor/src/scene_edit.rs"


def fail(message: str) -> None:
    print(f"FAILED Pass167Z106N5G editor scene-test map-height import hotfix: {message}")
    raise SystemExit(1)


for path in (SCENE_TESTS, SCENE_EDIT):
    if not path.is_file():
        fail(f"missing {path.relative_to(ROOT)}")

scene_tests = SCENE_TESTS.read_text(encoding="utf-8")
scene_edit = SCENE_EDIT.read_text(encoding="utf-8")

if "use haven_core::{SceneId, MAP_H};" not in scene_tests:
    fail("scene_edit_tests.rs must explicitly import SceneId and MAP_H")
if scene_tests.count("MAP_H as i32") < 2:
    fail("scene_edit regression tests no longer exercise the vertical MAP_H boundary")
if "MAP_H, MAP_W" in scene_edit or "MAP_H," in scene_edit:
    fail("production scene_edit.rs must not regain the stale MAP_H import")

print("Pass167Z106N5G editor scene-test map-height import hotfix validated")
