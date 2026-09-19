#!/usr/bin/env python3
"""B48R24 authoring contract and optional exact-source compositing fixture.

This static/PNG test does not compile Rust or validate a game's generation rules.
"""
from pathlib import Path
import argparse
import json
import sys

ap = argparse.ArgumentParser()
ap.add_argument('--repo', default='.')
repo = Path(ap.parse_args().repo).resolve()
src = (repo/'apps/haven_atlas_mapper_lite/src/main.rs').read_text(encoding='utf-8')
checks = {
 'new schema reads v0_6 without resetting numeric placements': 'atlas_mapper_project.v0_7' in src and 'LEGACY_PROJECT_SCHEMA_V6' in src and 'self.pieces = document.pieces;' in src,
 'source library starts with all Summer groups': 'sheet_library_group: None' in src and 'Self::Characters' in src and 'normalized.contains("/characters/")' in src,
 'seven named compositing buckets': 'const SCENE_LAYER_NAMES: [&str; 7]' in src and '"Cliff / portals"' in src and '"Water / contacts"' in src,
 'old numeric placements migrate by view only': 'layer.div_euclid(10).clamp(0,' in src and 'self.pieces[index].layer = slot as i32 * 10;' in src,
 'persist scene layer state in project and handoff': src.count('layer_visibility: self.layer_visibility') >= 3 and src.count('layer_locks: self.layer_locks') >= 3,
 'undo restores visibility/locks/selection': 'self.layer_visibility = snapshot.layer_visibility;' in src and 'self.layer_locks = snapshot.layer_locks;' in src,
 'visibility controls render and picking': 'if !app.layer_visibility[layer_slot(piece.layer)] { continue; }' in src and 'if !self.layer_visibility[layer_slot(piece.layer)] { return false; }' in src,
 'locking protects delete and move': 'if self.selected_is_locked() {' in src and 'Selected locked layer tile; unlock it before moving.' in src,
 'layer overlay blocks underlying paint': 'let blocked_by_layers = self.show_layers && layer_rect.contains(mouse);' in src and '&& !blocked_by_layers' in src,
 'only one contextual overlay at a time': 'if self.show_layers { self.show_inspector = false; }' in src and 'if self.show_inspector { self.show_layers = false; }' in src,
 'review remains exact-source/all-layer and unapproved': 'review::write_review(&path, &sources, &self.pieces, &self.heightmap)' in src and 'No recipe reroll yet; candidate only.' in src and 'false // Save/hand-off state is never a visual or runtime approval.' in src,
 'heightmap still includes genuine plus one': 'level.min(30)' in src and 'clamp(0, 30)' in src,
}
for label,ok in checks.items(): print(('PASS' if ok else 'FAIL')+': '+label)
if not all(checks.values()): sys.exit(1)
try:
 from PIL import Image
except ImportError:
 print('SKIP optional Pillow source-alpha fixture: Pillow not installed; Rust/Windows tests still required.')
else:
 grass = repo/'assets/source/licensed/lpc_revised/Terrain/terrain_summer.png'
 cliff = repo/'assets/source/licensed/lpc_revised/Terrain/cliff_summer.png'
 if grass.is_file() and cliff.is_file():
  with Image.open(grass) as a, Image.open(cliff) as b:
   assert a.width>=32 and b.width>=32
   base=a.convert('RGBA').crop((0,0,32,32))
   top=b.convert('RGBA').crop((0,0,32,32))
   first=Image.new('RGBA',(32,32));first.alpha_composite(base);first.alpha_composite(top)
   second=Image.new('RGBA',(32,32));second.alpha_composite(top);second.alpha_composite(base)
   assert first.tobytes()!=second.tobytes(), 'fixture did not distinguish stacking order'
   assert base.size==top.size==(32,32)
   print('PASS optional source-exact same-cell alpha composition, order matters; no generated artwork')
 else: print('SKIP optional source-alpha fixture: original source PNGs missing from this checkout.')
print('PASS B48R24 static layer contract; Cargo GUI, PCC and runtime parity remain unverified.')
