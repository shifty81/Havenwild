#!/usr/bin/env python3
"""B48R12 fail-closed metadata/source contact audit. Not renderer/collision certification."""
import argparse, copy, hashlib, io, json, pathlib, sys, zipfile
ROOT=pathlib.Path(__file__).resolve().parents[5]
REPORT='content/assets/lpc/elizawy_cliff_water_contact_evidence_b48r12_v0_1.json'
R11='content/assets/lpc/elizawy_cliff_water_role_audit_b48r11_v0_1.json'
W14='content/worldgen/elizawy_cliff_source_grammar_authority_v0_1.json'
def sha(data): return hashlib.sha256(data).hexdigest()
def validate(mapping, older, w14):
    assert mapping['schema']=='havenwild.elizawy.cliff_water_contact_evidence.b48r12.v0_1'
    assert all(mapping[key] is False for key in ('productionEnabled','editorClientRecipeEnabled','validForWorldgenPlacement'))
    assert all(older[key] is False for key in ('productionEnabled','editorClientRecipeEnabled','validForWorldgenPlacement'))
    assert older['measurements']['b48r10RecoveredTransitionPlacements']==0
    assert older['measurements']['b48r10VisualApproval'] is False
    assert older['source']['sha256']==mapping['sourceAuthority']['splitWaterfallTransitions']['sha256']
    assert w14['ordinarySouthRoles']['straight']['crest']==[2,7]
    assert w14['ordinarySouthRoles']['straight']['body']==[2,3]
    assert w14['ordinarySouthRoles']['straight']['foot']==[2,8]
    s=mapping['sourceAddressReview']
    assert (s['recoveredTransitionGridAddresses'],s['artworkCells'],s['transparentCells'],s['animatedCliffWaterGridAddresses'])==(42,40,[[4,6],[5,6]],42)
    assert s['direct32x32UncompositedOpaqueMatchesInArtistDemo']=={'transitionSheet':0,'animatedWaterSheet':0}
    assert len(mapping['artistDemoContactRegions'])==4
    ids=[x['id'] for x in mapping['contactGates']]
    assert ids==['CW%02d'%i for i in range(1,11)]
    assert all(x['sourceRoleCertified'] is False and x['joinCertified'] is False and x['runtimeEnabled'] is False for x in mapping['contactGates'])
    retired=mapping['withdrawnB48R10']
    assert (retired['status'],retired['knownRecoveredTransitionPlacements'],retired['floatingCliffBodyCells'])==('rejected_preview_not_a_gameplay_recipe',0,10)
    assert retired['doNotRebuildRejectedPreview'] is True and retired['doNotShipCandidateFixture'] is True
    policy=mapping['structuralPolicy']
    assert policy['baselineWorldAuthority']==W14
    assert policy['baselinePolicyStatus']=='retired_by_elizawy_first_heightmap_reset'
    assert policy['genericEditorLevelOneAllowed'] is True
    assert policy['genericStandaloneOneHighCliffAllowed'] is True
    assert policy['currentEngineMigrationCompleted'] is False and policy['maxTargetTestElevation']==30
    assert policy['approvedTrueCliffExampleWaterLevelChain']==[2,1,0]
    assert policy['exampleChainIsPlayableFixture'] is False
    assert mapping['validationStatus']=='preflight_not_runtime_certification'
    for region in mapping['artistDemoContactRegions']:
        x0,y0,x1,y1=region['sourceRectPx']
        assert 0<=x0<x1<=1024 and 0<=y0<y1<=1184
        assert len(region['croppedRGBAsha256'])==64

def check_sources(mapping, pack, terrain, scenes):
    from PIL import Image
    with zipfile.ZipFile(pack) as pk,zipfile.ZipFile(terrain) as tr,zipfile.ZipFile(scenes) as sc:
        keys={'originalArtistDemo':sc,'originalCliff':tr,'splitWaterfallTransitions':pk,'splitAnimatedCliffWater':pk}
        for name,z in keys.items():
            meta=mapping['sourceAuthority'][name]
            assert sha(z.read(meta['member']))==meta['sha256'],name+' source changed'
        member=mapping['sourceAuthority']['originalArtistDemo']['member']
        img=Image.open(io.BytesIO(sc.read(member))).convert('RGBA')
        assert img.size==(1024,1184)
        for region in mapping['artistDemoContactRegions']:
            raw=img.crop(tuple(region['sourceRectPx'])).tobytes()
            assert sha(raw)==region['croppedRGBAsha256'],region['label']+' pixels changed'
    return True

def check_self_test(mapping, older, w14):
    cases=[('premature runtime',lambda x:x.__setitem__('productionEnabled',True)),
           ('rejected scene promotion',lambda x:x['withdrawnB48R10'].__setitem__('doNotShipCandidateFixture',False)),
           ('old level-1 ban reintroduced',lambda x:x['structuralPolicy'].__setitem__('genericEditorLevelOneAllowed',False)),
           ('premature contact certification',lambda x:x['contactGates'][0].__setitem__('joinCertified',True)),
           ('transparent tile promotion',lambda x:x['sourceAddressReview'].__setitem__('transparentCells',[]))]
    for label,mutate in cases:
        candidate=copy.deepcopy(mapping);mutate(candidate)
        try: validate(candidate,older,w14)
        except AssertionError: continue
        raise AssertionError('self-test failed to reject '+label)
    return len(cases)

def main():
    p=argparse.ArgumentParser();p.add_argument('--repo',type=pathlib.Path,default=ROOT)
    for name in ('reference-pack','terrain','scenes'):p.add_argument('--'+name,type=pathlib.Path)
    p.add_argument('--self-test',action='store_true');a=p.parse_args()
    mapping=json.loads((a.repo/REPORT).read_text(encoding='utf8'))
    older=json.loads((a.repo/R11).read_text(encoding='utf8'))
    w14=json.loads((a.repo/W14).read_text(encoding='utf8'))
    validate(mapping,older,w14)
    print('PASS B48R12 source-role gates, rejected R10 quarantine, W14, 10 unresolved contacts, retired +1 ban (engine migration pending)')
    if a.self_test: print('PASS B48R12 negative mutation tests:',check_self_test(mapping,older,w14))
    args=[a.reference_pack,a.terrain,a.scenes]
    if any(args):
        assert all(args),'Provide all three original archives together'
        check_sources(mapping,*args)
        print('PASS B48R12 original image byte SHA and 4 actual-demo RGBA crop hashes')
    else: print('NOT RUN original archive pixels: provide --reference-pack, --terrain and --scenes')
if __name__=='__main__':
    try:main()
    except Exception as exc:print('FAIL B48R12',repr(exc),file=sys.stderr);sys.exit(1)
