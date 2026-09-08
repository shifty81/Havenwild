#!/usr/bin/env python3
"""Export used Universal LPC CC-BY-SA assets as a redistributable open-assets bundle."""
from __future__ import annotations
import argparse,csv,gzip,json,shutil,subprocess,sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CATALOG=ROOT/'content/assets/lpc/universal_lpc_sharealike_catalog_v0_1.json.gz'
SOURCE=ROOT/'assets/source/licensed/universal_lpc_generator/spritesheets'
LICENSE=ROOT/'content/assets/lpc/licenses/CC-BY-SA-3.0-NOTICE.txt'
DEFAULT_USAGE=ROOT/'WORKSPACE/generated/universal_lpc_usage_manifest.json'
USAGE_BUILDER=ROOT/'tools/automation/characters/Build-UniversalLpcUsageManifestV167X.py'

def load_catalog():
    with gzip.open(CATALOG,'rt',encoding='utf-8') as f:return json.load(f)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--usage-manifest',type=Path);ap.add_argument('--output',type=Path,default=ROOT/'DIST/open-assets/cc-by-sa');ap.add_argument('--include-all-conditional',action='store_true');args=ap.parse_args()
    catalog=load_catalog(); by_source={r['source']:r for r in catalog['records']}
    generated=[]; usage={}
    if args.include_all_conditional: sources={s:{'source':s,'modified':False} for s in by_source}
    else:
        usage_path=args.usage_manifest
        if usage_path is None:
            if not USAGE_BUILDER.is_file():raise SystemExit(f'Missing usage-manifest builder: {USAGE_BUILDER}')
            subprocess.run([sys.executable,str(USAGE_BUILDER),'--output',str(DEFAULT_USAGE)],check=True)
            usage_path=DEFAULT_USAGE
        if not usage_path.is_file():raise SystemExit(f'Usage manifest does not exist: {usage_path}')
        usage=json.loads(usage_path.read_text(encoding='utf-8'))
        sources={x['source']:x for x in usage.get('sources',[])};generated=usage.get('generatedComposites',[])
    unknown=sorted(set(sources)-set(by_source))
    if unknown:raise SystemExit(f'Usage manifest references non-ShareAlike or unknown sources: {unknown[:10]}')
    if not SOURCE.is_dir():raise SystemExit('Universal LPC source mount is missing')
    out=args.output.resolve(); assets=out/'assets'; composites=out/'generated-composites';out.mkdir(parents=True,exist_ok=True)
    credit_rows=[];manifest=[]
    for source,usage_item in sorted(sources.items()):
        rec=by_source[source]; src=SOURCE/source
        if not src.is_file():raise SystemExit(f'Missing mounted source file: {src}')
        override=usage_item.get('overridePath')
        copy_src=(ROOT/override) if override else src
        if not copy_src.is_file():raise SystemExit(f'Missing override: {copy_src}')
        dst=assets/source;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(copy_src,dst)
        entry={'source':source,'bundlePath':dst.relative_to(out).as_posix(),'authors':rec['authors'],'selectedLicense':rec.get('selectedLicense') or rec.get('selected_license'),'urls':rec['urls'],'modified':bool(usage_item.get('modified',False) or override),'modificationNote':usage_item.get('modificationNote','')}
        manifest.append(entry);credit_rows.append({'source':source,'authors':'; '.join(rec['authors']),'license':entry['selectedLicense'],'urls':'; '.join(rec['urls']),'modified':entry['modified'],'modification_note':entry['modificationNote']})
    for item in generated:
        src=ROOT/item['path']
        deps=item.get('sourceDependencies',[])
        if not src.is_file():raise SystemExit(f'Missing generated composite: {src}')
        if not any(dep in by_source for dep in deps):continue
        dst=composites/src.name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
    if LICENSE.is_file():shutil.copy2(LICENSE,out/LICENSE.name)

    broad_files = [
        ROOT / 'content/legal/HAVENWILD_OPEN_ASSET_ACKNOWLEDGEMENT.txt',
        ROOT / 'content/legal/open_assets/UNIVERSAL_LPC_MASTER_CONTRIBUTORS.txt',
        ROOT / 'content/legal/open_assets/UNIVERSAL_LPC_MASTER_CONTRIBUTORS.csv',
        ROOT / 'content/legal/open_assets/UNIVERSAL_LPC_MASTER_CATALOG_SUMMARY.json',
    ]
    for broad_file in broad_files:
        if broad_file.is_file():
            shutil.copy2(broad_file, out / broad_file.name)
    (out/'MANIFEST.json').write_text(json.dumps({'schema':'havenwild.universal_lpc_open_asset_bundle.v0_1','recordCount':len(manifest),'records':manifest},indent=2)+'\n',encoding='utf-8')
    with (out/'CREDITS.csv').open('w',encoding='utf-8',newline='') as s:
        w=csv.DictWriter(s,fieldnames=['source','authors','license','urls','modified','modification_note']);w.writeheader();w.writerows(credit_rows)
    with (out/'CREDITS.txt').open('w',encoding='utf-8') as s:
        s.write('Havenwild Universal LPC CC-BY-SA Asset Credits\n\n')
        for r in credit_rows:s.write(f"{r['source']}\n  Authors: {r['authors']}\n  License: {r['license']}\n  Source: {r['urls']}\n  Modified: {r['modified']} {r['modification_note']}\n\n")
    print(f'Exported {len(manifest):,} ShareAlike sources to {out}')
    return 0
if __name__=='__main__':raise SystemExit(main())
