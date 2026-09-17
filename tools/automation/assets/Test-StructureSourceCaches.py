#!/usr/bin/env python3
"""Fixture-based source-cache contract tests. Does not access or alter original artwork."""
from __future__ import annotations
import importlib.util
import json
import tempfile
from pathlib import Path
from PIL import Image

SCRIPT = Path(__file__).with_name('Ensure-StructureSourceCaches.py')
spec = importlib.util.spec_from_file_location('havenwild_source_cache_gate', SCRIPT)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

with tempfile.TemporaryDirectory() as work:
    root = Path(work)
    first = module.SPECS[0]
    label, source_id, png_rel, metadata_rel, builder, dimensions = first
    valid, message = module.inspect_cache(root, png_rel, metadata_rel, dimensions)
    assert not valid and 'missing:' in message
    source = root / 'licensed/original.png'
    source.parent.mkdir(parents=True)
    source.write_bytes(b'unmodified source bytes')
    image_path = root / png_rel
    image_path.parent.mkdir(parents=True)
    Image.new('RGBA', dimensions).save(image_path)
    metadata_path = root / metadata_rel
    metadata_path.write_text(json.dumps({'atlas': png_rel, 'atlasSize': list(dimensions),
                                         'sourceHashes': {'licensed/original.png': module.sha256(source)}}))
    valid, message = module.inspect_cache(root, png_rel, metadata_rel, dimensions)
    assert valid and 'cache/source verified' in message
    source.write_bytes(b'source drift')
    valid, message = module.inspect_cache(root, png_rel, metadata_rel, dimensions)
    assert not valid and 'hash mismatch' in message
    source.unlink()
    valid, message = module.inspect_cache(root, png_rel, metadata_rel, dimensions)
    assert not valid and 'pinned original source missing' in message
    image_path.unlink()
    valid, message = module.inspect_cache(root, png_rel, metadata_rel, dimensions)
    assert not valid and 'missing:' in message
print('PASS: missing cache, valid original, drifted original, absent original, and missing PNG fixture checks')

# Exercise the orchestration independently of any private/licensed source files.
with tempfile.TemporaryDirectory() as work:
    root = Path(work)
    source = root / 'licensed/original.png'
    source.parent.mkdir(parents=True)
    source.write_bytes(b'fixture: original is never changed by the cache builder')
    first = module.SPECS[0]
    label, source_id, png_rel, metadata_rel, _, dimensions = first
    (root / 'content/asset_packs/havenwild_objects').mkdir(parents=True)
    (root / 'content/asset_packs/havenwild_objects/pack.json').write_text(
        json.dumps({'sources': [{'id': source_id, 'path': png_rel}]}))
    builder_rel = 'tools/automation/assets/fixture_builder.py'
    builder = root / builder_rel
    builder.parent.mkdir(parents=True)
    builder.write_text('''from pathlib import Path
import argparse, hashlib, json
from PIL import Image
ap=argparse.ArgumentParser(); ap.add_argument('--root',type=Path); ap.add_argument('--require-source',action='store_true'); args=ap.parse_args()
r=args.root; source=r/'licensed/original.png'; assert source.is_file()
png=r/'assets/generated/havenwild_structure_components_w45b.png'; png.parent.mkdir(parents=True,exist_ok=True)
Image.new('RGBA',(256,256)).save(png)
meta=r/'assets/generated/havenwild_structure_components_w45b.json'
meta.write_text(json.dumps({'atlas':'assets/generated/havenwild_structure_components_w45b.png','atlasSize':[256,256], 'sourceHashes':{'licensed/original.png':hashlib.sha256(source.read_bytes()).hexdigest()}}))
''')
    module.SPECS = ((label, source_id, png_rel, metadata_rel, builder_rel, dimensions),)
    before = source.read_bytes()
    assert module.run(root, audit_only=True) == 1  # missing: do not mutate
    assert module.run(root, audit_only=False) == 0  # source-only rebuild
    assert source.read_bytes() == before
    assert module.run(root, audit_only=True) == 0  # no-op valid cache
    (root / png_rel).unlink()
    source.unlink()
    assert module.run(root, audit_only=False) == 1  # no fabricated source
print('PASS: source-only repair, audit-only, verified original preservation and blocked source fixture checks')
