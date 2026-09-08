#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
TOPO = ROOT / 'content/buildings/structure_support_topology_contract_v1.json'
CONTRACT = ROOT / 'content/buildings/structure_support_exact_region_review_contract_v1.json'
BUILDER = ROOT / 'tools/automation/assets/Build-StructureSupportReviewEvidenceV1.py'
INV = ROOT / 'content/assets/lpc/structure_source_inventory_v1.json'
WORK = ROOT / 'WORKSPACE/generated/structure_review/w45d_exact_support/manifest.json'
PUB = ROOT / 'content/buildings/structure_support_exact_region_publication_v1.json'


def need(value, msg):
    if not value:
        raise SystemExit('FAIL W45D1: ' + msg)


def load(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def main() -> int:
    need(TOPO.is_file(), 'structure support topology contract missing')
    need(CONTRACT.is_file(), 'exact-region review contract missing')
    need(BUILDER.is_file(), 'structure support evidence builder missing')
    need(INV.is_file(), 'structure source inventory missing')

    topo = load(TOPO); contract = load(CONTRACT); inv = load(INV)
    need(topo.get('schema') == 'havenwild.structure_support_topology_contract.v1', 'topology contract schema drift')
    need(contract.get('schema') == 'havenwild.structure_support_exact_region_review_contract.v1', 'review contract schema drift')
    commit = 'f07f7f5892e67c932c68f70bb04472f2c64e46bc'
    need(topo.get('sourceCommit') == commit and contract.get('sourceCommit') == commit, 'pinned LPC commit drift')

    families = topo.get('families', [])
    need(len(families) == 9, 'support source family count must remain 9')
    by_role = {}
    for family in families:
        by_role[family.get('role')] = by_role.get(family.get('role'), 0) + 1
    need(by_role == {'bridge': 5, 'platform': 2, 'pillar': 2}, f'support role counts drift: {by_role}')
    need(set(contract.get('requiredFamilies', [])) == {f.get('id') for f in families}, 'review/topology source-family mismatch')
    need(contract.get('requiredRoleGroups') == topo.get('requiredTopologyRoles'), 'review role groups must match topology contract')

    policy = contract.get('reviewPolicy', {})
    need(policy.get('exactSourceRectRequired') is True, 'exact source region gate missing')
    need(policy.get('visualHumanReviewRequired') is True, 'human visual review gate missing')
    need(policy.get('generatedEvidenceIsNotRuntimeAuthority') is True, 'generated evidence must remain non-authoritative')
    need(policy.get('publishOnlyAfterSelectionManifestIsSourceControlled') is True, 'source-controlled publication gate missing')

    bridge = [e for e in inv.get('entries', []) if e.get('role') == 'bridge']
    platform = [e for e in inv.get('entries', []) if e.get('role') == 'platform']
    pillar = [e for e in inv.get('entries', []) if e.get('role') == 'pillar']
    need(len(bridge) == 5, 'bridge inventory count drift')
    need(len(platform) == 2, 'platform inventory count drift')
    need(len(pillar) == 2, 'pillar inventory count drift')
    reviewed={entry.get('sourcePath') for entry in bridge + platform + pillar if entry.get('certification',{}).get('componentRectsReviewed')}
    if PUB.is_file():
        pub=load(PUB)
        need(pub.get('schema')=='havenwild.structure_support_exact_region_publication.v1','W45D2 publication schema drift')
        accepted=set(pub.get('acceptedFamilies',[]))
        family_to_path={f.get('id'):f.get('source') for f in families}
        expected={family_to_path[f] for f in accepted}
        need(reviewed==expected,f'support reviewed set must exactly match source-controlled W45D2 publication: {sorted(reviewed)}')
    else:
        # W45D1 creates evidence/grammar only; before W45D2 no support sheet may be reviewed.
        need(not reviewed,'support source falsely marked reviewed before W45D2')

    bridge_policy = topo.get('bridgePolicy', {})
    need(bridge_policy.get('bridgeIsAssemblyNotPlaceableSheet') is True, 'bridge assembly policy missing')
    need(bridge_policy.get('bankSocketsRequiredBeforeW46Publication') is True, 'bridge bank-socket gate missing')
    need(bridge_policy.get('collisionFollowsWalkableDeckNotVisualRails') is True, 'bridge collision policy drift')
    platform_policy = topo.get('platformPolicy', {})
    need(platform_policy.get('platformDoesNotMasqueradeAsTerrainElevation') is True, 'platform/terrain authority boundary missing')
    pillar_policy = topo.get('pillarPolicy', {})
    need(pillar_policy.get('pillarVisualHeightDoesNotChangeSimulationLevel') is True, 'pillar/elevation authority boundary missing')

    if WORK.is_file():
        evidence = load(WORK)
        need(evidence.get('schema') == 'havenwild.exact_structure_support_review_evidence.v1', 'machine-local evidence schema drift')
        need(evidence.get('sourceCommit') == commit, 'machine-local evidence source commit drift')
        for src in evidence.get('sources', []):
            need(Path(src['board']).suffix.lower() == '.png', 'support evidence board must be png')
            need(src.get('nonEmptyCells', 0) > 0, 'support evidence source unexpectedly empty')
        print(f"W45D1 machine-local support evidence present: {len(evidence.get('sources', []))}/9 source sheet(s)")
    else:
        print('W45D1 machine-local support evidence deferred (raw LPC dependency not mounted in this checkout)')

    print('PASS W45D1 bridge/platform/pillar topology + exact review evidence authority')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
