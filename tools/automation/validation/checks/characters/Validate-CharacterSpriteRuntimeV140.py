#!/usr/bin/env python3
import json, pathlib, sys
root = Path(__file__).resolve().parents[5]
registry=json.loads((root/'content/characters/character_sprite_registry_v0_1.json').read_text())
catalog=json.loads((root/'content/characters/character_creation_catalog_v0_1.json').read_text())
errors=[]
if (registry['frame_width'],registry['frame_height']) != (64,64): errors.append('registry must use 64x64 frames')
if set(registry['direction_rows']) != {'down','left','right','up'}: errors.append('direction rows incomplete')
ids={x['option_id'] for x in registry['layers']}
required={o['id'] for c in catalog['appearance_categories'] for o in c['options']} | {o['id'] for o in catalog['starter_clothing']}
missing=sorted(required-ids)
if missing: errors.append('missing sprite roles: '+', '.join(missing))
paths=[x['texture_path'] for x in registry['layers']]
if any('..' in p or not p.endswith('.png') for p in paths): errors.append('invalid texture path')
ui=(root/'crates/haven_game/src/client_character_creator_ui.rs').read_text()
runtime=(root/'crates/haven_game/src/client_character_sprite_runtime.rs').read_text()
for token in ['draw_with_sprite_runtime','draw_preview_panel_with_sprites']:
    if token not in ui: errors.append('UI missing '+token)
for token in ['load_texture','FilterMode::Nearest','draw_texture_ex','source: Some','palette_tint']:
    if token not in runtime: errors.append('runtime missing '+token)
if errors:
    print('Character Sprite Runtime V140: FAIL'); [print(' - '+e) for e in errors]; sys.exit(1)
print('Character Sprite Runtime V140: PASS')
