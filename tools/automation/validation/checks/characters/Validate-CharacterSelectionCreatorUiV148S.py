#!/usr/bin/env python3
from pathlib import Path
import json, sys
ROOT = Path(__file__).resolve().parents[5]
errors=[]
def require(path, token, label):
    text=(ROOT/path).read_text(encoding='utf-8')
    if token not in text: errors.append(f"{label}: missing {token!r} in {path}")
def check(cond,msg):
    if not cond: errors.append(msg)
policy=json.loads((ROOT/'content/characters/character_selection_creator_ui_policy_v1.json').read_text())
check(policy.get('character_card_count')==5,'character selection must expose five profile cards')
check(policy.get('world_save_limit')=='unlimited','world browser must remain unlimited')
check(policy['flows']['new_game'][0]=='choose_character','new game must choose character first')
check(policy['flows']['load_game'][0]=='choose_character','load game must choose character first')
check(policy['character_cards']['preview']=='layered_lpc_composite','cards must use layered LPC previews')
check(policy['world_browser']['dynamic_directory_scan'] is True,'world browser must dynamically scan directories')
require('crates/haven_game/src/character_selection_ui.rs','CharacterProfileCard','character profile cards')
require('crates/haven_game/src/character_selection_ui.rs','CharacterCreatorDraft','character creator draft')
require('crates/haven_game/src/character_selection_ui.rs','WorldSaveCard','unlimited world cards')
require('crates/haven_game/src/character_selection_ui.rs','MAX_PERSISTENT_CHARACTERS','five profile capacity')
require('crates/haven_game/src/character_selection_ui.rs','scan_unlimited_world_saves','dynamic world discovery')
require('crates/haven_game/src/character_selection_ui.rs','choose a character before selecting a world','character-first guard')
require('crates/haven_game/src/main.rs','mod character_selection_ui;','game module wiring')
if errors:
    print('Pass 148S FAILED')
    for error in errors: print(' -',error)
    sys.exit(1)
print('Pass 148S character selection and creator UI validated')
print('character_cards=5 world_limit=unlimited preview=layered_lpc_composite')
