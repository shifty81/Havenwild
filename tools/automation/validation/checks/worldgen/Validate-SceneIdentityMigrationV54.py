#!/usr/bin/env python3
from pathlib import Path
import json, sys
root = Path(__file__).resolve().parents[5]
errors = []

def require(path):
    p = root / path
    if not p.exists():
        errors.append(f"missing {path}")
        return ""
    return p.read_text(encoding='utf-8')

scene_identity = require('crates/haven_core/src/scene_identity.rs')
lib = require('crates/haven_core/src/lib.rs')
contract_text = require('content/editor/scene_identity/scene_identity_migration_contract_v0_1.json')
if 'pub struct ProjectSceneId' not in scene_identity:
    errors.append('ProjectSceneId missing')
if 'pub enum SceneSurfaceRole' not in scene_identity:
    errors.append('SceneSurfaceRole missing')
if 'SceneIdentityMigrationPlan' not in scene_identity:
    errors.append('SceneIdentityMigrationPlan missing')
if 'mod scene_identity;' not in lib or 'pub use scene_identity::*;' not in lib:
    errors.append('haven_core does not export scene_identity module')
try:
    contract = json.loads(contract_text)
    if contract.get('targetSceneIdType') != 'ProjectSceneId':
        errors.append('scene identity contract does not target ProjectSceneId')
    if contract.get('supportsArbitrarySceneCreation') is not False:
        errors.append('scene creation must remain gated during bridge pass')
    if not any(r.get('role') == 'overworld_surface' for r in contract.get('seedRecords', [])):
        errors.append('contract has no overworld surface scene records')
    if not any('bank' in r.get('role','') for r in contract.get('seedRecords', [])):
        errors.append('contract has no scene bank records')
except Exception as exc:
    errors.append(f'invalid scene identity contract json: {exc}')
if errors:
    print('Scene identity migration validation failed:')
    for e in errors:
        print(' -', e)
    sys.exit(1)
print('Scene identity migration validation passed.')
