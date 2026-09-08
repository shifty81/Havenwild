#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[5]
CONTRACT=ROOT/'content/buildings/roof_exact_region_review_contract_v1.json'
TOPO=ROOT/'content/buildings/roof_topology_contract_v1.json'
BUILDER=ROOT/'tools/automation/assets/Build-ExactRoofReviewEvidenceV1.py'
INV=ROOT/'content/assets/lpc/structure_source_inventory_v1.json'
WORK=ROOT/'WORKSPACE/generated/structure_review/w45c3_exact_roof/manifest.json'
PUB=ROOT/'content/buildings/roof_exact_region_publication_v1.json'

def need(v,msg):
    if not v: raise SystemExit('FAIL W45C3A: '+msg)
def load(p): return json.loads(p.read_text(encoding='utf-8'))

def main()->int:
    need(CONTRACT.is_file(),'review contract missing'); need(TOPO.is_file(),'roof topology contract missing'); need(BUILDER.is_file(),'evidence builder missing')
    c=load(CONTRACT); t=load(TOPO); inv=load(INV)
    need(c.get('schema')=='havenwild.roof_exact_region_review_contract.v1','review contract schema drift')
    need(c.get('sourceCommit')=='f07f7f5892e67c932c68f70bb04472f2c64e46bc','pinned LPC commit drift')
    families=set(c.get('requiredFamilies',[])); need(len(families)==7,'required roof family count drift')
    roles=set(c.get('requiredSelectionRoles',[])); topo_roles=set(t.get('requiredTopologyRoles',[])); need(roles==topo_roles,'review roles must match roof topology contract')
    policy=c.get('reviewPolicy',{}); need(policy.get('visualHumanReviewRequired') is True,'human review must remain required'); need(policy.get('publishOnlyAfterSelectionManifestIsSourceControlled') is True,'source-controlled publication gate missing')
    roof=[e for e in inv.get('entries',[]) if e.get('role')=='roof']; need(len(roof)==7,'roof inventory count drift')
    reviewed={e.get('sourcePath') for e in roof if e.get('certification',{}).get('componentRectsReviewed')}
    if PUB.is_file():
        pub=load(PUB)
        need(pub.get('schema')=='havenwild.roof_exact_region_publication.v1','W45C3B publication schema drift')
        accepted=set(pub.get('acceptedFamilies',[]))
        family_to_path={f.get('id'):f.get('source') for f in t.get('roofFamilies',[])}
        expected={family_to_path[f] for f in accepted}
        need(reviewed==expected,f'roof reviewed set must exactly match source-controlled W45C3B publication: {sorted(reviewed)}')
    else:
        # W45C3A creates evidence only; before W45C3B no roof sheet may be reviewed.
        need(not reviewed,'roof sheet falsely marked reviewed before W45C3B publication')
    if WORK.is_file():
        e=load(WORK); need(e.get('schema')=='havenwild.exact_roof_review_evidence.v1','machine-local evidence schema drift')
        need(e.get('sourceCommit')==c.get('sourceCommit'),'evidence commit drift')
        for src in e.get('sources',[]):
            need(Path(src['board']).suffix.lower()=='.png','evidence board must be png'); need(src.get('nonEmptyCells',0)>0,'evidence source unexpectedly empty')
        print(f"W45C3A machine-local evidence present: {len(e.get('sources',[]))}/7 source sheet(s)")
    else:
        print('W45C3A machine-local evidence deferred (raw LPC dependency not mounted in this checkout)')
    print('PASS W45C3A exact roof review evidence authority')
    return 0
if __name__=='__main__': raise SystemExit(main())
