#!/usr/bin/env python3
"""Report actual source authority and production/runtime availability; never generate pixels.

This audit intentionally distinguishes an optional quarantined authoring sheet
from the mandatory production cliff texture. It records the exact OGA source
hash without silently downloading or renaming a building stair sprite.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

GRASS = 'content/assets/oga_lpc/source/terrain/cliffs_grass_top/LPC_cliffs_grass.png'
RAMP_CONTRACT = 'content/worldgen/lpc_directional_cliff_ramp_authority_v0_1.json'
PACK = 'content/asset_packs/oga_lpc_cliffs/pack.json'
STAIRS = 'assets/source/licensed/lpc_revised/Structure/Stairs/Short Steps A.png'
W3 = 'assets/generated/worldgen_v0_1/terrain/elizawy_cliff_runtime_overlay_summer.png'


def inspect(root: Path) -> dict:
    contract = json.loads((root / RAMP_CONTRACT).read_text(encoding='utf-8-sig'))
    pack = json.loads((root / PACK).read_text(encoding='utf-8-sig'))
    grass = contract['sourceFamily']['grass']
    assert grass['path'] == GRASS
    rows = []
    for role, path, expected, required in (
        ('primary_w3_cliff_cache', W3, None, True),
        ('optional_quarantined_cliff_ramp_source', GRASS, grass['sha256'], False),
        ('distinct_building_stair_source', STAIRS, None, False),
    ):
        source = root / path
        observed = hashlib.sha256(source.read_bytes()).hexdigest() if source.is_file() else None
        status = ('missing_required' if required else 'not_mounted_optional') if observed is None else (
            'hash_mismatch' if expected and expected != observed else 'available')
        rows.append({'role': role, 'path': path, 'required': required,
                     'status': status, 'actual_sha256': observed, 'expected_sha256': expected})
    return {'schema': 'havenwild.source_first_visual_binding_audit.b07.v1',
            'source_pack_production_enabled': pack['production_enabled'],
            'source_page': pack['license']['source_url'],
            'original_licensed_art_mutated': False,
            'bindings': rows}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    report = inspect(args.root)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    for item in report['bindings']:
        print(f"{item['role']}: {item['status']} — {item['path']}")
    # Informational diagnostic: optional quarantined art must not fail the gate.
    # Mandatory W3 is guarded by B05C's separate exact-hash recovery.

if __name__ == '__main__':
    main()
