#!/usr/bin/env python3
"""Package one mapper correction cycle, without certifying its gameplay artwork."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import zipfile


def package(project: Path, png: Path, handoff: Path, out: Path, audit: Path | None = None) -> dict:
    project, png, handoff, out = (p.resolve() for p in (project, png, handoff, out))
    ledger = png.with_suffix('.review.json')
    files = {'mapper_project.json': project, 'scene_review.png': png,
             'scene_review.review.json': ledger, 'mapping_handoff.json': handoff}
    if audit is not None:
        files['scene_audit.json'] = audit.resolve()
    for name, file in files.items():
        if not file.is_file():
            raise ValueError(f'Missing {name}: {file}')
        if file == out:
            raise ValueError('Output must not overwrite evidence')
    if not png.read_bytes().startswith(b'\x89PNG\r\n\x1a\n'):
        raise ValueError('Review PNG signature missing')
    doc = json.loads(project.read_text(encoding='utf-8-sig'))
    review = json.loads(ledger.read_text(encoding='utf-8-sig'))
    candidate = json.loads(handoff.read_text(encoding='utf-8-sig'))
    if doc.get('schema') != 'havenwild.atlas_mapper_project.v0_6':
        raise ValueError('Unsupported mapper project schema')
    if review.get('approval') != 'unreviewed_source_assembly_not_for_runtime':
        raise ValueError('Review approval field changed unexpectedly')
    if candidate.get('certification_stage') != 'candidate_export_not_validated':
        raise ValueError('Handoff must be a non-certified candidate')
    if not candidate.get('iteration_coverage'):
        raise ValueError('No mapping-cycle coverage: export with B48R17 mapper')
    if review.get('placements') != candidate.get('pieces') or review.get('heightmap') != candidate.get('heightmap'):
        raise ValueError('Review and handoff are from different scene revisions')
    if review.get('source_assets') != candidate.get('source_assets'):
        raise ValueError('Review and handoff source identities differ')
    if doc.get('pieces') != candidate.get('pieces') or doc.get('heightmap') != candidate.get('heightmap'):
        raise ValueError('Saved project does not match exported candidate')
    if audit is not None:
        report = json.loads(files['scene_audit.json'].read_text(encoding='utf-8-sig'))
        if report.get('certification_stage') != 'unreviewed_candidate_no_runtime_publication':
            raise ValueError('Scene audit missing candidate status')
    receipts = [{'file': name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                 'bytes': path.stat().st_size} for name, path in sorted(files.items())]
    coverage = candidate['iteration_coverage']
    summary = {'schema': 'havenwild.mapper_iteration_packet.v0_1',
               'status': 'UNREVIEWED_CANDIDATE_NOT_FOR_GAME_RUNTIME',
               'generation_passes': candidate.get('generation_passes', 0),
               'source_count': len(coverage),
               'missing_source_addresses': sum(len(s.get('missing_cells', [])) for s in coverage),
               'unresolved_scene_cells': sum(s.get('unresolved_scene_cells', 0) for s in coverage),
               'files': receipts,
               'notes': ['Original source PNG bytes are not embedded; see source_assets paths and pinned hashes.',
                         'Source pixel replay and visual/topology approval must be checked separately.',
                         'No green gate, runtime publication or approved cliff-water recipe is inferred.']}
    if out.parent != Path('.'):
        out.parent.mkdir(parents=True, exist_ok=True)
    temp = out.with_name(out.name + '.pending')
    try:
        with zipfile.ZipFile(temp, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as z:
            z.writestr('ITERATION_MANIFEST.json', json.dumps(summary, indent=2) + '\n')
            for name, path in sorted(files.items()):
                z.write(path, name)
        with zipfile.ZipFile(temp) as z:
            if z.testzip() is not None:
                raise ValueError('Iteration ZIP CRC failed')
            for receipt in receipts:
                if hashlib.sha256(z.read(receipt['file'])).hexdigest() != receipt['sha256']:
                    raise ValueError('Iteration ZIP SHA-256 verification failed')
        os.replace(temp, out)
    finally:
        if temp.exists():
            temp.unlink()
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', required=True, type=Path)
    parser.add_argument('--png', required=True, type=Path)
    parser.add_argument('--handoff', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--audit', type=Path)
    args = parser.parse_args()
    try:
        summary = package(args.project, args.png, args.handoff, args.out, args.audit)
    except (ValueError, OSError, json.JSONDecodeError, zipfile.BadZipFile) as error:
        print(f'BLOCKED: {error}', file=sys.stderr)
        return 1
    print(f'PASS candidate ZIP: {args.out}; sheets={summary["source_count"]}, '
          f'missing={summary["missing_source_addresses"]}; NOT runtime certified')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
