from pathlib import Path
import sys

root = Path(__file__).resolve().parents[5]
def read(rel):
    return (root / rel).read_text(encoding='utf-8')

app = '\n'.join(read(rel) for rel in [
    'apps/haven_editor_native/src/app/mod.rs',
    'apps/haven_editor_native/src/app/input.rs',
    'apps/haven_editor_native/src/app/canvas_controller.rs',
    'apps/haven_editor_native/src/app/draw.rs',
    'apps/haven_editor_native/src/app/scene_authoring.rs',
    'apps/haven_editor_native/src/app/scene_bank_workspace.rs',
    'apps/haven_editor_native/src/app/island_authoring.rs',
    'apps/haven_editor_native/src/app/world_canvas_context.rs',
    'apps/haven_editor_native/src/app/world_surface_authoring_ui.rs',
])
canvas = read('apps/haven_editor_native/src/app/canvas_view.rs')
world_surface = read('apps/haven_editor_native/src/app/world_surface_editor.rs')
camera = read('apps/haven_editor_native/src/app/canvas_camera.rs')
checks = {
    'clipped persistent world canvas': (
        'world_canvas: CanvasCameraState' in app
        and 'camera.viewport = Some' in camera
        and 'draw_scene_rectangle_map' in world_surface
    ),
    'world canvas context click handler': 'fn handle_world_canvas_context_click' in app,
    'canonical world properties routing': ('handle_world_properties_click' in app and 'RightDockTab::Properties' in app),
    'overworld filter helper': 'fn rectangle_is_overworld_surface' in world_surface,
    'dedicated scene bank workspace': 'EditorViewportMode::SceneBank' in app and 'draw_scene_bank_workspace' in app,
    'actual scene thumbnails': 'pub(crate) fn draw_scene_into_rect' in canvas and 'draw_scene_into_rect(scene, preview)' in app,
    'candidate assign widgets': 'Generate from selected template' in app and 'Generate this scene' in app and 'Clear assignment' in app,
    'contract json': (root / 'content/editor/world_canvas/world_canvas_scene_bank_contract_v0_1.json').exists(),
    'docs': (root / 'docs/editor/WORLD_CANVAS_SCENE_BANK_PASS44.md').exists(),
}
failed = [name for name, ok in checks.items() if not ok]
if failed:
    print('World canvas scene-bank validation failed:')
    for name in failed:
        print(' -', name)
    sys.exit(1)
print('World canvas scene-bank validation passed.')
