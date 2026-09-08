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
require('crates/haven_game/src/character_world_sync.rs', [
    'update_character_world_autosave', 'host_character_world_state_envelope',
    'apply_replicated_character_world_state', 'persist_scene_transition_state',
    'persist_disconnect_state', 'validate_for_client'
])
require('crates/haven_game/src/main.rs', [
    'mod character_world_sync;', 'character_autosave_next_at',
    'character_state_sequence'
])
require('crates/haven_game/src/client_entry.rs', [
    'persist_runtime_exit_state', 'return to main menu', 'quit desktop'
])
require('crates/haven_game/src/client_pause_menu.rs', ['update_character_world_autosave(now)'])
require('crates/haven_game/src/runtime_scene_navigation.rs', [
    'persist_scene_transition_state(if surface_streaming',
    '"surface chunk crossing"', '"scene transition"',
    'persist_scene_transition_state("developer scene jump")'
])
require('crates/haven_net/src/lib.rs', [
    'CharacterWorldStateSnapshot', 'CharacterWorldStateEnvelope',
    'CharacterStateAuthority', 'stale character-world state sequence', 'validate_for_client'
])
policy=ROOT/'content/characters/character_world_sync_policy_v1.json'
try:
    data=json.loads(policy.read_text())
    expected={'autosave','scene_transition','return_to_main_menu','quit_desktop','server_disconnect'}
    if not expected.issubset(set(data.get('save_triggers',[]))): checks.append('policy missing save triggers')
    authority=data.get('authority',{})
    if authority.get('mutation_owner')!='listen_server_host': checks.append('policy mutation owner is not host')
    if authority.get('transport_status')!='contract_ready_transport_pending': checks.append('policy must disclose pending transport')
except Exception as e: checks.append(f'policy invalid: {e}')
if checks:
    print('Pass 148W FAILED')
    for c in checks: print('-',c)
    sys.exit(1)
print('Pass 148W character-world autosave and synchronization contract validated')
