#!/usr/bin/env python3
"""Static contract + real candidate ZIP tests; native Rust/PowerShell require Windows."""
from pathlib import Path
import hashlib
import importlib.util
import json
import sys
import tempfile
import zipfile
root = Path(__file__).resolve().parents[3]
source = (root/'apps/haven_atlas_mapper_lite/src/main.rs').read_text()
ledger = (root/'tools/control/PccPatchLedger.ps1').read_text(encoding='utf-8-sig')
assert 'fn reassemble_from_mapped_scene' in source
assert 'Save the corrected scene before Reassemble' in source
assert 'self.checkpoint_scene();' in source
assert 'MAX_REASSEMBLY_CELLS: usize = 24' in source
assert 'source_asset_id' in source and 'iteration_coverage: self.iteration_coverage()' in source
assert 'status == MAPPED_TILE_STATUS_APPROVED' in source
assert 'let complete = mapped_tile_count > 0 && coverage_percent >= 99.999 && all_approved' in source
assert 'let nonempty_cells = atlas.cell_profiles.iter().filter(|cell| cell.coverage > 0.0)' in source
assert 'unresolved.source_cell.needs_authoring' in source
assert 'if self.dirty || self.project_path.is_none()' in source
assert "Where-Object { $_.LastWriteTimeUtc -ge $SinceUtc.AddSeconds(-2) }" not in ledger
assert 'if(Test-Path -LiteralPath (Join-Path $Root $Transport) -PathType Leaf){ return $null }' in ledger
assert 'PATCH_MANIFEST.json' in ledger
helper=root/'apps/haven_atlas_mapper_lite/tools/package_iteration.py'
spec=importlib.util.spec_from_file_location('mapper_packet', helper)
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
with tempfile.TemporaryDirectory() as tmp:
    tmp=Path(tmp)
    piece={'id':1,'source_asset_id':'source:one','source_tile_x':0,'source_tile_y':0}
    sources=[{'id':'source:one','path':'source.png'}]
    height=[{'x':0,'y':0,'elevation':1}]
    project={'schema':'havenwild.atlas_mapper_project.v0_6','pieces':[piece],'heightmap':height}
    review={'approval':'unreviewed_source_assembly_not_for_runtime','placements':[piece],
            'heightmap':height,'source_assets':sources}
    handoff={'certification_stage':'candidate_export_not_validated','pieces':[piece],
             'heightmap':height,'source_assets':sources,'iteration_coverage':[{'source_asset_id':'source:one',
             'missing_cells':[[1,0]],'unresolved_scene_cells':1}], 'generation_passes':3}
    for path, obj in [(tmp/'scene.json', project),(tmp/'scene.review.json',review),(tmp/'scene_handoff.json',handoff)]:
        path.write_text(json.dumps(obj))
    (tmp/'scene.png').write_bytes(b'\x89PNG\r\n\x1a\n' + b'fixture only')
    summary=mod.package(tmp/'scene.json',tmp/'scene.png',tmp/'scene_handoff.json',tmp/'packet.zip')
    assert summary['missing_source_addresses']==1 and summary['unresolved_scene_cells']==1
    with zipfile.ZipFile(tmp/'packet.zip') as z:
        assert z.testzip() is None and 'ITERATION_MANIFEST.json' in z.namelist()
        for item in summary['files']:
            assert hashlib.sha256(z.read(item['file'])).hexdigest()==item['sha256']
    bad=handoff|{'pieces':[piece|{'id':2}]}
    (tmp/'scene_handoff.json').write_text(json.dumps(bad))
    try:
        mod.package(tmp/'scene.json',tmp/'scene.png',tmp/'scene_handoff.json',tmp/'bad.zip')
        raise AssertionError('Mismatched handoff should be rejected')
    except ValueError as e:
        assert 'different scene revisions' in str(e)
print('PASS mapping-cycle source contract; candidate ZIP CRC/SHA; mismatched handoff rejected. Rust/Windows UNTESTED')
