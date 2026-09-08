#!/usr/bin/env python3
from pathlib import Path
import json, sys
ROOT = Path(__file__).resolve().parents[5]
errors=[]
def require(path, token, label):
    p=ROOT/path
    if not p.is_file(): errors.append(f"{label}: missing {path}"); return
    text=p.read_text(encoding='utf-8')
    if token not in text: errors.append(f"{label}: missing {token!r} in {path}")
def check(condition, message):
    if not condition: errors.append(message)
policy=json.loads((ROOT/'content/characters/character_visual_frontend_policy_v1.json').read_text())
check(policy.get('character_card_count')==5,'visual frontend must expose five character cards')
check(policy.get('world_save_limit')=='unlimited','visual frontend policy must preserve unlimited worlds')
check(policy['flows']['new_game'][0]=='choose_character','new game must choose character first')
check(policy['flows']['load_game'][0]=='choose_character','load game must choose character first')
check(set(policy['character_actions']) >= {'select','create','edit','delete'},'character CRUD actions incomplete')
check(policy['world_browser']['dynamic_directory_scan'] is True,'world browser must scan dynamically')
check(policy['world_browser']['must_display_adapter_boundary'] is True,'legacy runtime adapter boundary must be visible')
require('crates/haven_game/src/client_frontend.rs','MAX_PERSISTENT_CHARACTERS','five-card frontend')
require('crates/haven_game/src/client_frontend.rs','CharacterProfileStore','persistent character store')
require('crates/haven_game/src/client_frontend.rs','scan_unlimited_world_saves','unlimited world discovery')
require('crates/haven_game/src/client_frontend.rs','FrontendScreen::Characters','character screen')
require('crates/haven_game/src/client_frontend.rs','FrontendScreen::Creator','creator screen')
require('crates/haven_game/src/client_frontend.rs','FrontendScreen::Worlds','world screen')
require('crates/haven_game/src/client_frontend.rs','profile_store.delete','character deletion')
require('crates/haven_game/src/client_frontend.rs','profile_store.update','character editing')
require('crates/haven_game/src/client_frontend.rs','profile_store.create','character creation')
require('crates/haven_game/src/client_character_frontend_draw.rs','draw_character_preview','LPC preview renderer')
require('crates/haven_game/src/main.rs','ClientFrontend::new().await','async visual frontend startup')
require('crates/haven_game/src/main.rs','mod client_character_frontend_draw;','draw module wiring')
for rel in ['crates/haven_game/src/client_frontend.rs','crates/haven_game/src/client_character_frontend_draw.rs']:
    lines=(ROOT/rel).read_text(encoding='utf-8').splitlines()
    check(len(lines)<=500,f'{rel} exceeds 500-line architecture limit ({len(lines)})')
if errors:
    print('Pass 148T FAILED')
    for error in errors: print(' -',error)
    sys.exit(1)
print('Pass 148T character visual frontend validated')
print('character_cards=5 actions=create/edit/delete/select world_scan=dynamic launch_adapter=legacy_explicit')
