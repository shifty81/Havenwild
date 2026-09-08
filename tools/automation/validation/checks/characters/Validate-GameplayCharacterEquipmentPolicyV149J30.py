from pathlib import Path
import json, sys
root = Path(__file__).resolve().parents[5]
errors=[]
policy_path=root/'content/characters/gameplay_character_equipment_policy_v0_1.json'
policy=json.loads(policy_path.read_text())
if policy.get('schema')!='havenwild.character.gameplay_equipment_policy.v0_1': errors.append('bad equipment policy schema')
slots={slot['id']:slot for slot in policy.get('slots',[])}
for required in ('head','torso','legs','feet','back','hands','off_hand'):
    if required not in slots: errors.append(f'missing equipment slot {required}')
for slot in ('head','back','hands','off_hand'):
    if slots.get(slot,{}).get('allowAtCreation') is not False: errors.append(f'{slot} must remain gameplay-only')
required=set(policy.get('requiredAnimationStates',[]))
if required != {'idle','walk'}: errors.append(f'required animation states must be idle/walk, got {sorted(required)}')
module=(root/'crates/haven_game/src/character_equipment_catalog.rs').read_text()
for token in ('missing_required_animations','slot_for_channel','gameplay_entries','animation_coverage_summary'):
    if token not in module: errors.append(f'missing runtime equipment catalog contract {token}')
main=(root/'crates/haven_game/src/main.rs').read_text()
if 'mod character_equipment_catalog;' not in main: errors.append('character equipment catalog not compiled into haven_game')
if errors:
    print('Pass 149J30 FAILED')
    [print('-', error) for error in errors]
    sys.exit(1)
print('Pass 149J30 gameplay equipment policy and animation coverage foundation validated')
