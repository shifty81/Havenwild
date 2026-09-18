#!/usr/bin/env python3
"""Read-only B14 audit of the EXISTING authority/catalog routing boundary.

Never changes active runtime, old saves, source mounts, or certification status.
Local evidence is opt-in to keep compact source-only quality gates portable.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PIN = 'f07f7f5892e67c932c68f70bb04472f2c64e46bc'
AUTH = 'content/assets/lpc/lpc_project_asset_authority_v0_1.json'
FOUND = 'content/assets/lpc/lpc_project_foundation_authority_v0_1.json'
COVER = 'content/asset_packs/lpc_revised/lpc_revised_category_coverage_v1.json'
EDITOR = 'content/editor/lpc_project_asset_library_v0_2.json'
LIBRARY = 'content/editor/elizawy_project_asset_library_v0_1.json'
CANDIDATE = 'content/assets/intake/elizawy_only_cutover_candidate_b12.json'
FAMILY = 'content/worldgen/terrain_visual_family_authority_v0_1.json'
REPORT = 'WORKSPACE/generated/lpc/elizawy_b13_report.json'
CATALOG = 'WORKSPACE/generated/lpc/catalogs'
DOMAINS = ('terrain','nature','objects','structure','characters','fx','palette','reference_scenes','repository_support','legal_and_documentation')


def read(root: Path, name: str) -> dict:
    result = json.loads((root / name).read_text(encoding='utf-8-sig'))
    if not isinstance(result, dict):
        raise ValueError(f'{name}: expected JSON object')
    return result


def validate(root: Path, require_local_evidence: bool = False) -> dict:
    root = root.resolve()
    blockers = []
    try:
        a, f, cover, editor, library, candidate, family = (
            read(root, p) for p in (AUTH, FOUND, COVER, EDITOR, LIBRARY, CANDIDATE, FAMILY))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return {'schema':'havenwild.elizawy_candidate_routing.b14', 'status':'BLOCKED',
                'blockers':[f'authority load failure: {exc}'], 'productionApproval':False,
                'runtimeCutover':False}
    policy = a.get('projectPolicy', {})
    if a.get('source',{}).get('commit') != PIN or candidate.get('source',{}).get('commit') != PIN:
        blockers.append('pinned source identity disagrees with B14')
    if policy.get('newAuthoringVisualProvider') != 'elizawy_lpc_revised' or policy.get('newAuthoringFallbackAllowed') is not False:
        blockers.append('project authority does not select ElizaWy exclusively for new authoring')
    if policy.get('sourceTreeIsImmutable') is not True:
        blockers.append('original source mutability policy changed')
    if set(cover.get('providers',[])) != {'elizawy_lpc_revised'}:
        blockers.append('source category coverage still includes competing new-authoring providers')
    if editor.get('providers') != ['elizawy_lpc_revised']:
        blockers.append('editor source-library provider selection is mixed')
    if f.get('projectDomains',{}).get('characters',{}).get('providerPriority') != ['elizawy_lpc_revised']:
        blockers.append('character new-authoring source priority is mixed')
    if f.get('projectDomains',{}).get('world',{}).get('providerPriority') != ['elizawy_lpc_revised']:
        blockers.append('world source priority is mixed')
    if f.get('projectDomains',{}).get('newAuthoringPolicy',{}).get('fallbackProviders') != []:
        blockers.append('new-authoring fallback provider list is nonempty')
    if candidate.get('activation',{}).get('enabled') is not False:
        blockers.append('unsafe premature runtime activation requested')
    if family.get('activeOpenWorldFamily') != 'lpc_terrain_v7_island_v1':
        blockers.append('runtime selector changed before certified editor/client migration')
    for item in library.get('collections',[]):
        if item.get('allowRuntimePromotion') is not False:
            blockers.append(f"uncertified runtime promotion enabled in {item.get('id')}")
    if not library.get('collections'):
        blockers.append('ElizaWy source library has no collections')
    source = {'status':'not_checked', 'verifiedFiles':0,'quarantinedAssets':[]}
    if require_local_evidence and not (root / 'assets/source/licensed/lpc_revised').is_dir():
        blockers.append('physical licensed source mount missing; B13 report alone is not sufficient')
    report_path = root / REPORT
    if report_path.is_file():
        try:
            report = read(root, REPORT)
            counts = report.get('source',{})
            good = (report.get('status') in ('SOURCE_REPRODUCED_WITH_QUARANTINE','SOURCE_REPRODUCED')
                and report.get('pinnedCommit') == PIN
                and counts.get('verificationDepth') == 'full_file_hashes'
                and counts.get('verifiedFiles') == report.get('historicalInventory',{}).get('indexedFiles')
                and all(counts.get(k) == 0 for k in ('missingIndexed','mismatchedIndexed','unexpectedFiles','invalidImages'))
                and not report.get('blockers') and report.get('productionApproval') is False)
            source = {'status':'verified_report' if good else 'invalid_or_incomplete_report',
                      'verifiedFiles':counts.get('verifiedFiles',0),
                      'quarantinedAssets':[x.get('relativePath') for x in report.get('quarantinedAssets',[])]}
            if require_local_evidence and not good:
                blockers.append('local full-index B13 source evidence is invalid/incomplete')
        except (OSError,ValueError,json.JSONDecodeError) as exc:
            source['status'] = 'invalid_report'
            if require_local_evidence: blockers.append(f'cannot parse B13 full-index report: {exc}')
    elif require_local_evidence:
        blockers.append('full-index B13 report missing; run the B13 certification command')
    catalog_status = 'not_generated'
    counted_records = 0
    quarantined_catalog_paths = set()
    if all((root / CATALOG / f'{domain}.json').is_file() for domain in DOMAINS):
        catalog_status = 'available_not_inspected'
        for domain in DOMAINS:
            try:
                catalog = read(root,f'{CATALOG}/{domain}.json')
                if catalog.get('newAuthoringProvider') != 'elizawy_lpc_revised' or catalog.get('productionApprovedRecordCount') != 0:
                    blockers.append(f'{domain} catalog was not built with B14 source-only eligibility')
                    continue
                records = catalog.get('records')
                if not isinstance(records,list) or catalog.get('recordCount') != len(records) or catalog.get('sourceCommit') != PIN:
                    blockers.append(f'{domain} catalog record count or source revision disagrees')
                    continue
                counted_records += len(records)
                for entry in records:
                    if entry.get('candidateProvider') != 'elizawy_lpc_revised' or entry.get('productionApproved') is not False:
                        blockers.append(f'{domain} contains a non-ElizaWy or prematurely approved entry')
                        break
                    if entry.get('productionState') == 'QUARANTINED':
                        quarantined_catalog_paths.add(entry.get('sourcePath'))
                    if entry.get('sourceSizeBytes') == 0 and entry.get('sourceKind') == 'image' and entry.get('productionState') != 'QUARANTINED':
                        blockers.append(f'{domain} zero-byte artwork not quarantined')
                        break
            except (OSError,ValueError,json.JSONDecodeError) as exc:
                blockers.append(f'{domain} catalog unreadable: {exc}')
        if require_local_evidence and source['status'] == 'verified_report':
            if counted_records != source['verifiedFiles']:
                blockers.append(f'candidate catalog coverage {counted_records}/{source["verifiedFiles"]} does not match B13')
            if quarantined_catalog_paths != set(source['quarantinedAssets']):
                blockers.append('candidate catalog quarantine paths do not match B13 source quarantine')
        if not blockers: catalog_status = 'source_only_candidate_catalogs_verified'
    elif require_local_evidence:
        blockers.append('domain catalogs absent: generate with the existing Build-ElizaWyProjectAssetAuditV167Z38.py --force --strict')
    return {'schema':'havenwild.elizawy_candidate_routing.b14',
            'status':'BLOCKED' if blockers else 'SOURCE_ONLY_CANDIDATE_CATALOGS_VERIFIED' if catalog_status == 'source_only_candidate_catalogs_verified' and source['status']=='verified_report' else 'POLICY_STAGED_NOT_RUNTIME_ACTIVE',
            'source':source,'catalogs':catalog_status,'newAuthoringProvider':'elizawy_lpc_revised',
            'legacyProviderHandling':'reference_only_legacy_save_compatibility',
            'runtimeCutover':False,'productionApproval':False,
            'visualApproval':False,'blockers':blockers,
            'next':'Next: certify mappings/assemblies, character/equipment, license and editor/client runtime; do not flip V7 active selector yet.'}


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=ROOT)
    parser.add_argument('--require-local-evidence',action='store_true')
    parser.add_argument('--report',type=Path)
    args=parser.parse_args()
    result=validate(args.root, args.require_local_evidence)
    if args.report:
        p=args.report if args.report.is_absolute() else args.root/args.report
        p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
    print('B14 candidate routing:',result['status'])
    print('Source:',result['source']['status'],'; catalogs:',result['catalogs'])
    for blocker in result['blockers'][:20]:print('BLOCKER:',blocker)
    return 2 if result['blockers'] else 0

if __name__=='__main__':
    raise SystemExit(main())
