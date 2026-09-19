#!/usr/bin/env python3
"""Restore exact original ElizaWy PNG from the repo-retained raw-byte source. Fail closed on conflict."""
import argparse, hashlib, json, os
from pathlib import Path

def digest(data):return hashlib.sha256(data).hexdigest()

def hydrate(repo):
    j=json.loads((repo/'content/assets/lpc/elizawy_mountain_waterfall_transition_source_b48r8_v0_1.json').read_text(encoding='utf-8'))
    a=j['authority'];blob=repo/a['gitRetainedOriginalPngBlob'];dst=repo/a['installedSourcePath']
    content=blob.read_bytes()
    if digest(content)!=a['sourceSha256'] or not content.startswith(b'\x89PNG\r\n\x1a\n'):
        raise ValueError('repository-retained original source blob invalid')
    if dst.exists():
        if digest(dst.read_bytes())!=a['sourceSha256']:
            raise ValueError('existing external asset differs; refusing to overwrite')
        print('PASS existing ElizaWy waterfall transition source exact; no copy required')
        return
    dst.parent.mkdir(parents=True,exist_ok=True)
    temp=dst.with_name(dst.name+'.b48r8-staging')
    try:
        temp.write_bytes(content)
        if digest(temp.read_bytes())!=a['sourceSha256']:
            raise ValueError('staged source asset did not verify')
        os.replace(temp,dst)
    finally:
        if temp.exists():temp.unlink()
    print('PASS restored exact ElizaWy source PNG to ignored local asset mount from tracked raw-byte blob')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--repo',type=Path,default=Path(__file__).resolve().parents[5]);args=p.parse_args()
    try:hydrate(args.repo)
    except (ValueError,KeyError,FileNotFoundError) as exc:raise SystemExit('FAIL hydration: '+str(exc))
