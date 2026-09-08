#!/usr/bin/env python3
"""Build the Universal LPC character authority with explicit ShareAlike tracking."""
from __future__ import annotations
import csv, json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SOURCE=ROOT/'assets/source/licensed/universal_lpc_generator'
OUTPUT=ROOT/'WORKSPACE/generated/universal_lpc_character_authority_v167w.json'
PREFERRED=ROOT/'WORKSPACE/generated/universal_lpc_preferred_credits_v167w.csv'
SHAREALIKE=ROOT/'WORKSPACE/generated/universal_lpc_sharealike_credits_v167w.csv'

def choose_license(raw:str):
    licenses=[x.strip() for x in raw.split(',') if x.strip()]
    if 'CC0' in licenses:return 'CC0','preferred'
    for x in licenses:
        if x.startswith('OGA-BY') or x=='OGA-BY-3.0':return x,'preferred'
    for x in licenses:
        if (x.startswith('CC-BY ') or x.startswith('CC-BY-') or x=='CC-BY') and 'SA' not in x:return x,'preferred'
    for x in licenses:
        if x.startswith('CC-BY-SA'):return x,'conditional'
    return None,'rejected'

def tags_for(path:str):
    low=path.lower(); tags={path.split('/')[0]}
    for tag in ('male','female','teen','child','elderly','pregnant','muscular','zombie','skeleton','lizard','wings','tail','wheelchair','prosthesis','hair','beards','eyes','hat','torso','legs','feet','weapon','shield','tools'):
        if tag in low: tags.add(tag)
    return sorted(tags)

def write_csv(path, rows):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',encoding='utf-8',newline='') as s:
        w=csv.DictWriter(s,fieldnames=['filename','authors','selected_license','urls','share_alike_required'])
        w.writeheader();w.writerows(rows)

def main():
    if not SOURCE.is_dir():raise SystemExit('Universal LPC source is not mounted; run tools/automation/characters/Ensure-UniversalLpcGenerator.py')
    with (SOURCE/'CREDITS.csv').open(encoding='utf-8',newline='') as s: rows=list(csv.DictReader(s))
    records=[]; tier=Counter();cats=Counter(); preferred=[]; conditional=[]
    for row in rows:
        selected,t=choose_license(row['licenses']); category=row['filename'].split('/')[0];tier[t]+=1;cats[category]+=1
        rec={'source':row['filename'],'category':category,'tags':tags_for(row['filename']),'authors':[x.strip() for x in row['authors'].split(',') if x.strip()],'licenses':[x.strip() for x in row['licenses'].split(',') if x.strip()],'selected_license':selected,'license_tier':t,'share_alike_required':t=='conditional','urls':[x.strip() for x in row['urls'].split(',') if x.strip()],'notes':row.get('notes','').strip()}
        records.append(rec)
        if selected:
            target=conditional if t=='conditional' else preferred
            target.append({'filename':row['filename'],'authors':row['authors'],'selected_license':selected,'urls':row['urls'],'share_alike_required':str(t=='conditional').lower()})
    animation=defaultdict(int)
    for p in (SOURCE/'spritesheets').rglob('*.png'):animation[p.stem]+=1
    authority={'schema':'havenwild.universal_lpc_character_authority.v167w','source_commit':'0f898bb675a1abe16ce430e82e3bf9daed278690','sex_values':['Male','Female'],'age_groups':['Child','Teen','Adult','Elder'],'credit_record_count':len(records),'license_tier_counts':dict(tier),'category_counts':dict(cats),'animation_filename_counts':dict(sorted(animation.items())),'release_policy':{'conditional_share_alike_selectable':True,'exact_dependency_tracking_required':True,'open_asset_bundle_required_for_release':True},'records':records}
    OUTPUT.parent.mkdir(parents=True,exist_ok=True);OUTPUT.write_text(json.dumps(authority,indent=2)+'\n',encoding='utf-8')
    write_csv(PREFERRED,preferred);write_csv(SHAREALIKE,conditional)
    print(f'Wrote {OUTPUT} with {len(records):,} records')
    print(f'Preferred: {len(preferred):,}; ShareAlike: {len(conditional):,}')
    return 0
if __name__=='__main__':raise SystemExit(main())
