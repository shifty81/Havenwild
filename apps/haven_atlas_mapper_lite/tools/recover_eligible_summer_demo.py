#!/usr/bin/env python3
"""Recover only unique, complete 32x32 source-pixel matches from an artist demo.

This is a *partial candidate* mapper project, never an approved recipe or a scene
rebuilder. Its source directory must contain original pack paths (Terrain/..., etc.).
Every source PNG must match the supplied source ZIP byte-for-byte before use.
"""
import argparse
import collections
import hashlib
import io
import json
from pathlib import Path
import zipfile

from PIL import Image, ImageDraw

TILE = 32
EXCLUDED = ('(autumn)', '(spring)', '(winter)', 'winter plants', 'ice-water', 'waterfall, frozen')
LAYERS = ['Ground', 'Transitions', 'Cliff / portals', 'Water / contacts',
          'Waterfall / FX', 'Objects', 'Foreground']


def sha(data):
    return hashlib.sha256(data).hexdigest()


def eligible(name):
    low = name.lower()
    return (low.endswith('.png') and
            (name.startswith('Terrain/') or name.startswith('Terrain Objects/')) and
            not any(item in low for item in EXCLUDED))


def require_inside(path, root):
    path = path.resolve()
    root = root.resolve()
    if not path.is_relative_to(root):
        raise ValueError(f'Source outside repo: {path}')
    return path.relative_to(root).as_posix()


