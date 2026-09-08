from pathlib import Path
import json, sys
root = Path(__file__).resolve().parents[5]
policy=json.loads((root/'content/characters/starter_creator_policy_v0_1.json').read_text())
errors=[]
if policy.get('schema')!='havenwild.character.starter_creator_policy.v0_1': errors.append('bad schema')
excluded=set(policy.get('excludedAtCreation',[]))
for required in ('armor','weapon','advanced_headwear'):
    if required not in excluded: errors.append(f'missing exclusion {required}')
for channel, entries in policy.get('starterClothing',{}).items():
    if len(entries)>4: errors.append(f'{channel} exposes too many starter items: {len(entries)}')
model=(root/'crates/haven_game/src/character_creator_model.rs').read_text()
for forbidden in ('LongShirt =>','LongSkirt =>','Hood =>'):
    if forbidden in model: errors.append(f'creator still exposes {forbidden}')
if errors:
    print('Pass 149J29 FAILED')
    [print('-',e) for e in errors]
    sys.exit(1)
print('Pass 149J29 starter creator scope validated')
