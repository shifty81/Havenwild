#!/usr/bin/env python3
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[5]
errors=[]
required=[
 'crates/haven_assets/src/asset_pack_discovery.rs',
 'content/asset_packs/pack_discovery_roots_v1.json',
 'content/asset_packs/havenwild_core/pack.json',
 'content/asset_packs/havenwild_worldgen/pack.json',
 'content/asset_packs/havenwild_characters/pack.json',
 'content/asset_packs/havenwild_objects/pack.json',
 'content/asset_packs/havenwild_interface/pack.json',
 'content/asset_packs/havenwild_audio/pack.json',
 'content/asset_packs/lpc_revised/pack.json',
 'docs/design/AUTOMATIC_ASSET_PACK_DISCOVERY_AND_MIGRATION_PASS148D.md'
]
for rel in required:
    if not (ROOT/rel).is_file(): errors.append(f'missing {rel}')

src=(ROOT/'crates/haven_assets/src/asset_pack_discovery.rs').read_text(encoding='utf-8') if (ROOT/'crates/haven_assets/src/asset_pack_discovery.rs').is_file() else ''
for token in ['pub struct AssetPackDiscovery','discover_and_mount','load_project_asset_packs','PackDiscoveryStatus','MissingDependency','user/asset_packs','mods/asset_packs']:
    if token not in src: errors.append(f'asset_pack_discovery.rs missing {token}')
lib=(ROOT/'crates/haven_assets/src/lib.rs').read_text(encoding='utf-8')
if 'pub mod asset_pack_discovery;' not in lib: errors.append('haven_assets does not export asset_pack_discovery')

pack_ids=set(); categories=set(); semantic_ids=set()
for manifest in sorted((ROOT/'content/asset_packs').glob('*/pack.json')):
    try: data=json.loads(manifest.read_text(encoding='utf-8'))
    except Exception as exc:
        errors.append(f'{manifest.relative_to(ROOT)} invalid JSON: {exc}'); continue
    pid=data.get('id')
    if pid in pack_ids: errors.append(f'duplicate pack id {pid}')
    pack_ids.add(pid)
    if data.get('schema')!='havenwild.asset_pack.v1': errors.append(f'{pid}: wrong schema')
    sources={s.get('id') for s in data.get('sources',[])}
    for asset in data.get('assets',[]):
        categories.add(asset.get('category'))
        semantic_ids.add(asset.get('semantic_id'))
        if asset.get('source_id') not in sources: errors.append(f'{pid}:{asset.get("id")} missing source')
    lic=data.get('license',{})
    if data.get('production_enabled') and not all(lic.get(k) for k in ('production_approved','commercial_use','redistribution')):
        errors.append(f'{pid}: invalid production license gate')

expected={'terrain','character','animation','tile_object','building','tree','foliage','ui','audio','music'}
missing=expected-categories
if missing: errors.append('migrated packs missing categories: '+', '.join(sorted(missing)))
for semantic in ['terrain.grass','character.player.base','object.catalog.runtime','ui.skin.default','audio.catalog.default']:
    if semantic not in semantic_ids: errors.append(f'missing migrated semantic asset {semantic}')

roots=json.loads((ROOT/'content/asset_packs/pack_discovery_roots_v1.json').read_text(encoding='utf-8')) if (ROOT/'content/asset_packs/pack_discovery_roots_v1.json').is_file() else {}
paths={item.get('path') for item in roots.get('roots',[])}
for path in ('content/asset_packs','user/asset_packs','mods/asset_packs'):
    if path not in paths: errors.append(f'discovery roots missing {path}')

if errors:
    print('Pass 148D asset-pack discovery and migration FAILED')
    for error in errors: print('-',error)
    raise SystemExit(1)
print(f'Pass 148D asset-pack discovery and migration valid: {len(pack_ids)} packs, {len(categories)} categories, {len(semantic_ids)} semantic entries')
