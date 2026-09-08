#!/usr/bin/env python3
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[5]
errors=[]
flow=json.loads((ROOT/'content/ui/character_creator_flow_v0_1.json').read_text())
source=(ROOT/'crates/haven_game/src/client_character_creator_ui.rs').read_text()
main=(ROOT/'crates/haven_game/src/main.rs').read_text()
required_categories=['Body','Head','Eyes','Eyebrows','FacialHair','Hair','StarterTop','StarterBottom','StarterFeet','Colors']
for value in required_categories:
    if value not in source: errors.append(f'missing creator category {value}')
for channel in ['skin_tone','hair_color','eye_color','starter_top_color','starter_bottom_color']:
    if channel not in source: errors.append(f'missing color channel {channel}')
for token in ['build_character_preview_layers','validate_for_commit','Create Character']:
    if token not in source: errors.append(f'missing GUI integration token {token}')
if 'mod client_character_creator_ui;' not in main: errors.append('main.rs does not register client_character_creator_ui')
if flow.get('implementation')!='crates/haven_game/src/client_character_creator_ui.rs': errors.append('flow implementation path mismatch')
if flow.get('maximum_profiles')!=5: errors.append('profile cap must remain five')
if any(x in source.lower() for x in ['armor tab','weapon tab','shield tab']): errors.append('combat equipment must not be exposed in initial creator')
if errors:
    print('Character Creator GUI V139: FAIL')
    for e in errors: print(' -',e)
    raise SystemExit(1)
print('Character Creator GUI V139: PASS')
