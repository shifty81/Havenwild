#!/usr/bin/env python3
"""Existing PCC's experimental-only candidate operations, not an independent PCC.

All verification is read-only. Cargo outputs stay within the isolated candidate;
this tool never writes the canonical game, source library, recipe catalog or saves.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

BASELINE = '78ff838499015ff434dbd935ae5daf9cbd11a02e'
CANDIDATE = Path('experiments/haven_bevy_candidate')
SOURCE = Path('assets/source/Terrain/terrain_summer.png')
CREDITS = Path('assets/source/Terrain/Credits.txt')
RECEIPT = Path('evidence/source_stage.json')
SCENE = Path('content/worldgen/scenes/terrain_acceptance/river_scene_v1.json')
SOURCE_SHA = '1251a6ea556330190ccb1e3af166eb69fbec4b7a3f7d51c1f54728abd75bd752'
FORGE_PIN = 'eafa8e78efd54142a19e66d8be7b7d3985af23d2'

class GateError(ValueError):
    pass

def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()

def git(root: Path, *args: str) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(['git','-C',str(root),*args],capture_output=True,text=True,timeout=10,check=False)
    except (OSError,subprocess.TimeoutExpired) as exc:
        raise GateError(f'Git unavailable: {exc}') from exc

def project(root: Path) -> Path:
    root=root.resolve(strict=True)
    if not (root/'Cargo.toml').is_file() or not (root/'tools/forge/HavenwildPccProvider.py').is_file():
        raise GateError('Not a Havenwild project with its existing PCC')
    candidate=root/CANDIDATE
    if not candidate.is_dir() or (root/'experiments').is_symlink() or candidate.is_symlink() or not (candidate/'Cargo.toml').is_file():
        raise GateError('Candidate missing or redirected; do not use another workspace')
    for relative in [Path('assets'), Path('assets/source'), Path('assets/source/Terrain'),
                     Path('evidence'), SOURCE, CREDITS, RECEIPT]:
        path=candidate/relative
        if path.is_symlink():
            raise GateError(f'Candidate source/receipt path is a symlink: {relative}')
    return candidate

def lane(root: Path) -> dict:
    branch=git(root,'symbolic-ref','--quiet','--short','HEAD')
    head=git(root,'rev-parse','HEAD')
    if branch.returncode or head.returncode or branch.stdout.strip()!='experimental':
        raise GateError('Experimental branch required; main, detached, and unavailable Git are blocked')
    ancestor=git(root,'merge-base','--is-ancestor',BASELINE,'HEAD')
    if ancestor.returncode:
        raise GateError('Current experimental checkout is not descended from B48R28B GREEN')
    return {'branch':branch.stdout.strip(),'head':head.stdout.strip(),'requiredAncestor':BASELINE}

def verify(root: Path) -> dict:
    candidate=project(root)
    lineage=lane(root)
    manifest=(candidate/'Cargo.toml').read_text(encoding='utf-8')
    for token in ['[workspace]','bevy = "=0.19.0"','bevy_egui = "=0.42.0"',FORGE_PIN]:
        if token not in manifest:
            raise GateError(f'Candidate Rust manifest missing pinned dependency contract: {token}')
    if 'macroquad' in manifest.lower():
        raise GateError('Candidate Rust manifest unexpectedly depends on Macroquad')
    source=candidate/SOURCE
    credits=candidate/CREDITS
    receipt_path=candidate/RECEIPT
    if not source.is_file() or not credits.is_file() or not receipt_path.is_file():
        raise GateError('Original source/credits/receipt are missing; stage Terrain.zip through prepare_source.py')
    source_hash=digest(source.read_bytes())
    if source_hash!=SOURCE_SHA:
        raise GateError('Original ElizaWy source bytes differ from approved pinned SHA')
    try:
        receipt=json.loads(receipt_path.read_text(encoding='utf-8'))
    except (json.JSONDecodeError,UnicodeError) as exc:
        raise GateError(f'Invalid source-stage receipt: {exc}') from exc
    if (receipt.get('sourceSha256')!=source_hash
        or receipt.get('creditsSha256')!=digest(credits.read_bytes())
        or receipt.get('publicationStatus')!='candidate_only'
        or receipt.get('originalSourceMutated') is not False
        or receipt.get('canonicalSaveMutated') is not False
        or receipt.get('branch')!='experimental'
        or receipt.get('baselineAncestor') is not True):
        raise GateError('Stale/incorrect source-stage evidence; no source approval')
    fixture=root/SCENE
    if not fixture.is_file() or fixture.is_symlink():
        raise GateError('Canonical scene fixture absent or redirected')
    scene_raw=fixture.read_bytes()
    evidence=receipt.get('fixture')
    if not isinstance(evidence,dict) or evidence.get('path')!=SCENE.as_posix() or evidence.get('sha256')!=digest(scene_raw):
        raise GateError('Scene fixture has changed since source staging; restage/review before running')
    try:
        scene=json.loads(scene_raw)
    except (json.JSONDecodeError,UnicodeError) as exc:
        raise GateError(f'Invalid canonical scene JSON: {exc}') from exc
    if not isinstance(scene,dict):
        raise GateError('Scene fixture must be a JSON object')
    size=scene.get('sceneSize')
    layers=scene.get('layers')
    grid=layers.get('terrain') if isinstance(layers,dict) else None
    if (scene.get('kind')!='worldgen_scene' or scene.get('tileSize')!=[32,32]
        or not isinstance(size,list) or len(size)!=2 or any(type(v) is not int or v<1 or v>2048 for v in size)
        or not isinstance(grid,list) or len(grid)!=size[1]
        or any(not isinstance(row,list) or len(row)!=size[0] or any(not isinstance(cell,str) for cell in row) for row in grid)):
        raise GateError('Unsupported/incomplete canonical scene fixture')
    if scene.get('sceneId')!=evidence.get('sceneId') or size!=evidence.get('dimensions'):
        raise GateError('Scene identity/dimensions changed since source staging')
    return {'schema':'havenwild.b48r28c.candidate_input_verification.v1',
            'status':'INPUTS_VERIFIED_NOT_RENDERER_OR_GAME_PARITY',
            'projectRoot':str(root),'candidateRoot':str(candidate),
            'lineage':lineage,'sourceSha256':source_hash,'sceneSha256':digest(scene_raw),
            'sceneId':scene['sceneId'],'size':size,'semanticCells':size[0]*size[1],
            'sourceExactArtApproved':False,'worldRendererParity':False,'pieCertified':False,
            'pccFullGate':'NOT_RUN_BY_THIS_TOOL'}


def prepare_missing_inputs(root: Path) -> None:
    """Only Build/Run hydrate local candidate inputs, never Verify/Status.

    Reuse the existing project ElizaWy dependency first. No silent downloads,
    source guessing, scanning Downloads, or replacing damaged staged evidence.
    The independent staging module enforces branch/ancestry before ANY writes.
    """
    candidate=project(root)
    lane(root)
    source, credits, receipt=(candidate/SOURCE,candidate/CREDITS,candidate/RECEIPT)
    if source.is_file() and credits.is_file() and receipt.is_file():
        return
    if receipt.exists():
        raise GateError('Staged source/credits are missing but receipt exists; inconsistent evidence; refusing automatic repair')
    module_path=Path(__file__).with_name('prepare_source.py')
    spec=importlib.util.spec_from_file_location('havenwild_candidate_original_source_stage',module_path)
    if spec is None or spec.loader is None:
        raise GateError('Original source staging implementation missing')
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    explicit=os.environ.get('HAVENWILD_BEVY_TERRAIN_ZIP','').strip()
    archive=Path(explicit).expanduser() if explicit else root/'Terrain.zip'
    source_root=root/module.INSTALLED_SOURCE
    if source_root.is_dir():
        selected=None
        print(f'[PCC] Reusing pinned project ElizaWy source: {source_root}',flush=True)
    elif archive.is_file():
        selected=archive
        print(f'[PCC] Staging explicit/local original Terrain.zip: {archive}',flush=True)
    else:
        raise GateError(
            'Original ElizaWy source is not installed at '
            f'{source_root}; Terrain.zip is also unavailable at {archive}. '
            'Restore the existing LPC source dependency or run prepare_source.py '
            '--terrain-zip "PATH_TO_ORIGINAL_Terrain.zip". No network/download scan attempted.'
        )
    try:
        staged=module.stage(selected,candidate,root)
    except (module.SourceError,ValueError,OSError) as exc:
        raise GateError(f'Original source staging failed: {exc}') from exc
    print('[PCC] Original source staged as candidate_only: '
          f'{staged["sourceSha256"]}; not asset certification',flush=True)


def inspect_cargo_lock(candidate: Path) -> dict:
    """Inspect local Cargo resolution, never confuse it with certified dependencies.

    Cargo.lock is intentionally not fabricated or packaged here; Windows Cargo
    creates it from actual registry and pinned Git resolutions on its first run.
    """
    path = candidate / 'Cargo.lock'
    if path.is_symlink() or (path.exists() and not path.is_file()):
        raise GateError('Candidate Cargo.lock is redirected or not a file; fail closed')
    if not path.exists():
        return {'status':'NOT_GENERATED','sha256':None,'trackedByPatch':False}
    raw = path.read_bytes()
    try:
        lock = tomllib.loads(raw.decode('utf-8'))
    except (UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
        raise GateError(f'Candidate Cargo.lock is malformed: {exc}') from exc
    versions = {pkg.get('name'):pkg.get('version') for pkg in lock.get('package',[]) if isinstance(pkg,dict)}
    if (lock.get('version') not in (3,4) or versions.get('bevy') != '0.19.0'
            or versions.get('bevy_egui') != '0.42.0'):
        raise GateError('Candidate lock no longer resolves pinned Bevy 0.19.0 / bevy_egui 0.42.0')
    return {'status':'LOCAL_RESOLVED_NOT_PATCH_PINNED','sha256':digest(raw),'trackedByPatch':False,
            'bevy':versions['bevy'],'bevyEgui':versions['bevy_egui']}


def write_cargo_attempt(candidate: Path, receipt: dict) -> Path:
    """Retain build/run exit evidence in ignored candidate space only."""
    evidence = candidate / 'evidence'
    path = evidence / 'cargo_attempt.json'
    if evidence.is_symlink() or path.is_symlink() or (path.exists() and not path.is_file()):
        raise GateError('Candidate Cargo attempt evidence destination is redirected')
    evidence.mkdir(parents=True, exist_ok=True)
    data = (json.dumps(receipt, indent=2, sort_keys=True) + '\n').encode('utf-8')
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=evidence,prefix='.cargo-attempt-',delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(data)
        os.replace(temporary,path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return path

def run(root: Path, action: str) -> int:
    if action=='status':
        project(root)
        lineage=lane(root)
        c=root/CANDIDATE
        print(json.dumps({'schema':'havenwild.b48r28c.candidate_status.v1',
             'status':'EXPERIMENTAL_NOT_PROMOTED','lineage':lineage,
             'sourceStaged':(c/SOURCE).is_file(),'receiptPresent':(c/RECEIPT).is_file(),
             'candidateManifest':str(c/'Cargo.toml'),'pcc':'project_owned_existing_only'},indent=2))
        return 0
    if action in ('build','run'):
        prepare_missing_inputs(root)
    evidence=verify(root)
    print(json.dumps(evidence,indent=2),flush=True)
    if action=='verify':
        return 0
    # A single candidate-local semantic receipt is shared by the build/run
    # workflow. It does not create a second scene or approve source art.
    # Resolve companion by exact on-disk path even when the PCC gate is loaded
    # through an importlib-based test harness (which does not add tools to sys.path).
    import importlib.util
    module_path=Path(__file__).with_name('semantic_scene_plan.py')
    spec=importlib.util.spec_from_file_location('havenwild_candidate_semantic_scene_plan',module_path)
    if spec is None or spec.loader is None:
        raise GateError('Semantic scene compiler unavailable')
    semantic_scene_plan=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(semantic_scene_plan)
    plan=semantic_scene_plan.compile_plan((root/SCENE).read_bytes(),
           source_sha=evidence['sourceSha256'],fixture_sha=evidence['sceneSha256'])
    plan_path=semantic_scene_plan.write_candidate_plan(root,plan)
    print(f'[PCC] Read-only semantic scene plan: {plan_path} ({plan["unmappedCellCount"]} unmapped)',flush=True)
    if action=='scene-plan':
        return 0
    draft_path=Path(__file__).with_name('draft_source_draw_plan.py')
    draft_spec=importlib.util.spec_from_file_location('havenwild_candidate_draft_source_draw_plan',draft_path)
    if draft_spec is None or draft_spec.loader is None:
        raise GateError('Original-pixel draft compiler unavailable')
    draft_mod=importlib.util.module_from_spec(draft_spec)
    draft_spec.loader.exec_module(draft_mod)
    mapping_raw=(root/'content/assets/intake/lpc_terrain_family_mapping_v0_3.json').read_bytes()
    binding_raw=(root/draft_mod.BINDINGS).read_bytes()
    draft=draft_mod.compile_draft(plan,mapping_raw,binding_raw,
        source_hash=evidence['sourceSha256'],fixture_hash=evidence['sceneSha256'])
    draft_receipt=draft_mod.write_draft(root,draft)
    print(f'[PCC] Original-pixel GPU DRAFT: {draft_receipt} ({draft["unreviewedDrawCount"]} unapproved; 0 approved)',flush=True)
    if action=='draft-plan':
        return 0
    candidate=root/CANDIDATE
    # Use one isolated Cargo manifest. Never invoke the legacy game or editor.
    backend = os.environ.get('WGPU_BACKEND', '').strip().lower()
    probe = os.environ.get('HAVENWILD_BEVY_PRIMARY_ONLY', '').strip()
    if action == 'run' and backend not in ('', 'vulkan', 'dx12', 'gl'):
        raise GateError('Invalid WGPU_BACKEND; use auto, vulkan, dx12 or gl through the PCC diagnostic commands')
    if action == 'run' and probe not in ('', '1'):
        raise GateError('Invalid HAVENWILD_BEVY_PRIMARY_ONLY; only 1 or unset is supported')
    if action == 'run':
        print(f'[PCC] GPU differential request: backend={backend or "AUTO"}, '
              f'primaryOnly={probe == "1"}; actual adapter/backend must be checked in Bevy logs', flush=True)
    locked_before = inspect_cargo_lock(candidate)
    cmd=['cargo','check' if action=='build' else 'run','--manifest-path',str(candidate/'Cargo.toml')]
    if locked_before['sha256']:
        cmd.append('--locked')
        print(f'[PCC] Using locally resolved Cargo.lock SHA-256: {locked_before["sha256"]}',flush=True)
    else:
        print('[UNCERTIFIED] Candidate Cargo.lock absent; first Cargo invocation will resolve dependencies. '
              'Generated lock must be reviewed and committed through PCC before reproducibility is claimed.',flush=True)
    print('[PCC] Delegating candidate Cargo operation: '+' '.join(cmd),flush=True)
    try:
        exit_code=subprocess.call(cmd,cwd=candidate)
    except OSError as exc:
        raise GateError(f'Cargo unavailable: {exc}') from exc
    locked_after = inspect_cargo_lock(candidate)
    status = ('CARGO_NONZERO_NOT_RENDERED' if exit_code else
              'CARGO_CHECK_PASSED_NO_GPU_EXECUTION' if action == 'build' else
              'CARGO_RUN_EXITED_ZERO_GPU_VISUAL_REVIEW_STILL_REQUIRED')
    receipt_path = write_cargo_attempt(candidate,{
        'schema':'havenwild.experimental.cargo_attempt.v0_1','status':status,
        'action':action,'exitCode':exit_code,'command':cmd,
        'backendRequested':backend or 'AUTO', 'primaryOnlyProbe':probe == '1',
        'actualGpuBackend':'SEE_BEVY_ADAPTER_INFO_NOT_INFERRED',
        'gpuValidation':'NOT_CAPTURED_BY_THIS_CARGO_EXIT_RECEIPT',
        'candidateManifestSha256':digest((candidate/'Cargo.toml').read_bytes()),
        'lineage':evidence['lineage'], 'sourceSha256':evidence['sourceSha256'],
        'sceneSha256':evidence['sceneSha256'],'lockBefore':locked_before,'lockAfter':locked_after,
        'gpuRendered':None,'worldRendererParity':False,'pieCertified':False,
        'pccFullGate':'NOT_RUN_BY_THIS_TOOL',
    })
    print(f'[PCC] Candidate Cargo result {exit_code}; attempt evidence: {receipt_path}; '
          f'GPU visual parity NOT certified',flush=True)
    return exit_code

def main(argv: list[str]|None=None)->int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['status','verify','scene-plan','draft-plan','build','run'])
    parser.add_argument('--root',type=Path,required=True)
    args=parser.parse_args(argv)
    try:
        return run(args.root.resolve(strict=True),args.action)
    except (GateError,OSError,ValueError) as exc:
        print(json.dumps({'status':'BLOCKED','error':str(exc),'action':args.action}),file=sys.stderr)
        return 2

if __name__=='__main__':
    raise SystemExit(main())
