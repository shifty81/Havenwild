#!/usr/bin/env python3
import json,sys,re
from pathlib import Path
R=Path(__file__).resolve().parents[5]; errors=[]
def load(p):
 try:return json.loads(p.read_text(encoding='utf-8'))
 except Exception as e: errors.append(f'{p}: {e}'); return {}
c=load(R/'content/worldgen/chunk_persistence_contract_v1.json')
if c.get('schema')!='havenwild.chunk_persistence_contract.v1' or c.get('version')!=1: errors.append('wrong chunk persistence schema/version')
pol=c.get('policy',{})
for k in ('canonicalChunkKeys','eastWestKeysWrap','northSouthKeysBounded','deterministicBaselineStoredByReference','authoredOverridesStoredSeparately','playerDeltasStoredSeparately','runtimeTransientNeverSaved','replicationStateNeverAuthoritativeOnDisk','atomicWritesRequired','recoveryCopyRequired','futureSchemaRule'):
 if k not in pol: errors.append(f'missing policy {k}')
if not all(pol.get(k) for k in ('canonicalChunkKeys','eastWestKeysWrap','northSouthKeysBounded','deterministicBaselineStoredByReference','authoredOverridesStoredSeparately','playerDeltasStoredSeparately','runtimeTransientNeverSaved','replicationStateNeverAuthoritativeOnDisk','atomicWritesRequired','recoveryCopyRequired')): errors.append('required persistence policy disabled')
parts=c.get('partitions',[]); ids=[x.get('id') for x in parts]
expected=['baseline_reference','authored_overrides','player_deltas','persistent_simulation','runtime_transient','replication_state']
if ids!=expected: errors.append('partition order/identity drift')
for p in parts:
 if p.get('persistence')=='never' and p.get('file') is not None: errors.append(f"{p.get('id')}: never-persist partition has file")
 if p.get('persistence')!='never' and not p.get('file'): errors.append(f"{p.get('id')}: persisted partition lacks file")
layout=c.get('saveLayout',{})
for k in ('manifest','migrationJournal','recoveryDirectory','compatibilityWorldSnapshot'):
 if not layout.get(k): errors.append(f'missing save layout {k}')
mig=c.get('migrationPolicy',{})
lib=(R/'crates/haven_save/src/lib.rs').read_text(encoding='utf-8')
version_match=re.search(r'CURRENT_CLIENT_GENERATION_VERSION: u32 = (\d+)', lib)
current_version=int(version_match.group(1)) if version_match else None
if current_version is None: errors.append('current save generation is not declared')
elif mig.get('currentClientGenerationVersion')!=current_version or 4 not in mig.get('supportedFromVersions',[]): errors.append(f'v4-to-v{current_version} migration policy missing')
rs=(R/'crates/haven_save/src/chunk_persistence.rs').read_text(encoding='utf-8')
for tok in ('CanonicalChunkKey','ChunkBaselineReference','ChunkAuthoredOverrides','ChunkPlayerDeltas','ChunkPersistentSimulation','ChunkPersistenceEnvelope','ChunkManifest','canonical_chunk','pub fn validate'):
 if tok not in rs: errors.append(f'Rust chunk persistence module missing {tok}')
for tok in (f'CURRENT_CLIENT_GENERATION_VERSION: u32 = {current_version}','chunk_manifest','chunks_root','recovery_root','atomic_write','save_chunk_manifest_to_path'):
 if tok not in lib: errors.append(f'haven_save wiring missing {tok}')
if re.search(r'(?<!atomic_)write\(path,', lib): errors.append('direct non-atomic save write remains in haven_save')
game=(R/'crates/haven_game/src/client_save_generation.rs').read_text(encoding='utf-8')
if 'save_chunk_manifest_to_path' not in game: errors.append('new saves do not initialize chunk manifest')
vm=load(R/'content/validation/validation_manifest_v1.json'); tasks={x.get('id'):x for x in vm.get('tasks',[])}
t=tasks.get('validate-chunkpersistencenormalizationv144')
if not t or not t.get('enabled') or not t.get('required') or t.get('lifecycle')!='active': errors.append('Pass 144 validator not actively registered')
if errors:
 print('Pass 144 chunk persistence normalization FAILED'); [print(' -',e) for e in errors]; sys.exit(1)
print(f'Pass 144 chunk persistence normalization validated: {len(parts)} ownership partitions, canonical wrapped keys, atomic/recovery writes, v4-to-v{current_version} migration contract')
