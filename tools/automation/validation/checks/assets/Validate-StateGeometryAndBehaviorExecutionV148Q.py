#!/usr/bin/env python3
from pathlib import Path
import json
ROOT = Path(__file__).resolve().parents[5]
required=[
 'crates/haven_assets/src/placeable_asset_registry.rs',
 'crates/haven_game/src/placeable_behavior_runtime.rs',
 'crates/haven_game/src/runtime_interactions.rs',
 'content/asset_packs/havenwild_objects/published_world_assets_v1.json',
 'content/asset_packs/placeable_state_geometry_behavior_policy_v1.json',
]
for rel in required:
    if not (ROOT/rel).is_file(): raise SystemExit(f'missing Pass 148Q file: {rel}')
registry=(ROOT/required[0]).read_text()
behavior=(ROOT/required[1]).read_text()
runtime=(ROOT/required[2]).read_text()
catalog=json.loads((ROOT/required[3]).read_text())
policy=json.loads((ROOT/required[4]).read_text())
entries={e['id']:e for e in catalog['entries']}
checks={
 'policy': policy.get('schema')=='havenwild.placeable_state_geometry_behavior_policy.v1',
 'state geometry type':'PlaceableStateGeometry' in registry and 'footprint_for_state' in registry,
 'attachments':'PlaceableAttachmentPoint' in registry and 'attachment_points_for_state' in registry,
 'behavior commands':'PlaceableBehaviorCommand' in behavior and 'compile_placeable_behavior' in behavior,
 'runtime footprint mutation':'object.footprint = next_footprint' in runtime,
 'runtime behavior execution':'compile_placeable_behavior' in runtime and 'executed behavior' in runtime,
 'door geometry':bool(entries['door_basic'].get('state_geometry')),
 'tree geometry':bool(entries['tree_default'].get('state_geometry')),
 'chair attachment':bool(entries['chair_basic'].get('attachment_points')),
 'bed attachment':bool(entries['bed_basic'].get('attachment_points')),
}
open_geo=next(g for g in entries['door_basic']['state_geometry'] if g['state']=='open')
checks['open door nonblocking']=open_geo['footprint']['blocks_movement'] is False and open_geo['footprint']['collision_size']==[0,0]
failed=[k for k,v in checks.items() if not v]
if failed: raise SystemExit('Pass 148Q validation failed: '+'; '.join(failed))
print('Pass 148Q valid: state-dependent geometry, attachment reservations, deterministic behavior execution')
