#!/usr/bin/env python3
from __future__ import annotations
import gzip,json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
def main():
    policy=json.loads((ROOT/'content/assets/intake/universal_lpc_sharealike_intake_v0_1.json').read_text())
    with gzip.open(ROOT/'content/assets/lpc/universal_lpc_sharealike_catalog_v0_1.json.gz','rt',encoding='utf-8') as f:cat=json.load(f)
    records=cat.get('records',[])
    if policy.get('enabled') is not True:raise SystemExit('ShareAlike intake must be enabled')
    if len(records)!=2038 or cat.get('recordCount')!=2038:raise SystemExit(f'Expected 2038 ShareAlike records, found {len(records)}')
    allowed=set(policy['allowedLicenses'])
    for r in records:
        lic=r.get('selectedLicense') or r.get('selected_license')
        if lic not in allowed:raise SystemExit(f'Unapproved conditional license: {lic}')
        if not r.get('authors'):raise SystemExit(f'Missing authors: {r.get("source")}')
        if not r.get('urls'):raise SystemExit(f'Missing source URL: {r.get("source")}')
        if r.get('shareAlikeRequired') is not True:raise SystemExit(f'Missing ShareAlike flag: {r.get("source")}')
    for rel in ['tools/automation/release/Build-UniversalLpcOpenAssetBundleV167W.py','content/schemas/universal_lpc_usage_manifest.schema.v0_1.json','content/assets/lpc/licenses/CC-BY-SA-3.0-NOTICE.txt']:
        if not (ROOT/rel).is_file():raise SystemExit(f'Missing compliance file: {rel}')
    print('Universal LPC ShareAlike intake validated: 2,038 selectable commercial records')
    return 0
if __name__=='__main__':raise SystemExit(main())
