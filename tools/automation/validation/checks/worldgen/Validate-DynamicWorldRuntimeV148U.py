#!/usr/bin/env python3
from pathlib import Path
import json, sys
ROOT = Path(__file__).resolve().parents[5]
errors=[]
def require(path, token):
    p=ROOT/path
    if not p.is_file(): errors.append(f'missing {path}'); return
    text=p.read_text(encoding='utf-8')
    if token not in text: errors.append(f'{path} missing {token!r}')
def check(ok,msg):
    if not ok: errors.append(msg)
policy=json.loads((ROOT/'content/characters/dynamic_world_runtime_policy_v1.json').read_text())
check(policy['runtime_world_identity']=='WorldSaveId','runtime identity must be WorldSaveId')
check(policy['world_save_limit']=='unlimited','world saves must be unlimited')
check(policy['runtime_launch']['direct_client_save_slot_dependency'] is False,'runtime launch must not depend on ClientSaveSlot')
check(policy['character_world_link_required'] is True,'character-world links must be required')
require('crates/haven_save/src/lib.rs','pub struct WorldSaveMetadata')
require('crates/haven_save/src/lib.rs','pub fn world_save_paths')
require('crates/haven_save/src/lib.rs','pub fn migrate_legacy_client_save_slots')
require('crates/haven_save/src/character_profiles.rs','pub fn validate(&self) -> Result<(), String>')
require('crates/haven_game/src/client_frontend.rs','pub(crate) struct WorldLaunchRequest')
require('crates/haven_game/src/client_frontend.rs','scan_world_saves')
require('crates/haven_game/src/client_frontend.rs','create_seeded_world_save')
require('crates/haven_game/src/client_save_generation.rs','WorldSaveMetadata')
require('crates/haven_game/src/main.rs','world_id: WorldSaveId')
require('crates/haven_game/src/main.rs','character_id: CharacterId')
require('crates/haven_game/src/main.rs','world_save_paths(&save_root, &world_id)')
main=(ROOT/'crates/haven_game/src/main.rs').read_text()
check('save_slot: ClientSaveSlot' not in main,'Game still owns ClientSaveSlot')
frontend=(ROOT/'crates/haven_game/src/client_frontend.rs').read_text()
check('Option<ClientSaveSlot>' not in frontend,'frontend still returns ClientSaveSlot')
if errors:
    print('Pass 148U FAILED')
    for e in errors: print(' -',e)
    sys.exit(1)
print('Pass 148U dynamic world runtime validated')
print('runtime_identity=WorldSaveId character_first=true world_limit=unlimited legacy_slots=migrated')
