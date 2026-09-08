from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
checks = {
    "apps/haven_editor_native/src/app/canvas_layers.rs": ["canvas_overlay_surface_rect", "W72A: rulers are overlays too"],
    "apps/haven_editor_native/src/app/canvas_controller.rs": ["Scene owns the complete CanvasWorkspace surface", "World owns the complete CanvasWorkspace surface"],
    "apps/haven_editor_native/src/app/pixel_studio_render.rs": ["pixel_context_toolbar_rect", "There is no full-width separator toolbar"],
    "apps/haven_editor_native/src/app/pixel_studio_layout.rs": ["canvas.y - 30.0"],
    "apps/haven_editor_native/src/app/autotile_authoring.rs": ["host.y + host.h - 36.0"],
}
errors=[]
if (ROOT/'content/editor/gui/canvas_chrome_alignment_w72d_v1.json').exists():
    layers=(ROOT/'apps/haven_editor_native/src/app/canvas_layers.rs').read_text(encoding='utf-8')
    controller=(ROOT/'apps/haven_editor_native/src/app/canvas_controller.rs').read_text(encoding='utf-8')
    view=(ROOT/'apps/haven_editor_native/src/app/canvas_view.rs').read_text(encoding='utf-8')
    for marker in ['W72D locked GUI geometry: Tool Rail is a dedicated left column outside',
                   'W72D locked GUI geometry: Layers is the dedicated panel immediately to']:
        if marker not in layers: errors.append('W72D superseding geometry missing: '+marker)
    if 'rect.x + left' not in controller: errors.append('W72D dedicated canvas inset missing')
    if 'retired compatibility shim' not in view: errors.append('W72D legacy toolbar retirement missing')
    if errors:
        print('FAIL: W72A historical validator under W72D')
        for e in errors: print(' - '+e)
        raise SystemExit(1)
    print('PASS: W72A historical geometry superseded by locked W72D sibling chrome')
    raise SystemExit(0)
for rel, markers in checks.items():
    text=(ROOT/rel).read_text(encoding="utf-8")
    for marker in markers:
        if marker not in text:
            errors.append(f"{rel} missing marker: {marker}")
controller=(ROOT/"apps/haven_editor_native/src/app/canvas_controller.rs").read_text(encoding="utf-8")
for bad in ("host.y + 98.0", "host.y + 62.0"):
    if bad in controller:
        errors.append(f"legacy reserved canvas offset remains: {bad}")
pixel=(ROOT/"apps/haven_editor_native/src/app/pixel_studio_render.rs").read_text(encoding="utf-8")
if "host.h - 68.0 - SPRITE_BOTTOM_DOCK_HEIGHT" in pixel:
    errors.append("Pixel still reserves palette/legacy-toolbar height")
if errors:
    print("FAIL: W72A true in-canvas overlay geometry")
    for e in errors: print(" - "+e)
    raise SystemExit(1)
print("PASS: W72A true in-canvas overlay geometry")
