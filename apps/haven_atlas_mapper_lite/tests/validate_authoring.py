#!/usr/bin/env python3
from pathlib import Path
import argparse, sys

p=argparse.ArgumentParser()
p.add_argument('--repo', default='.')
a=p.parse_args()
root=Path(a.repo).resolve()
main=(root/'apps/haven_atlas_mapper_lite/src/main.rs').read_text(encoding='utf-8')
review=(root/'apps/haven_atlas_mapper_lite/src/review.rs').read_text(encoding='utf-8')
checks={
 'multi-source scene': 'source_stack: Vec<LoadedAtlas>' in main and 'source_asset_id: String' in main,
 'height tool': 'AuthorTool::Elevation' in main and 'set_height_cell' in main and 'paint_elevation' in main,
 'water tool': 'AuthorTool::Water' in main and 'toggle_water_cell' in main,
 '0..30 contract': '.min(30)' in main and 'elevation > 30' in review,
 'genuine +1 permitted': 'including +1' in review,
 'source review export': 'write_review' in main and 'unreviewed_source_assembly_not_for_runtime' in review,
 'cliff connectors': all(x in main for x in ['climbable_vine_candidate','cliff_handhold_candidate','ladder_candidate','walkable_termination_candidate']),
 'non-destructive source switching': 'Selecting an existing source card switches the source picker only' in main,
 'candidate-only handoff': 'candidate_export_not_validated' in main,
}
failed=[k for k,v in checks.items() if not v]
for k,v in checks.items(): print(('PASS' if v else 'FAIL'),k)
if failed:
    print('FAILED:',', '.join(failed)); sys.exit(1)
print('PASS B48R14 authoring static gate; native Rust build/GUI still required on Windows')
