#!/usr/bin/env python3
"""Convert the complete LPC Revised repository inventory into actionable mapping queues."""
from __future__ import annotations
import argparse, json, time
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_INPUT=ROOT/'WORKSPACE/generated/lpc_revised_inventory_v1.json'
DEFAULT_OUTPUT=ROOT/'WORKSPACE/generated/lpc_revised_mapping_queues_v1.json'
QUEUE_BY_CATEGORY={
 'character':'characters','clothing':'characters','armor':'characters','weapon':'characters','tool':'characters','npc':'characters',
 'terrain':'terrain','floor':'terrain','wall':'terrain','tile_object':'terrain','crop':'terrain','tree':'terrain','foliage':'terrain',
 'building':'structures','door':'structures','furniture':'placeables','interior':'structures','cave':'structures','dungeon':'structures',
 'animal':'animals','animation':'animations','effect':'animations','ui':'ui','item':'items','audio':'audio','music':'audio',
 'editor_template':'editor_templates','other':'review'
}
QUEUE_ORDER=['license_review','characters','terrain','structures','placeables','animals','animations','ui','items','audio','editor_templates','review']

def queue_for(entry):
    if entry.get('readiness')=='license_review_required' or not entry.get('nearby_license_files'):
        return 'license_review'
    return QUEUE_BY_CATEGORY.get(entry.get('category','other'),'review')

def priority(entry, queue):
    score=0
    if queue=='license_review': score+=100
    if entry.get('source_kind') in ('tiled_tileset','tiled_map','sidecar'): score+=35
    if entry.get('frame_cell'): score+=25
    if entry.get('animation_family'): score+=20
    if entry.get('nearby_license_files'): score+=10
    return score

def build(inventory):
    queues=defaultdict(list); counts=Counter()
    for source in inventory.get('files',[]):
        queue=queue_for(source)
        record={
          'queue':queue,
          'relative_path':source['relative_path'],
          'category':source.get('category','other'),
          'source_kind':source.get('source_kind','other'),
          'proposed_asset_id':source.get('proposed_asset_id',''),
          'proposed_semantic_id':source.get('proposed_semantic_id',''),
          'tags':source.get('tags',[]),
          'dimensions':source.get('dimensions'),
          'frame_cell':source.get('frame_cell'),
          'animation_family':source.get('animation_family'),
          'license_evidence':source.get('nearby_license_files',[]),
          'readiness':source.get('readiness','manual_mapping_required'),
          'priority':priority(source,queue),
          'promotion_state':'unreviewed',
          'recommended_action':'review_license' if queue=='license_review' else 'map_and_preview'
        }
        queues[queue].append(record); counts[queue]+=1
    for values in queues.values():
        values.sort(key=lambda v:(-v['priority'],v['category'],v['relative_path']))
    return {
      'schema':'havenwild.lpc_revised_mapping_queues.v1',
      'source_inventory_schema':inventory.get('schema'),
      'generated_at_unix_seconds':int(time.time()),
      'queue_order':QUEUE_ORDER,
      'queue_counts':{q:counts.get(q,0) for q in QUEUE_ORDER},
      'queues':{q:queues.get(q,[]) for q in QUEUE_ORDER},
      'promotion_states':['unreviewed','license_blocked','mapping','preview_ready','approved','rejected'],
      'diagnostics':list(inventory.get('diagnostics',[]))
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--inventory',type=Path,default=DEFAULT_INPUT)
    ap.add_argument('--output',type=Path,default=DEFAULT_OUTPUT)
    args=ap.parse_args()
    src=args.inventory if args.inventory.is_absolute() else ROOT/args.inventory
    out=args.output if args.output.is_absolute() else ROOT/args.output
    if not src.is_file():
        raise SystemExit(f'inventory missing: {src}; run Build-LpcRevisedInventoryV148X.py first')
    data=build(json.loads(src.read_text(encoding='utf-8')))
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
    print(f"LPC mapping queues: {sum(data['queue_counts'].values())} records across {len(data['queue_order'])} queues -> {out}")
if __name__=='__main__': main()
