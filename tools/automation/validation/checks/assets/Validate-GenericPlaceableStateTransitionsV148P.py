#!/usr/bin/env python3
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[5]
required=[
 'crates/haven_assets/src/placeable_asset_registry.rs',
 'crates/haven_game/src/runtime_interactions.rs',
 'crates/haven_core/src/foundation.rs',
 'crates/haven_core/src/foundation/map_serialization.rs',
 'apps/haven_editor_native/src/app/asset_library_panel.rs',
 'apps/haven_editor_native/src/app/scene_authoring.rs',
 'content/asset_packs/havenwild_objects/published_world_assets_v1.json',
 'content/asset_packs/placeable_state_transition_policy_v1.json',
]
for rel in required:
    if not (ROOT/rel).is_file(): raise SystemExit(f'missing Pass 148P file: {rel}')
registry=(ROOT/required[0]).read_text(encoding='utf-8')
runtime=(ROOT/required[1]).read_text(encoding='utf-8')
core=(ROOT/required[2]).read_text(encoding='utf-8')
serialization=(ROOT/required[3]).read_text(encoding='utf-8')
panel=(ROOT/required[4]).read_text(encoding='utf-8')
authoring=(ROOT/required[5]).read_text(encoding='utf-8')
catalog=json.loads((ROOT/required[6]).read_text(encoding='utf-8'))
policy=json.loads((ROOT/required[7]).read_text(encoding='utf-8'))
checks={
 'policy schema':policy.get('schema')=='havenwild.placeable_state_transition_policy.v1',
 'host authority policy':policy['requirements']['host_authority_required_for_runtime_mutation'] is True,
 'transition contract':'PlaceableStateTransition' in registry,
 'behavior binding':'PlaceableBehaviorBinding' in registry,
 'authority context':'PlaceableMutationContext' in registry and 'is_authoritative_host' in registry,
 'state resolver':'transition_for' in registry,
 'runtime mutation':'set_object_state(object_id' in runtime,
 'runtime authority gate':'transition.authority.allows(authority)' in runtime,
 'behavior node dispatch':'definition.behavior.node_id' in runtime,
 'saved object state':'"object_state {} {}\\n"' in serialization,
 'editor previous state':'library_state_prev_rect' in panel,
 'editor next state':'library_state_next_rect' in panel,
 'placement preview state':'selected_placeable_preview_state' in authoring,
}
entries={e['id']:e for e in catalog.get('entries',[])}
for key in ('chair_basic','bed_basic','tree_default','door_basic'):
    checks[f'{key} transitions']=bool(entries.get(key,{}).get('transitions'))
    checks[f'{key} behavior node']=bool(entries.get(key,{}).get('behavior',{}).get('node_id'))
for entry in catalog.get('entries',[]):
    states=set(entry.get('states',[]))
    for i,t in enumerate(entry.get('transitions',[])):
        checks[f"{entry.get('id')} transition {i} states"] = t.get('from') in states and t.get('to') in states
        checks[f"{entry.get('id')} transition {i} authority"] = t.get('authority') in {'host','editor_preview'}
failed=[name for name,ok in checks.items() if not ok]
if failed: raise SystemExit('Pass 148P validation failed: '+'; '.join(failed))
print('Pass 148P generic placeable state transitions valid: persisted state, host authority, behavior bindings, editor preview controls')