def recover(repo, source_root, pack_zip, demo_zip, out):
    repo, source_root, out = repo.resolve(), source_root.resolve(), out.resolve()
    require_inside(out, repo)
    if out.exists():
        raise FileExistsError(f'Refusing to replace existing project: {out}')
    if not source_root.is_dir():
        raise FileNotFoundError(f'Missing original extracted pack: {source_root}')
    with zipfile.ZipFile(pack_zip) as pack:
        members = sorted(name for name in pack.namelist() if eligible(name))
        if not members:
            raise ValueError('Original pack contains no eligible Summer/neutral sheets')
        lookup = collections.defaultdict(list)
        sources = {}
        rejected = []
        for name in members:
            target = source_root.joinpath(*Path(name).parts)
            expected = pack.read(name)
            if not target.is_file():
                rejected.append({'name': name, 'reason': 'not installed at expected original relative path'})
                continue
            installed = target.read_bytes()
            if installed != expected:
                rejected.append({'name': name, 'reason': 'source bytes disagree with supplied original ZIP',
                                 'expected_sha256': sha(expected), 'installed_sha256': sha(installed)})
                continue
            try:
                image = Image.open(io.BytesIO(installed)).convert('RGBA')
                image.load()
            except Exception as exc:
                rejected.append({'name': name, 'reason': f'PNG decode failed: {exc}'})
                continue
            if image.width % TILE or image.height % TILE:
                rejected.append({'name': name, 'reason': 'image is not a full 32px cell grid'})
                continue
            relative = require_inside(target, repo)
            sid = 'source:' + relative.lower()
            sources[sid] = {'id': sid, 'path': relative, 'file_name': target.name,
                            'source_sha256': sha(expected), 'archive_member': name}
            for sy in range(image.height // TILE):
                for sx in range(image.width // TILE):
                    rgba = image.crop((sx*TILE, sy*TILE, (sx+1)*TILE, (sy+1)*TILE))
                    if not rgba.getchannel('A').getbbox():
                        continue
                    lookup[sha(rgba.tobytes())].append((sid, sx, sy))
    with zipfile.ZipFile(demo_zip) as demo_source:
        reference_name = '_ Test Scenes/DemoGame - 2 - Summer.png'
        reference_bytes = demo_source.read(reference_name)
    demo = Image.open(io.BytesIO(reference_bytes)).convert('RGBA')
    demo.load()
    if demo.width % TILE or demo.height % TILE:
        raise ValueError('Demo image is not a 32px-aligned scene')
    overlay = demo.copy()
    draw = ImageDraw.Draw(overlay, 'RGBA')
    counts = collections.Counter()
    tiles = []
    pieces = []
    selected_sources = set()
    idx = 1
    for gy in range(demo.height // TILE):
        for gx in range(demo.width // TILE):
            tile = demo.crop((gx*TILE, gy*TILE, (gx+1)*TILE, (gy+1)*TILE))
            choices = lookup.get(sha(tile.tobytes()), [])
            if len(choices) == 1:
                sid, sx, sy = choices[0]
                # A pixel-identical complete tile proves only image provenance.
                # It cannot establish source semantics, collision or elevation.
                pieces.append({'id': idx, 'source_tile_x': sx, 'source_tile_y': sy,
                               'source_rect': [sx*TILE, sy*TILE, TILE, TILE],
                               'canvas_grid_x': gx, 'canvas_grid_y': gy,
                               'rotation_degrees': 0, 'flip_x': False, 'flip_y': False,
                               'layer': 0, 'semantic_role': 'reference_pixel_match_unreviewed',
                               'source_asset_id': sid})
                idx += 1
                selected_sources.add(sid)
                state, border = 'unique_match_candidate', (55, 255, 94, 210)
            elif choices:
                state, border = 'ambiguous_identical_sources', (255, 187, 24, 210)
            else:
                state, border = 'unmatched_or_layered', (255, 63, 78, 205)
            counts[state] += 1
            draw.rectangle((gx*TILE, gy*TILE, (gx+1)*TILE-1, (gy+1)*TILE-1), outline=border, width=1)
            tiles.append({'x': gx, 'y': gy, 'state': state,
                          'matches': [{'source_asset_id': sid, 'source_x': sx, 'source_y': sy}
                                      for sid, sx, sy in choices]})
    if not pieces:
        raise ValueError('No uniquely matched source tiles; refusing to produce an empty candidate')
    chosen = [sources[sid] for sid in sorted(selected_sources)]
    active = chosen[0]
    report = {'schema': 'havenwild.elizawy_summer_reference_recovery.v0_1',
              'baseline': 'B48R25/796895a5dd2aae3cbf3dcca37f73a54df94969ad',
              'status': 'source_exact_partial_candidate_not_approved',
              'reference': reference_name, 'reference_sha256': sha(reference_bytes),
              'reference_dimensions': [demo.width, demo.height],
              'source_pack_sha256': sha(pack_zip.read_bytes()), 'source_pack': pack_zip.name,
              'counts': dict(counts), 'rejected_sources': rejected,
              'source_documents': chosen, 'cells': tiles,
              'limitations': ['Exact complete-tile image equality is not semantic mapping.',
                              'Unmatched cells may be composed overlays, effects, shifted sprites or absent artwork.',
                              'Identical pixel matches are ambiguous; none are silently selected.',
                              'No elevation, collisions, connectivity, dual-grid recipes or gameplay logic inferred.',
                              'No full summer master scene, seeded generation or Windows PCC gate claimed.']}
    project = {'schema': 'havenwild.atlas_mapper_project.v0_7',
               'tool': 'haven_atlas_mapper_lite', 'source_atlas_path': active['path'],
               'source_atlas_file_name': active['file_name'], 'source_is_modified': False,
               'tile_size': TILE, 'category': 'terrain', 'category_label': 'Terrain',
               'assembly_name': 'Summer artist-reference partial recovery — UNREVIEWED',
               'next_piece_id': idx, 'source_pan': [0.0, 0.0], 'source_zoom': 1.0,
               'canvas_pan': [0.0, 0.0], 'canvas_zoom': 1.0,
               'pieces': pieces,
               'source_assets': [{k: v for k, v in source.items() if k != 'archive_member'} for source in chosen],
               'active_source_asset_id': active['id'], 'heightmap': [],
               'authoring_notes': [
                   'UNREVIEWED PARTIAL RECOVERY: This is not the finished summer master demo.',
                   'Only source tiles with exactly ONE complete pixel-identical match were placed.',
                   'See companion recovery ledger for unmatched and ambiguous regions.',
                   'Do not use this candidate for generation, publishing, certification, collision or traversal.',
                   'Do not overwrite the existing elizawy_summer_master.mapper.json with this file.',
               ], 'layer_visibility': [True]*len(LAYERS),
               'layer_locks': [False]*len(LAYERS), 'active_layer': 0}
    out.parent.mkdir(parents=True, exist_ok=True)
    report_path = out.with_suffix('.recovery.json')
    preview_path = out.with_suffix('.diagnostic.png')
    for dest in (report_path, preview_path):
        if dest.exists():
            raise FileExistsError(f'Refusing to replace existing evidence: {dest}')
    out.write_text(json.dumps(project, indent=2) + '\n', encoding='utf-8')
    report_path.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    overlay.save(preview_path)
    print(json.dumps({'project': str(out), 'report': str(report_path),
                      'diagnostic': str(preview_path), 'counts': dict(counts),
                      'original_sheets': len(members), 'eligible_installed_sheets': len(sources),
                      'rejected_sources': len(rejected)}, indent=2))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--source-root', type=Path, required=True,
                        help='Installed original ElizaWy 4-season pack folder containing Terrain/ and Terrain Objects/')
    parser.add_argument('--pack-zip', type=Path, required=True)
    parser.add_argument('--demo-zip', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    recover(args.repo, args.source_root, args.pack_zip, args.demo_zip, args.out)


if __name__ == '__main__':
    main()
