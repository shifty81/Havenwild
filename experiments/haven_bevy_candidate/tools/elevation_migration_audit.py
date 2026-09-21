#!/usr/bin/env python3
"""Read-only scope audit: legacy +1 cliff restrictions to migrate before Bevy game parity.

This is an evidence inventory, NEVER an automatic world or validator rewrite.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

PATTERNS = {
    'crates/haven_world/src/geographic_surface.rs': (
        'Level 1 is reserved for a certified authored ramp transition.',
        'geographic_authority_never_emits_standalone_level_one_cliffs',
    ),
    'crates/haven_world/src/structural_elevation_normalization.rs': (
        'BROAD_LEVEL_ONE_MIN_CELLS',
        'Ordinary editor/worldgen structural authoring uses 0,2,3,4.',
        'thin_one_high_shelf_collapses_to_relief',
        'broad_legacy_one_high_region_promotes_to_true_plateau',
        'ordinary_authoring_skips_reserved_level_one',
    ),
    'crates/haven_world/src/generated_surface_chunks.rs': (
        'generated_surface_has_no_standalone_level_one_cliff_cells',
        'Level 1 is reserved for certified ramp paths',
    ),
}

def inspect(root: Path) -> dict:
    findings=[]
    for rel, patterns in PATTERNS.items():
        path=root/rel
        if not path.is_file() or path.is_symlink():
            findings.append({'path':rel,'status':'SOURCE_ABSENT_NOT_A_NEGATIVE_FINDING','hits':[]})
            continue
        lines=path.read_text(encoding='utf-8').splitlines()
        hits=[{'line':i,'marker':pattern} for pattern in patterns
              for i,line in enumerate(lines,1) if pattern in line]
        findings.append({'path':rel,'status':'LEGACY_CONSTRAINT_FOUND' if hits else 'NO_KNOWN_MARKER_FOUND_REVIEW_REQUIRED', 'hits':hits})
    return {'schema':'havenwild.experimental.elevation_migration_audit.v1',
            'status':'LEGACY_ELEVATION_MIGRATION_UNCERTIFIED',
            'targetContract':'Sea level 0; every integer +1..+30 is real geography; no implicit ramps',
            'findings':findings,'worldgenMigrated':False,'oldValidatorsRetired':False,
            'bevyWorldParityCertified':False,
            'rule':'Only source-supported connected traversal may cross a height discontinuity. No automatic tile coercion.',
            'scope':'Original files read-only; no canonical edits or regenerated world assets.'}

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,required=True)
    args=parser.parse_args(argv)
    if not args.root.is_dir():parser.error('Existing Havenwild root required')
    print(json.dumps(inspect(args.root.resolve()),indent=2))
    return 0
if __name__=='__main__':raise SystemExit(main())
