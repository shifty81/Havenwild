#!/usr/bin/env python3
"""Static/source and review-data gate for B48R13. NOT a Rust compile or runtime gate."""
import argparse
import json
import pathlib
import sys


def check(root: pathlib.Path):
    mapper = root / 'apps/haven_atlas_mapper_lite'
    main = (mapper / 'src/main.rs').read_text(encoding='utf-8')
    review = (mapper / 'src/review.rs').read_text(encoding='utf-8')
    cli = (mapper / 'tools/verify_review.py').read_text(encoding='utf-8')
    assert 'havenwild.atlas_mapper_project.v0_6' in main
    assert 'source_stack: Vec<LoadedAtlas>' in main
    assert 'source_asset_id: String' in main
    assert 'self.texture_for_piece(piece)' in main
    assert 'fn export_review_dialog(' in main and 'review::write_review(' in main
    assert 'fn edit_selected_height(' in main and '.clamp(0, 30)' in main
    assert 'fn toggle_selected_water(' in main
    assert 'candidate_export_not_validated' in main
    assert 'Project load blocked; current scene preserved.' in main
    assert 'if self.dirty {' in main
    assert 'if sources.is_empty() || pieces.is_empty()' in review
    assert 'heightmap.iter().any(' in review and 'water > 30' in review
    assert 'unreviewed_source_assembly_not_for_runtime' in review
    assert 'all_source_hashes_pinned' in cli
    assert 'alpha_composite' in cli
    height = json.loads((root / 'content/worldgen/elizawy_heightmap_target_v0_1.json').read_text())
    assert (height['oceanElevation'], height['testMaxElevation']) == (0,30)
    assert height['everyIntegerLevelIsReal'] and height['levelOneValidCoastalCliff']
    assert height['runtimeCertified'] is False
    assert set(height['mountainTraversal']) == {'source_climbable_vines','source_cliff_indentations',
        'source_ladders','topologically_walkable_cliff_terminations'}
    contact = json.loads((root / 'content/assets/lpc/elizawy_cliff_water_contact_evidence_b48r12_v0_1.json').read_text())
    assert contact['structuralPolicy']['baselinePolicyStatus'] == 'retired_by_elizawy_first_heightmap_reset'
    assert contact['structuralPolicy']['maxTargetTestElevation'] == 30
    assert contact['structuralPolicy']['currentEngineMigrationCompleted'] is False
    assert not (mapper / 'src/parallel_mapper.rs').exists()
    print('PASS B48R13 mapper static/source gate: in-place multi-sheet, source review, real +1..+30 candidate, safe load, deferred publication')
    print('NOT TESTED native Rust compile/GUI, adjacency, visual certification, worldgen/editor/client parity')

if __name__ == '__main__':
    p=argparse.ArgumentParser();p.add_argument('--repo',type=pathlib.Path,default=pathlib.Path(__file__).resolve().parents[3]);a=p.parse_args()
    try:check(a.repo)
    except (AssertionError,ValueError,KeyError,OSError) as exc:
        print('FAIL B48R13 convergence:',repr(exc),file=sys.stderr);sys.exit(1)
