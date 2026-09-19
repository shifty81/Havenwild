#!/usr/bin/env python3
"""Independent source-mapping regression checks; run directly for B48R8 certification."""
import importlib.util
import json
import shutil
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('b48r8_validator',HERE/'Validate-ElizaWyWaterfallTransitionB48R8.py')
checker=importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)
REPO=HERE.parents[4]
FILES=[checker.MAP_PATH,checker.EXPECTED_SHEET,'assets/source/licensed/lpc_revised/Terrain/REFERENCE_PACK_TERRAIN_CREDITS.txt','content/assets/lpc/source_blobs/elizawy_mountain_waterfall_transitions_summer.png.source','content/assets/lpc/credits/elizawy_reference_terrain_credits_b48r8.txt']
with tempfile.TemporaryDirectory(prefix='b48r8-validation-') as directory:
    root=Path(directory)
    for name in FILES:
        target=root/name
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(REPO/name,target)
    checker.validate(root)
    raw=(root/checker.EXPECTED_SHEET).read_bytes()
    width,height,pixels=checker.decode_rgba_png(raw)
    assert (width,height)==(192,224)
    try:
        from PIL import Image
        image=Image.open(root/checker.EXPECTED_SHEET).convert('RGBA')
        assert image.tobytes()==pixels,'stdlib PNG decode diverges from Pillow'
        print('PASS decode cross-check against Pillow')
    except ImportError:
        print('SKIP optional Pillow decoder cross-check; stdlib pixel digest still verified')
    checks=0
    # Bytes fail closed even if PNG still begins with PNG magic.
    (root/checker.EXPECTED_SHEET).write_bytes(raw[:-1]+bytes([raw[-1]^1]))
    try:checker.validate(root)
    except ValueError:checks+=1
    else:raise AssertionError('tampered source was accepted')
    (root/checker.EXPECTED_SHEET).write_bytes(raw)
    mp=root/checker.MAP_PATH
    good=json.loads(mp.read_text())
    damaged=json.loads(mp.read_text());damaged['cells'][0]['pixelSha256']='0'*64
    mp.write_text(json.dumps(damaged))
    try:checker.validate(root)
    except ValueError:checks+=1
    else:raise AssertionError('tampered cell hash was accepted')
    damaged=json.loads(json.dumps(good));damaged['cells'][0]['grid']=[1,0]
    mp.write_text(json.dumps(damaged))
    try:checker.validate(root)
    except ValueError:checks+=1
    else:raise AssertionError('duplicate cell was accepted')
    damaged=json.loads(json.dumps(good));damaged['productionEnabled']=True
    mp.write_text(json.dumps(damaged))
    try:checker.validate(root)
    except ValueError:checks+=1
    else:raise AssertionError('runtime promotion was accepted')
    mp.write_text(json.dumps(good))
    checker.validate(root)
    # Simulate a clean Git clone: ignored /assets/ source not present, tracked blob remains.
    spec_h=importlib.util.spec_from_file_location('b48r8_hydrate',HERE/'Hydrate-ElizaWyWaterfallTransitionB48R8.py')
    hydrator=importlib.util.module_from_spec(spec_h)
    spec_h.loader.exec_module(hydrator)
    (root/checker.EXPECTED_SHEET).unlink()
    hydrator.hydrate(root)
    checker.validate(root)
    assert (root/checker.EXPECTED_SHEET).read_bytes()==(root/'content/assets/lpc/source_blobs/elizawy_mountain_waterfall_transitions_summer.png.source').read_bytes()
    print('PASS negative tests: %d tampered source, cell, inventory, production-gate failures rejected; clean-clone hydration restored exact bytes'%checks)
