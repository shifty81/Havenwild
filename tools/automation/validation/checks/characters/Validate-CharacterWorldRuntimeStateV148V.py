#!/usr/bin/env python3
from pathlib import Path
import json, sys
ROOT = Path(__file__).resolve().parents[5]
checks=[]
def require(path, tokens=()):
    p=ROOT/path
    if not p.is_file(): checks.append(f'missing {path}'); return
    text=p.read_text(encoding='utf-8')
    for token in tokens:
        if token not in text: checks.append(f'{path} missing {token}')
require('crates/haven_game/src/character_world_runtime.rs', [
    'restore_character_world_link', 'persist_character_world_state',
    'reload_character_world_state', 'world_reputation', 'world_quest_flags'
])
require('crates/haven_game/src/main.rs', ['mod character_world_runtime;', 'character_world_link: CharacterWorldLink'])
require('crates/haven_game/src/runtime_persistence.rs', ['persist_character_world_state("manual save")', 'reload_character_world_state()'])
require('crates/haven_game/src/client_frontend.rs', ['load_character_world_link', 'link.touch()'])
policy=ROOT/'content/characters/character_world_runtime_state_policy_v1.json'
try:
    data=json.loads(policy.read_text())
    expected={'world_position','world_scene','world_reputation','world_relationships','world_quest_flags','last_played_unix_seconds'}
    if not expected.issubset(set(data.get('restored_fields',[]))): checks.append('policy missing restored fields')
except Exception as e: checks.append(f'policy invalid: {e}')
if checks:
    print('Pass 148V FAILED')
    for c in checks: print('-',c)
    sys.exit(1)
print('Pass 148V character-world runtime state validated')
