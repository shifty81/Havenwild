import json
from pathlib import Path
root = Path(__file__).resolve().parents[3]
p=root/'content/editor/world_asset_edit_bindings_v0_1.json'
data=json.loads(p.read_text(encoding='utf-8'))
assert data['schema']=='havenwild.world_asset_edit_bindings.v0_1'
seen=set()
for item in data['bindings']:
    assert item['semantic_id'] not in seen
    seen.add(item['semantic_id'])
    src=root/item['source_path']
    assert src.is_file(), src
    x,y,w,h=item['source_rect']
    assert w>0 and h>0 and x>=0 and y>=0
print(f'World asset edit bindings passed: {len(seen)} bindings')
