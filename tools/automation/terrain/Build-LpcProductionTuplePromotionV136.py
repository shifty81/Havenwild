#!/usr/bin/env python3
"""Build Pass 136 exact production shore/depth tuple promotion outputs."""
from __future__ import annotations
import json, subprocess, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[3]
MANIFEST = ROOT / 'assets/generated/worldgen_v0_1/terrain/lpc_mapped_terrain_v7_32.json'
ATLAS = ROOT / 'assets/generated/worldgen_v0_1/terrain/lpc_mapped_terrain_v7_32.png'
AUDIT = ROOT / 'content/assets/lpc/lpc_tuple_coverage_audit_v0_1.json'
REPORT = ROOT / 'docs/assets/LPC_PRODUCTION_TUPLE_PROMOTION_PASS136.md'
PREVIEW = ROOT / 'docs/assets/previews/havenwild_lpc_production_tuple_promotion_pass136.png'
PAIRS = [
 ('Sand','Water_Deep'), ('Grass','Water_Deep'),
 ('Water_Deep','Water_Shallows_Sand'), ('Water','Mudstone_Brown'),
 ('Water_Deep','Water_Shallows_Dirt'),
 ('Water_Shallows_Sand','Water_Shallows_Dirt'),
]
KEYS=('topLeft','topRight','bottomLeft','bottomRight')

def run(name: str) -> None:
 subprocess.run([sys.executable, str(ROOT/'tools/automation'/name)], cwd=ROOT, check=True)

def main() -> int:
 run('Build-LpcMappedTerrainV7.py')
 run('Build-LpcTupleCoverageAuditV133.py')
 run('Build-LpcTuplePromotionPlanV134.py')
 manifest=json.loads(MANIFEST.read_text(encoding="utf-8"))
 entries=manifest['entries']
 generated=[e for e in entries if e.get('sourceSheet')=='generated_pass136_tuple_promotion']
 by_pair={tuple(sorted(pair)):[] for pair in PAIRS}
 for e in generated:
  names=tuple(e['corners'][k] for k in KEYS)
  pair=tuple(sorted(set(names)))
  if pair in by_pair: by_pair[pair].append(e)
 audit=json.loads(AUDIT.read_text(encoding="utf-8"))
 totals=audit['totals']
 lines=['# LPC Production Tuple Promotion - Pass 136','',
 'Pass 136 converts the six highest-frequency production shoreline and water-depth pairs from guarded pure-fill fallback ownership into explicit deterministic terrain-v7 tuple entries.','',
 f"- Exact tuples after promotion: **{totals['exact']}**",
 f"- Remaining fallback tuples: **{totals['fallback']}**",
 f"- Missing tuples: **{totals.get('missing',0)}**",
 f"- New generated exact entries: **{len(generated)}**",'',
 '| Pair | Exact promoted shapes |','|---|---:|']
 for pair in PAIRS: lines.append(f"| `{pair[0]} ↔ {pair[1]}` | {len(by_pair[tuple(sorted(pair))])} |")
 lines += ['', 'The generated tiles use seam-safe deterministic corner masks. Water/land pairs use the appropriate shallow-water intermediary band where available, while mixed tiles remain stable across water animation frames.','',f'- Preview: `{PREVIEW.relative_to(ROOT)}`']
 REPORT.write_text('\n'.join(lines)+'\n', encoding='utf-8')

 image=Image.open(ATLAS).convert('RGBA')
 cell=54; label=34; margin=12
 canvas=Image.new('RGB',(14*cell+margin*2,len(PAIRS)*(cell+label)+margin),(24,28,31))
 draw=ImageDraw.Draw(canvas)
 try: font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',11)
 except OSError: font=None
 for row,pair in enumerate(PAIRS):
  y=margin+row*(cell+label)
  draw.text((margin,y),f'{pair[0]} ↔ {pair[1]}',fill=(230,211,132),font=font)
  items=sorted(by_pair[tuple(sorted(pair))],key=lambda e:e['tileId'])
  for i,e in enumerate(items):
   x=margin+i*cell; rx,ry,rw,rh=e['rect']
   tile=image.crop((rx,ry,rx+rw,ry+rh)).resize((48,48),Image.Resampling.NEAREST)
   canvas.paste(tile,(x,y+18),tile); draw.rectangle((x,y+18,x+47,y+65),outline=(78,88,91))
 PREVIEW.parent.mkdir(parents=True,exist_ok=True); canvas.save(PREVIEW)
 print(f'Pass 136 built {len(generated)} exact production tuples; totals {totals}')
 return 0
if __name__=='__main__': raise SystemExit(main())
