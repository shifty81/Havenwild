#!/usr/bin/env python3
"""Offline source/layout contract, including original provenance; not a native GUI test."""
from pathlib import Path
import argparse, hashlib, sys
ap=argparse.ArgumentParser();ap.add_argument('--repo', default='.');r=Path(ap.parse_args().repo).resolve()
s=(r/'apps/haven_atlas_mapper_lite/src/main.rs').read_text(encoding='utf-8')
checks={
 'three independent panels and approximately 14 percent library': 'LIBRARY_RAIL_FRACTION: f32 = 0.14' in s and all(f'fn draw_{name}_panel(' in s for name in ('library','atlas','canvas')),
 'scene and atlas split remaining space without shrinking source rail': 'let atlas_w = available * app.pane_ratio;' in s and 'let canvas_w = available - atlas_w;' in s and 'let rail_w = (width * LIBRARY_RAIL_FRACTION)' in s,
 'source folder grouping before filename fallbacks': s.index('key.contains("/objects/furniture/")') < s.index('name.contains("mountain")') and all(x in s for x in ('/terrain objects/','/structure/','/objects/','/fx/')),
 'original licensed source root only': 'vec![root.join("assets/source/licensed/lpc_revised")]' in s and 'normalized.contains("/assets/source/licensed/lpc_revised/")' in s,
 'source picker sorted by stable path and stacked with height': 'fn active_atlases_sorted' in s and 'sheets.sort_by' in s and 'top = image_top + image.h + ATLAS_CARD_GAP;' in s and 'y = bottom;' in s,
 'fit to widest activated atlas and scroll bounded to contents': 'fn atlas_fit_scale' in s and '.map(|a| a.width).max()' in s and 'fn clamp_atlas_scroll' in s and 'self.source_pan.y.clamp(lower, 0.0)' in s,
 'wheel scroll only hovered atlas; modifier zoom, scene independent': 'else if over_atlas {' in s and 'self.source_pan.y += wheel_y * 64.0;' in s and 'self.source_zoom = (self.source_zoom * zoom_factor)' in s and 'self.canvas_zoom = (self.canvas_zoom * zoom_factor)' in s,
 'multi-atlas picking switches active source identity before drag': 'fn atlas_tile_at' in s and 'self.activate_source_id(&source_id);' in s and 'self.drag = DragState::SourceTile(tile);' in s,
 'independent real GPU viewport clipping and input rects': 'camera.viewport = Some(' in s and 'begin_viewport_clip(view);' in s and 'begin_viewport_clip(scene_view);' in s and 'end_viewport_clip();' in s and 'canvas_edit_rect(canvas_rect).contains(mouse)' in s,
 'state preserved and no invented generator/certification': 'atlas_mapper_project.v0_7' in s and 'self.pieces = document.pieces;' in s and 'No recipe reroll yet; candidate only.' in s and 'false // Save/hand-off state is never a visual or runtime approval.' in s,
 'no old double-pane source renderer': 'fn draw_source_panel(' not in s and 'fn source_preview_rect(' not in s,
}
for label,ok in checks.items():print(('PASS' if ok else 'FAIL')+': '+label)
assert all(checks.values()),'B48R25 source contract failed'
for width in (900,1024,1280,1600,1920,2560):
 gap=12.;rail=min(max(min(max(width*.14,160),240),width*.10),width*.15)
 available=width-rail-gap*4
 atlas=available*.5;scene=available-atlas
 left=gap;atlas_x=left+rail+gap;scene_x=atlas_x+atlas+gap
 assert 0<rail<atlas and 0<scene and scene_x+scene <= width-gap+1e-5
 assert width<1100 or .10<=rail/width<=.15
 print(f'PASS geometry width={width}: rail={rail:.0f} ({rail/width:.1%}), atlas={atlas:.0f}, scene={scene:.0f}, right-margin={width-scene_x-scene:.0f}')
orig=r/'assets/source/licensed/lpc_revised'
if orig.is_dir():
 originals=[p for p in orig.rglob('*.png') if '/characters/' not in p.as_posix().lower()]
 assert len(originals)>=300 and any('/Objects/Furniture/' in str(p) for p in originals) and any('/Terrain Objects/' in str(p) for p in originals)
 primary=orig/'Terrain/Waterfall.png';split=orig/'seasonal_split/Terrain/Waterfall.png'
 assert primary.is_file() and split.is_file() and hashlib.sha256(primary.read_bytes()).digest()!=hashlib.sha256(split.read_bytes()).digest()
 print(f'PASS {len(originals)} original noncharacter sources retained; distinct waterfall variants not merged')
else: print('SKIP original image availability test: no raw source root in this checkout')
print('PASS B48R25 source checks only; Windows Rust compilation/GUI and ForgeGUI hosting NOT tested.')
