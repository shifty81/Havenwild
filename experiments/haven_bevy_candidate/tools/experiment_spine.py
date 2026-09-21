#!/usr/bin/env python3
"""B48R28C7-C16 candidate-only project/scene/renderer/PIE infrastructure.

ONE authority: the existing Havenwild PCC and original source/fixture. This module
never launches a second server/PCC, publishes assets, or writes canonical saves.
All artifacts are explicitly UNAPPROVED and held in candidate-ignored evidence.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import importlib.util
import json
import os
import re
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

SCHEMA = 'havenwild.experimental.infrastructure.v1'
SESSION = 'session.json'
SAVED = 'saved_snapshot.json'
CANDIDATE = Path('experiments/haven_bevy_candidate')
ARTIFACTS = Path('experiments/haven_bevy_candidate/evidence/infrastructure')
EVENT_LIMIT = 128
SUPPORTED = frozenset(('Grass', 'MudBank', 'RiverWater'))
ID_RE = re.compile(r'^[a-zA-Z0-9._-]{1,64}$')

class SpineError(ValueError):
    pass

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def encoded(value: dict) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + '\n').encode('utf-8')

def document_sha(doc: dict) -> str:
    return sha(json.dumps(doc, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8'))

def load(path: Path) -> dict:
    try:
        raw = path.read_bytes()
        if len(raw) > 8_000_000:
            raise SpineError(f'Candidate evidence exceeds 8MB: {path.name}')
        value = json.loads(raw)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise SpineError(f'Cannot read valid JSON: {path}: {exc}') from exc
    if not isinstance(value, dict):
        raise SpineError('Expected a JSON object')
    return value

def guard(root: Path) -> Path:
    """Fail closed if evidence could escape the candidate through symlinks."""
    root = root.resolve(strict=True)
    if not (root / 'Cargo.toml').is_file():
        raise SpineError('Havenwild root Cargo.toml absent')
    for relative in ('experiments', CANDIDATE, CANDIDATE / 'evidence', ARTIFACTS):
        item = root / relative
        if item.is_symlink() or (item.exists() and not item.is_dir()):
            raise SpineError(f'Candidate infrastructure path redirected: {relative}')
    candidate = root / CANDIDATE
    if not candidate.is_dir():
        raise SpineError('Candidate directory absent')
    for filename in (SESSION, SAVED, 'source_stack.json', 'mapper_queue.json',
                     'render_packets.json', 'pie_ticket.json', 'parity.json', 'readiness.json'):
        item = root / ARTIFACTS / filename
        if item.is_symlink() or (item.exists() and not item.is_file()):
            raise SpineError(f'Candidate infrastructure output redirected: {filename}')
    return root / ARTIFACTS

def atomic(root: Path, name: str, value: dict) -> Path:
    if name not in (SESSION, SAVED, 'source_stack.json', 'mapper_queue.json',
                    'render_packets.json', 'pie_ticket.json', 'parity.json', 'readiness.json'):
        raise SpineError('Unknown candidate infrastructure output path')
    directory = guard(root)
    directory.mkdir(parents=True, exist_ok=True)
    if directory.is_symlink():
        raise SpineError('Candidate evidence directory was redirected')
    path = directory / name
    raw = encoded(value)
    if path.is_file() and path.read_bytes() == raw:
        return path
    tmp = None
    try:
        with tempfile.NamedTemporaryFile(dir=directory, prefix='.candidate-atomic-', delete=False) as stream:
            tmp = Path(stream.name)
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(tmp, path)
    finally:
        if tmp is not None:
            tmp.unlink(missing_ok=True)
    return path

def _load_gate() -> object:
    path = Path(__file__).with_name('candidate_gate.py')
    spec = importlib.util.spec_from_file_location('hw_candidate_gate_infra', path)
    if spec is None or spec.loader is None:
        raise SpineError('Existing PCC candidate gate not available')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def authority(root: Path) -> tuple[dict, object]:
    root = root.resolve(strict=True)
    guard(root)
    gate = _load_gate()
    receipt = gate.verify(root)
    if (receipt['lineage']['branch'] != 'experimental' or receipt['sourceExactArtApproved'] is not False
        or receipt['worldRendererParity'] is not False or receipt['pieCertified'] is not False):
        raise SpineError('Candidate gate returned a promoted or nonexperimental state')
    return receipt, gate

def fixture(root: Path, receipt: dict, gate: object) -> dict:
    path = root / gate.SCENE
    raw = path.read_bytes()
    if sha(raw) != receipt['sceneSha256']:
        raise SpineError('Canonical fixture changed since PCC input verification')
    doc = json.loads(raw)
    check_scene(doc)
    if doc['sceneId'] != receipt['sceneId'] or doc['sceneSize'] != receipt['size']:
        raise SpineError('Fixture identity does not match PCC verification')
    return doc

def check_scene(doc: dict) -> None:
    if not isinstance(doc, dict) or doc.get('kind') != 'worldgen_scene' or doc.get('tileSize') != [32, 32]:
        raise SpineError('Unsupported scene kind or 32px contract')
    size = doc.get('sceneSize')
    if (not isinstance(size, list) or len(size) != 2 or any(type(n) is not int or not 1 <= n <= 2048 for n in size)
        or size[0] * size[1] > 65536):
        raise SpineError('Invalid bounded scene size')
    if not isinstance(doc.get('sceneId'), str) or not doc['sceneId']:
        raise SpineError('Missing stable scene identity')
    layers = doc.get('layers')
    terrain = layers.get('terrain') if isinstance(layers, dict) else None
    if (not isinstance(terrain, list) or len(terrain) != size[1]
        or any(not isinstance(row, list) or len(row) != size[0]
                   or any(type(role) is not str or role not in SUPPORTED for role in row) for row in terrain)):
        raise SpineError('Incomplete or unsupported terrain grid')
    # Existing source data has no elevation layer. Never imply all cells are at sea level.
    if 'elevation' in layers:
        levels = layers['elevation']
        if (not isinstance(levels, list) or len(levels) != size[1] or any(
                not isinstance(row, list) or len(row) != size[0]
                or any(type(v) is not int or not 0 <= v <= 30 for v in row) for row in levels)):
            raise SpineError('Elevation must be a separate complete 0..30 integer heightmap')

def context(root: Path, receipt: dict, gate: object) -> dict:
    original = fixture(root, receipt, gate)
    return {'schema': SCHEMA+'.context', 'status': 'PROJECT_INPUTS_VERIFIED_CANDIDATE_ONLY',
            'projectRoot': str(root), 'candidateRoot': str(root / CANDIDATE),
            'branch': receipt['lineage']['branch'], 'sourceSha256': receipt['sourceSha256'],
            'creditsSha256': sha((root / CANDIDATE / gate.CREDITS).read_bytes()),
            'sceneId': original['sceneId'], 'fixtureSha256': receipt['sceneSha256'],
            'tileSizePx': 32, 'sourceFamily': 'ElizaWy',
            'canonicalSaveWriteAllowed': False, 'assetPublicationAllowed': False,
            'worldRendererParity': False, 'actualGamePie': False,
            'pccAuthority': 'tools/control/HavenwildPccHost.ps1'}

def source_stack(root: Path, receipt: dict, gate: object) -> dict:
    result = context(root, receipt, gate)
    source = root / CANDIDATE / gate.SOURCE
    credits = root / CANDIDATE / gate.CREDITS
    raw = source.read_bytes()
    if sha(raw) != receipt['sourceSha256']:
        raise SpineError('Immutable source mismatched PCC pin')
    result.update({'schema': SCHEMA+'.source_stack', 'status': 'SOURCE_BYTES_VERIFIED_NOT_ASSET_APPROVED',
                   'entries': [{'sourceId': 'elizawy.terrain.summer.original',
                                'candidateReadOnlyPath': str(gate.SOURCE),
                                'sha256': sha(raw), 'creditsSha256': sha(credits.read_bytes()),
                                'dimensionsPx': [512, 832], 'cellSizePx': 32,
                                'visualApproval': False, 'runtimePublication': False}],
                   'stackPolicy': 'read_only_originals_derived_project_layers_only'})
    atomic(root,'source_stack.json',result)
    return result

def fresh_session(root: Path, receipt: dict, gate: object) -> dict:
    original = fixture(root, receipt, gate)
    return {'schema': SCHEMA+'.session', 'status': 'ISOLATED_AUTHORING_CANDIDATE',
            'sceneId': original['sceneId'], 'fixtureSha256': receipt['sceneSha256'],
            'sourceSha256': receipt['sourceSha256'], 'documentRevision': 0,
            'document': original, 'documentSha256': document_sha(original),
            'history': [], 'cursor': 0, 'usedCommandIds': [], 'canonicalSaveWriteAllowed': False,
            'assetPublicationAllowed': False}

def replay(original: dict, history: list, cursor: int) -> dict:
    scene = copy.deepcopy(original)
    for index, event in enumerate(history):
        if (not isinstance(event, dict) or not ID_RE.fullmatch(str(event.get('commandId', '')))
            or event.get('type') != 'set_terrain' or not isinstance(event.get('cell'), list)
            or len(event['cell']) != 2 or any(type(n) is not int for n in event['cell'])
            or event.get('before') not in SUPPORTED or event.get('after') not in SUPPORTED
            or event['before'] == event['after']):
            raise SpineError(f'Malformed journal event {index}')
        x, y = event['cell']
        if not (0 <= x < scene['sceneSize'][0] and 0 <= y < scene['sceneSize'][1]):
            raise SpineError('Journal coordinate outside scene')
        current = scene['layers']['terrain'][y][x]
        if current != event['before']:
            raise SpineError(f'Journal replay mismatch at {index}')
        scene['layers']['terrain'][y][x] = event['after']
    for event in reversed(history[cursor:]):
        x, y = event['cell']
        scene['layers']['terrain'][y][x] = event['before']
    return scene

def verified_session(root: Path, receipt: dict, gate: object) -> dict:
    path = guard(root) / SESSION
    if not path.is_file():
        raise SpineError('No candidate session; run infra-open through PCC')
    value = load(path)
    if (value.get('schema') != SCHEMA+'.session' or value.get('fixtureSha256') != receipt['sceneSha256']
        or value.get('sourceSha256') != receipt['sourceSha256'] or value.get('sceneId') != receipt['sceneId']
        or value.get('canonicalSaveWriteAllowed') is not False
        or value.get('assetPublicationAllowed') is not False):
        raise SpineError('Candidate session source/authority/fixture mismatch')
    history = value.get('history')
    cursor = value.get('cursor')
    revision = value.get('documentRevision')
    if (not isinstance(history, list) or len(history) > EVENT_LIMIT
        or type(cursor) is not int or not 0 <= cursor <= len(history)
        or type(revision) is not int or revision < 0 or revision > 1_000_000):
        raise SpineError('Invalid session journal, cursor or revision')
    ids = [event.get('commandId') for event in history if isinstance(event,dict)]
    used = value.get('usedCommandIds')
    if (len(ids) != len(history) or len(ids) != len(set(ids))
        or not isinstance(used,list) or len(used) != len(set(used))
        or len(used) > 1_000_000 or any(not isinstance(i,str) or not ID_RE.fullmatch(i) for i in used)
        or not set(ids).issubset(set(used))):
        raise SpineError('Duplicate or malformed journal command identity')
    doc = value.get('document')
    check_scene(doc)
    # Validate journal chronology first. A corrupted event must fail with a
    # replay-specific diagnostic even if the document checksum also disagrees;
    # both checks remain mandatory before returning the session.
    expected = replay(fixture(root, receipt, gate), history, cursor)
    if document_sha(doc) != value.get('documentSha256'):
        raise SpineError('Session document hash changed without a command')
    if doc != expected:
        raise SpineError('Session document differs from replayed journal')
    return value

def open_session(root: Path, receipt: dict, gate: object) -> dict:
    path = guard(root) / SESSION
    if path.is_file():
        return verified_session(root, receipt, gate)
    result = fresh_session(root, receipt, gate)
    atomic(root, SESSION, result)
    return result

def edit(root: Path, receipt: dict, gate: object, *, command_id: str,
         expected_revision: int, x: int, y: int, role: str) -> dict:
    value = verified_session(root, receipt, gate)
    if not isinstance(command_id,str) or not ID_RE.fullmatch(command_id):
        raise SpineError('Invalid stable command ID')
    if command_id in value['usedCommandIds']:
        raise SpineError('Command ID already used; no duplicate application')
    if type(expected_revision) is not int or expected_revision != value['documentRevision']:
        raise SpineError('Stale edit revision; optimistic concurrency conflict')
    if type(x) is not int or type(y) is not int or not (0 <= x < value['document']['sceneSize'][0] and 0 <= y < value['document']['sceneSize'][1]):
        raise SpineError('Edit cell outside scene')
    if role not in SUPPORTED:
        raise SpineError('Only actual source-supported fixture roles accepted')
    old = value['document']['layers']['terrain'][y][x]
    if old == role:
        raise SpineError('No-op edit rejected; revision remains unchanged')
    value['history'] = value['history'][:value['cursor']]
    if len(value['history']) >= EVENT_LIMIT:
        raise SpineError('Bounded journal full; snapshot/checkpoint before more edits')
    value['usedCommandIds'].append(command_id)
    value['history'].append({'commandId': command_id,'type':'set_terrain','cell':[x,y],
                             'before':old,'after':role})
    value['cursor'] += 1
    value['document']['layers']['terrain'][y][x] = role
    value['documentRevision'] += 1
    value['documentSha256'] = document_sha(value['document'])
    atomic(root,SESSION,value)
    verified_session(root,receipt,gate)
    return value

def step_history(root: Path, receipt: dict, gate: object, *, mode: str, expected_revision: int) -> dict:
    value=verified_session(root,receipt,gate)
    if type(expected_revision) is not int or value['documentRevision'] != expected_revision:
        raise SpineError('Stale undo/redo revision')
    if mode=='undo' and value['cursor']>0:
        event=value['history'][value['cursor']-1]
        value['cursor']-=1
        target=event['before']
    elif mode=='redo' and value['cursor']<len(value['history']):
        event=value['history'][value['cursor']]
        value['cursor']+=1
        target=event['after']
    else:
        raise SpineError('Nothing available to '+mode)
    x,y=event['cell']
    value['document']['layers']['terrain'][y][x]=target
    value['documentRevision']+=1
    value['documentSha256']=document_sha(value['document'])
    atomic(root,SESSION,value)
    verified_session(root,receipt,gate)
    return value

def save_snapshot(root: Path, receipt: dict, gate: object) -> dict:
    value=verified_session(root,receipt,gate)
    snapshot={'schema': SCHEMA+'.saved_snapshot', 'status':'ATOMIC_CANDIDATE_ONLY_SAVE',
              'fixtureSha256':receipt['sceneSha256'],'sourceSha256':receipt['sourceSha256'],
              'sceneId':value['sceneId'],'revision':value['documentRevision'],
              'documentSha256':value['documentSha256'], 'document':value['document'],
              'canonicalSaveMutated':False,'runtimeLoaded':False}
    atomic(root,SAVED,snapshot)
    return snapshot

def reopen(root: Path, receipt: dict, gate: object) -> dict:
    value=verified_session(root,receipt,gate)
    snapshot=load(guard(root)/SAVED)
    if (snapshot.get('schema')!=SCHEMA+'.saved_snapshot' or snapshot.get('fixtureSha256')!=receipt['sceneSha256']
        or snapshot.get('sourceSha256')!=receipt['sourceSha256'] or snapshot.get('sceneId')!=receipt['sceneId']
        or snapshot.get('canonicalSaveMutated') is not False
        or type(snapshot.get('revision')) is not int
        or snapshot.get('documentSha256') != document_sha(snapshot.get('document',{}))):
        raise SpineError('Saved candidate snapshot evidence invalid')
    check_scene(snapshot['document'])
    if snapshot['revision'] != value['documentRevision'] or snapshot['document'] != value['document']:
        raise SpineError('Saved snapshot differs from current isolated session; no silent overwrite')
    return {'schema':SCHEMA+'.reopen','status':'CANDIDATE_SAVE_REOPEN_EQUAL','sceneId':value['sceneId'],
            'revision':value['documentRevision'],'sha256':value['documentSha256'],
            'canonicalSaveMutated':False,'runtimeLoaded':False}

def mapper_queue(root: Path, receipt: dict, gate: object) -> dict:
    value=verified_session(root,receipt,gate)
    grid=value['document']['layers']['terrain']
    width,height=value['document']['sceneSize']
    signatures=defaultdict(lambda: {'count':0,'firstCell':None})
    for y in range(height):
        for x in range(width):
            neighboring=(grid[y-1][x] if y else None,
                         grid[y][x+1] if x+1<width else None,
                         grid[y+1][x] if y+1<height else None,
                         grid[y][x-1] if x else None)
            key=json.dumps([grid[y][x],*neighboring],separators=(',',':'))
            item=signatures[key];item['count']+=1
            if item['firstCell'] is None:item['firstCell']=[x,y]
    variants=[{'roleAndNeighborsNESW':json.loads(key),'count':val['count'],
               'exampleCell':val['firstCell'],'mappingStatus':'UNREVIEWED_NEEDS_MAPPER'}
              for key,val in sorted(signatures.items())]
    result={'schema':SCHEMA+'.mapper_queue','status':'UNREVIEWED_SOURCE_RECIPE_QUEUE',
            'sceneId':value['sceneId'],'documentRevision':value['documentRevision'],
            'documentSha256':value['documentSha256'], 'fixtureSha256':receipt['sceneSha256'],
            'sourceSha256':receipt['sourceSha256'],'roleTopologyVariants':variants,
            'semanticCellCount':width*height,'visuallyApproved':False,'runtimePublished':False,
            'mapperAuthority':'apps/haven_atlas_mapper_lite',
            'assetAuthority':'Havenwild Asset Authority',
            'note':'Review exact source cells/edges/corners/cliffs/waterfalls in existing mapper; no auto-approval'}
    if sum(item['count'] for item in variants)!=width*height:
        raise SpineError('Mapper queue lost semantic cells')
    atomic(root,'mapper_queue.json',result)
    return result

def render_packets(root: Path, receipt: dict, gate: object) -> dict:
    """Actual source coordinates from existing historic draft, NEVER certification."""
    value=verified_session(root,receipt,gate)
    mod_path=Path(__file__).with_name('draft_source_draw_plan.py')
    spec=importlib.util.spec_from_file_location('hw_candidate_draft_for_packets',mod_path)
    if spec is None or spec.loader is None:raise SpineError('Existing draft resolver missing')
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    # Reuse its exact source/role/hash verification rather than create a mapper.
    draft_path=root / CANDIDATE / 'evidence/draft_source_draw_plan.json'
    if draft_path.is_symlink():
        raise SpineError('Historical draft evidence is redirected')
    existing=load(draft_path)
    mapping=(root / 'content/assets/intake/lpc_terrain_family_mapping_v0_3.json').read_bytes()
    binding=(root / mod.BINDINGS).read_bytes()
    if sha(mapping) != '280735da3be341cbbb6a085d45fc14673886a94d24d2b34473ff48878f038307':
        raise SpineError('Historical mapping differs from source-verified C3/C6 pin')
    if (existing.get('schema')!=mod.SCHEMA or existing.get('historicalMappingSha256')!=sha(mapping)
        or existing.get('bindingSha256')!=sha(binding)
        or existing.get('originalSourceSha256')!=receipt['sourceSha256']
        or existing.get('sceneSha256')!=receipt['sceneSha256'] or existing.get('sourceExactArtApproved') is not False
        or existing.get('runtimePublicationAllowed') is not False
        or existing.get('approvedDrawCallCount')!=0):
        raise SpineError('Existing historical draft draw receipt stale/altered or promoted')
    roles=existing.get('draftRoleSourceRects')
    if not isinstance(roles,dict) or set(roles)!=SUPPORTED:
        raise SpineError('Historical role source coordinates incomplete')
    # Derive expected coordinates from exactly the established historical mapping
    # and explicit binding. Neither the draft receipt nor this module may assign
    # new source cells or silently approve old ones.
    mapping_obj=json.loads(mapping)
    binding_obj=json.loads(binding)
    if (binding_obj.get('sourceSha256')!=receipt['sourceSha256']
        or binding_obj.get('historicalMappingSha256')!=sha(mapping)
        or binding_obj.get('runtimePublicationAllowed') is not False
        or binding_obj.get('sourceArtApproval') is not False):
        raise SpineError('Historical bindings are stale or claim publication')
    expected_rects={}
    for entry in binding_obj.get('roleBindings',[]):
        role=entry.get('sceneRole')
        name=entry.get('historicalBaseTile')
        if role in expected_rects or entry.get('sourceVariantIndex')!=0:
            raise SpineError('Duplicate/unapproved historical role binding')
        try:
            col,row=mapping_obj['baseTiles'][name]['cells'][0]
        except (KeyError,IndexError,TypeError,ValueError) as exc:
            raise SpineError('Historical source role absent') from exc
        if type(col) is not int or type(row) is not int:
            raise SpineError('Historical source coordinates malformed')
        expected_rects[role]=[col*32,row*32,32,32]
    if roles!=expected_rects:
        raise SpineError('Draft role coordinates differ from pinned historical source mapping')
    canonical=fixture(root,receipt,gate)
    raw_draws=existing.get('draws')
    width0,height0=canonical['sceneSize']
    if not isinstance(raw_draws,list) or len(raw_draws)!=width0*height0:
        raise SpineError('Historical draw entries incomplete')
    for index,draw in enumerate(raw_draws):
        x0,y0=index%width0,index//width0
        role0=canonical['layers']['terrain'][y0][x0]
        if (not isinstance(draw,dict) or draw.get('x')!=x0 or draw.get('y')!=y0
            or draw.get('terrainRole')!=role0 or draw.get('sourceRectPx')!=expected_rects[role0]
            or draw.get('visualStatus')!='HISTORICAL_COORDINATE_DRAFT_UNREVIEWED'):
            raise SpineError('Historical draft draw entry altered')
    source_rects={}
    for role,rect in roles.items():
        if (not isinstance(rect,list) or len(rect)!=4 or any(type(n) is not int for n in rect)
            or rect[2:]!=[32,32] or rect[0]<0 or rect[1]<0
            or rect[0]%32 or rect[1]%32 or rect[0]+32>512 or rect[1]+32>832):
            raise SpineError('Unverified source rect for '+role)
        source_rects[role]=rect
    doc=value['document'];width,height=doc['sceneSize']
    packets=[]
    for y,row in enumerate(doc['layers']['terrain']):
        for x,role in enumerate(row):
            packets.append({'sceneId':value['sceneId'],'sceneRevision':value['documentRevision'],
                            'cell':[x,y],'semanticTerrainRole':role,'sourceId':'elizawy.terrain.summer.original',
                            'sourceSha256':receipt['sourceSha256'],'sourceRectPx':source_rects[role].copy(),
                            'worldPositionPx':[x*32,y*32],'worldFootprintTiles':[1,1],
                            'layer':'ground_draft','depthOrder':0,'elevation':None,
                            'collisionRef':None,'traversalRef':None,'hydrologyRef':None,
                            'animationClipRef':None,'recipeId':None,'recipeRevision':None,
                            'visualApprovalReceipt':None,'visualStatus':'HISTORICAL_UNAPPROVED_DRAFT'})
    result={'schema':SCHEMA+'.render_packets','status':'RENDERER_NEUTRAL_HISTORICAL_UNAPPROVED_ONLY',
            'sceneId':value['sceneId'],'sceneRevision':value['documentRevision'],
            'sceneSha256':value['documentSha256'],'originalSourceSha256':receipt['sourceSha256'],
            'historicalDraftSha256':sha(encoded(existing)), 'sourceFamily':'ElizaWy',
            'tileSizePx':32,'sizeTiles':doc['sceneSize'],'packets':packets,
            'drawCount':len(packets),'approvedDrawCount':0,'unresolvedRecipeCount':len(packets),
            'sourceExactPixels':True,'sourceExactArtApproved':False,'worldRendererParity':False,
            'runtimePublicationAllowed':False}
    if len(packets)!=width*height:raise SpineError('Renderer plan dropped a scene cell')
    atomic(root,'render_packets.json',result)
    return result

def pie_ticket(root: Path,receipt: dict,gate: object) -> dict:
    snapshot=load(guard(root)/SAVED)
    again=reopen(root,receipt,gate)
    ticket={'schema':SCHEMA+'.pie_ticket','status':'SNAPSHOT_STAGED_ACTUAL_PIE_NOT_IMPLEMENTED',
            'sceneId':snapshot['sceneId'],'sceneRevision':again['revision'],
            'sceneSha256':again['sha256'],'sourceSha256':receipt['sourceSha256'],
            'snapshotSha256':sha(encoded(snapshot)),
            'runtimeAck':None,'hostSessionId':None,'launchAllowed':False,
            'serverAuthoritative':False,'canonicalEstateMutationAllowed':False,
            'saveIsolation':'candidate_local_only',
            'note':'Metadata handshake only; MUST NOT report a real host, gameplay, or PIE launch'}
    atomic(root,'pie_ticket.json',ticket)
    return ticket

def parity(root: Path,receipt: dict,gate: object) -> dict:
    value=verified_session(root,receipt,gate)
    original=fixture(root,receipt,gate)
    doc=value['document'];changed=[]
    for y,(before,after) in enumerate(zip(original['layers']['terrain'],doc['layers']['terrain'])):
        for x,(left,right) in enumerate(zip(before,after)):
            if left!=right:changed.append({'cell':[x,y],'before':left,'after':right})
    status='EDITOR_SEMANTIC_PARITY_ONLY_RENDERER_AND_GAME_PENDING'
    result={'schema':SCHEMA+'.parity','status':status,'sceneId':value['sceneId'],
            'fixtureSha256':receipt['sceneSha256'],'candidateSceneSha256':value['documentSha256'],
            'documentRevision':value['documentRevision'],'changedCellCount':len(changed),
            'changedCells':changed,'semanticGridComplete':True,'sourceUnchanged':True,
            'gpuPixelsReviewed':False,'collisionNavigationVerified':False,
            'runtimeAck':None,'worldRendererParity':False,'pieCertified':False,
            'fullPccGateByThisTool':False}
    atomic(root,'parity.json',result)
    return result

def readiness(root: Path,receipt: dict,gate: object) -> dict:
    folder=guard(root)
    result={'schema':SCHEMA+'.readiness','status':'CANDIDATE_INFRASTRUCTURE_NOT_PROMOTED',
            'projectContext':context(root,receipt,gate),
            'components':{},'staleOrInvalid':[],
            'promotionAllowed':False,'macroquadRetirementAllowed':False,
            'productionAssetPublicationAllowed':False,'actualPieReady':False,
            'pending':['Windows Rust build and GPU screenshot','source-exact mapper certification',
                       'actual game host ACK + collision/navigation parity',
                       'PCC Full Gate against THIS candidate and GUI smoke']}
    session=None
    if (folder/SESSION).is_file():
        session=verified_session(root,receipt,gate)
    for key,file in [('session',SESSION),('savedSnapshot',SAVED),('sourceStack','source_stack.json'),
                     ('mapperQueue','mapper_queue.json'),('drawPackets','render_packets.json'),
                     ('pieTicket','pie_ticket.json'),('semanticParity','parity.json')]:
        path=folder/file
        present=path.is_file()
        item={'present':present,'sha256':sha(path.read_bytes()) if present else None,
              'current':False if not present else True}
        if present:
            data=load(path)
            if key=='sourceStack':
                current=(data.get('schema')==SCHEMA+'.source_stack' and data.get('sourceSha256')==receipt['sourceSha256']
                         and data.get('status')=='SOURCE_BYTES_VERIFIED_NOT_ASSET_APPROVED')
            elif key=='session':
                current=session is not None
            elif key=='savedSnapshot':
                current=(session is not None and data.get('schema')==SCHEMA+'.saved_snapshot'
                         and data.get('documentSha256')==session['documentSha256']
                         and data.get('revision')==session['documentRevision']
                         and data.get('sourceSha256')==receipt['sourceSha256']
                         and data.get('canonicalSaveMutated') is False)
            elif key=='mapperQueue':
                current=(session is not None and data.get('schema')==SCHEMA+'.mapper_queue'
                         and data.get('documentSha256')==session['documentSha256']
                         and data.get('documentRevision')==session['documentRevision']
                         and data.get('visuallyApproved') is False and data.get('runtimePublished') is False)
            elif key=='drawPackets':
                current=(session is not None and data.get('schema')==SCHEMA+'.render_packets'
                         and data.get('sceneSha256')==session['documentSha256']
                         and data.get('sceneRevision')==session['documentRevision']
                         and data.get('originalSourceSha256')==receipt['sourceSha256']
                         and data.get('approvedDrawCount')==0
                         and data.get('runtimePublicationAllowed') is False)
            elif key=='pieTicket':
                current=(session is not None and data.get('schema')==SCHEMA+'.pie_ticket'
                         and data.get('sceneSha256')==session['documentSha256']
                         and data.get('sceneRevision')==session['documentRevision']
                         and data.get('launchAllowed') is False and data.get('runtimeAck') is None)
            else:
                current=(session is not None and data.get('schema')==SCHEMA+'.parity'
                         and data.get('candidateSceneSha256')==session['documentSha256']
                         and data.get('documentRevision')==session['documentRevision']
                         and data.get('worldRendererParity') is False and data.get('pieCertified') is False)
            item['current']=current
            if not current: result['staleOrInvalid'].append(key)
        result['components'][key]=item
    if result['staleOrInvalid']:
        result['status']='REVIEW_REQUIRED_STALE_CANDIDATE_EVIDENCE_NOT_PROMOTED'
    atomic(root,'readiness.json',result)
    return result

def execute(root: Path,action: str, *, command_id: str|None=None,
            revision: int|None=None,x: int|None=None,y: int|None=None,role: str|None=None) -> dict:
    root=root.resolve(strict=True)
    receipt,gate=authority(root)
    if action=='context':return context(root,receipt,gate)
    if action=='source':return source_stack(root,receipt,gate)
    if action=='open':return open_session(root,receipt,gate)
    if action=='edit':return edit(root,receipt,gate,command_id=command_id,expected_revision=revision,x=x,y=y,role=role)
    if action in ('undo','redo'):return step_history(root,receipt,gate,mode=action,expected_revision=revision)
    if action=='save':return save_snapshot(root,receipt,gate)
    if action=='reopen':return reopen(root,receipt,gate)
    if action=='mapper-queue':return mapper_queue(root,receipt,gate)
    if action=='render-packets':return render_packets(root,receipt,gate)
    if action=='pie-plan':return pie_ticket(root,receipt,gate)
    if action=='parity':return parity(root,receipt,gate)
    if action=='audit':return readiness(root,receipt,gate)
    raise SpineError('Unsupported experimental infrastructure operation')

def main(argv: list[str]|None=None)->int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['context','source','open','edit','undo','redo','save','reopen',
                                         'mapper-queue','render-packets','pie-plan','parity','audit'])
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--command-id');parser.add_argument('--revision',type=int)
    parser.add_argument('--x',type=int);parser.add_argument('--y',type=int);parser.add_argument('--role')
    ns=parser.parse_args(argv)
    try:
        result=execute(ns.root,ns.action,command_id=ns.command_id,revision=ns.revision,
                       x=ns.x,y=ns.y,role=ns.role)
        # Never dump 1,120 source packets or entire editable scene into the PCC log.
        print(json.dumps({'schema':result['schema'],'status':result.get('status','PASS'),
                          'sceneId':result.get('sceneId'),'revision':result.get('documentRevision',result.get('revision')),
                          'approvedDrawCount':result.get('approvedDrawCount'),
                          'componentCount':len(result.get('components',{})),
                          'candidateEvidence':str(ns.root.resolve()/ARTIFACTS)},indent=2))
        return 0
    except (SpineError,OSError,ValueError,KeyError,TypeError) as exc:
        print(json.dumps({'status':'BLOCKED','action':ns.action,'error':str(exc)}),file=sys.stderr)
        return 2

if __name__=='__main__':raise SystemExit(main())
