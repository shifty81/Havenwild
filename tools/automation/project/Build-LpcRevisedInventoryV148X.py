#!/usr/bin/env python3
"""Build a read-only-derived inventory of the complete mounted LPC Revised repository."""
from __future__ import annotations
import argparse, json, re, struct, time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_SOURCE = ROOT / 'assets/source/licensed/lpc_revised'
DEFAULT_OUTPUT = ROOT / 'WORKSPACE/generated/lpc_revised_inventory_v1.json'

EXT_KIND = {
    '.png':'image', '.gif':'image', '.jpg':'image', '.jpeg':'image', '.webp':'image',
    '.tsx':'tiled_tileset', '.tmx':'tiled_map', '.json':'sidecar', '.xml':'sidecar', '.ron':'sidecar',
    '.ogg':'audio', '.wav':'audio', '.mp3':'audio', '.txt':'documentation', '.md':'documentation',
    '.license':'license'
}
LICENSE_TOKENS = ('license','licence','copying','authors','credits','attribution','readme')
RULES = [
 ('character', ('character','body','base sprites','spritesheet')),
 ('clothing', ('hair','clothes','clothing','dress','shirt','pants','boots','hat')),
 ('armor', ('armor','armour','helmet','shield')),
 ('weapon', ('weapon','sword','axe','bow','spear','staff')),
 ('tool', ('tool','hoe','pickaxe','watering','fishing')),
 ('animal', ('animal','creature','monster','beast','horse')),
 ('npc', ('npc','portrait','faces','face')),
 ('animation', ('animation','walkcycle','slash','spellcast','thrust','shoot')),
 ('terrain', ('terrain','ground','grass','dirt','sand','water','mountain','cliff')),
 ('building', ('building','house','castle','tower','roof')),
 ('wall', ('wall','fence')),
 ('floor', ('floor','carpet','rug')),
 ('door', ('door','gate','window')),
 ('furniture', ('furniture','chair','table','bed','shelf','cabinet')),
 ('crop', ('crop','farm','plant','seed')),
 ('tree', ('tree','wood','stump')),
 ('foliage', ('foliage','flower','bush','shrub','weed')),
 ('interior', ('interior','indoor')),
 ('cave', ('cave','mine')),
 ('dungeon', ('dungeon','crypt','ruin')),
 ('effect', ('effect','particle','magic','spell','projectile')),
 ('ui', ('ui','interface','icon','cursor','button')),
 ('item', ('item','inventory','food','potion')),
 ('tile_object', ('tile','object','decor','prop')),
]

def classify(path: str) -> str:
    v = path.replace("\\", "/").lower()
    if v.startswith("terrain/"):
        name = Path(v).name
        if "mushroom" in name:
            return "forage"
        if "wildflower" in name or "flower" in name or "plants_" in name:
            return "foliage"
        if "trees_" in name:
            return "tree"
        if "rocks," in name:
            return "rock_object"
        if "cliff_" in name or "rocks, cliffs" in name:
            return "elevation"
        if "waterfall" in name or "ice-shallows" in name:
            return "water_feature"
        if "tilled_soil" in name:
            return "farm_ground"
        if "terrain_" in name:
            return "terrain"
    if any(x in v for x in ("animal", "creature", "monster")):
        for category, terms in RULES[5:]:
            if any(term in v for term in terms):
                return category
    for category, terms in RULES:
        if any(term in v for term in terms):
            return category
    return "other"

def slug(value: str) -> str:
    value = re.sub(r'[^a-z0-9]+', '.', value.lower()).strip('.')
    return value or 'unnamed'

def png_dimensions(path: Path):
    try:
        with path.open('rb') as f:
            if f.read(8) != b'\x89PNG\r\n\x1a\n': return None
            length = struct.unpack('>I', f.read(4))[0]
            if f.read(4) != b'IHDR' or length < 8: return None
            return list(struct.unpack('>II', f.read(8)))
    except OSError:
        return None

def nearby_licenses(path: Path, source: Path):
    found=[]
    for parent in [path.parent, *path.parents]:
        if source not in [parent, *parent.parents] and parent != source: break
        try:
            for p in parent.iterdir():
                if p.is_file() and any(t in p.name.lower() for t in LICENSE_TOKENS):
                    rel=p.relative_to(source).as_posix()
                    if rel not in found: found.append(rel)
        except OSError: pass
        if parent == source or len(found) >= 8: break
    return found[:8]

def frame_hint(path: str, dims):
    v=path.lower()
    if not dims: return None
    if any(t in v for t in ('character','body','hair','clothing','armor','weapon','walkcycle','spellcast')):
        if dims[0] % 64 == 0 and dims[1] % 96 == 0: return [64,96]
        if dims[0] % 64 == 0 and dims[1] % 64 == 0: return [64,64]
    if dims[0] % 32 == 0 and dims[1] % 32 == 0: return [32,32]
    return None

def animation_hint(path: str):
    v=path.lower()
    for token in ('walkcycle','idle','slash','thrust','spellcast','shoot','hurt','death'):
        if token in v: return token
    return None

def build(source: Path):
    files=[]; counts=Counter(); diagnostics=[]
    if not source.is_dir():
        diagnostics.append(f'external dependency missing: {source}')
    else:
        for path in sorted(p for p in source.rglob('*') if p.is_file()):
            ext=path.suffix.lower()
            if ext not in EXT_KIND: continue
            rel=path.relative_to(source).as_posix()
            category=classify(rel)
            dims=png_dimensions(path) if ext=='.png' else None
            licenses=nearby_licenses(path,source)
            stem=slug(rel.rsplit('.',1)[0])
            tags={category, *[slug(part) for part in Path(rel).parts[:-1]]}
            readiness='license_review_required'
            if EXT_KIND[ext] in ('documentation','license'): readiness='indexed'
            elif ext in ('.tsx','.tmx','.json','.xml','.ron'): readiness='metadata_candidate'
            elif EXT_KIND[ext] not in ('image','audio'): readiness='unsupported_source'
            elif licenses: readiness='manual_mapping_required'
            entry={
              'relative_path':rel, 'source_kind':EXT_KIND[ext], 'category':category,
              'proposed_asset_id':stem, 'proposed_semantic_id':f'lpc.{category}.{stem}',
              'tags':sorted(tags), 'dimensions':dims, 'frame_cell':frame_hint(rel,dims),
              'animation_family':animation_hint(rel), 'nearby_license_files':licenses,
              'readiness':readiness
            }
            files.append(entry); counts[category]+=1
    return {
      'schema':'havenwild.lpc_revised_repository_inventory.v1',
      'source_root':source.as_posix(), 'generated_at_unix_seconds':int(time.time()),
      'files':files, 'category_counts':dict(sorted(counts.items())), 'diagnostics':diagnostics
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--source',type=Path,default=DEFAULT_SOURCE)
    ap.add_argument('--output',type=Path,default=DEFAULT_OUTPUT)
    ap.add_argument('--strict-source',action='store_true')
    args=ap.parse_args()
    source=args.source if args.source.is_absolute() else ROOT/args.source
    output=args.output if args.output.is_absolute() else ROOT/args.output
    data=build(source)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
    print(f"LPC Revised inventory: {len(data['files'])} files across {len(data['category_counts'])} categories -> {output}")
    if args.strict_source and not source.is_dir(): raise SystemExit(2)
if __name__=='__main__': main()
