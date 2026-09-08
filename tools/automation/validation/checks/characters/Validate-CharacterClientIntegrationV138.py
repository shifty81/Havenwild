#!/usr/bin/env python3
import json, pathlib, sys
root = Path(__file__).resolve().parents[5]
errors=[]
def load(rel):
    p=root/rel
    if not p.is_file(): errors.append(f"missing {rel}"); return {}
    try: return json.loads(p.read_text(encoding='utf-8'))
    except Exception as e: errors.append(f"invalid JSON {rel}: {e}"); return {}
storage=load('content/characters/character_profile_storage_v0_1.json')
flow=load('content/ui/character_creator_flow_v0_1.json')
if storage.get('maximum_profiles_per_account') != 5: errors.append('profile limit must be 5')
if storage.get('world_save_reference_field') != 'selected_character_profile_id': errors.append('world save must reference selected_character_profile_id')
if set(storage.get('preview_directions',[])) != {'down','up','left','right'}: errors.append('four cardinal preview directions required')
prohibited=set(flow.get('prohibited_creator_categories',[]))
for required in {'armor','weapons','shields','advanced_outfits'}:
    if required not in prohibited: errors.append(f'{required} must be prohibited in creator')
for rel, needles in {
 'crates/haven_save/src/character_profiles.rs':['MAX_CHARACTER_PROFILES: usize = 5','PersistentCharacterProfile','CharacterProfileIndex'],
 'crates/haven_game/src/client_character_creation.rs':['CharacterCreationState','build_character_preview_layers','idle_'],
 'crates/haven_save/src/lib.rs':['pub mod character_profiles;'],
 'crates/haven_game/src/main.rs':['mod client_character_creation;'],
}.items():
    p=root/rel
    if not p.is_file(): errors.append(f'missing {rel}'); continue
    text=p.read_text(encoding='utf-8')
    for needle in needles:
        if needle not in text: errors.append(f'{rel} missing {needle}')
if errors:
    print('Character Client Integration V138: FAIL')
    for e in errors: print(' -',e)
    sys.exit(1)
print('Character Client Integration V138: PASS')
