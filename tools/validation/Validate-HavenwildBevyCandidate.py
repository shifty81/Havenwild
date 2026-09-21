#!/usr/bin/env python3
"""PCC Full Gate's mandatory experimental Bevy candidate Python suite.

No independent GREEN marker. Any failure returns nonzero to the ONE PCC.
Rust compilation is separately checked by its normal registered Build operation.
"""
from __future__ import annotations
import argparse
import importlib.util
import subprocess
import sys
from pathlib import Path


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,required=True)
    ns=parser.parse_args(argv)
    root=ns.root.resolve(strict=True)
    gate_path=root/'experiments/haven_bevy_candidate/tools/candidate_gate.py'
    if not gate_path.is_file():
        print('[BLOCKED] Candidate gate unavailable; cannot certify experimental build',file=sys.stderr)
        return 2
    spec=importlib.util.spec_from_file_location('hw_bevy_gate_full_gate',gate_path)
    if spec is None or spec.loader is None:
        return 2
    gate=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gate)
    try:
        gate.project(root)
        gate.lane(root)
    except (gate.GateError,OSError,ValueError) as exc:
        print(f'[BLOCKED] Experimental Bevy gate cannot establish lane: {exc}',file=sys.stderr)
        return 2
    suites=[('Bevy candidate',root/'experiments/haven_bevy_candidate/tests','test_*.py'),
            ('ElizaWy publication boundary',root/'tests/architecture','test_elizawy_draw_plan_boundary.py'),
            ('Architecture convergence',root/'tests/architecture','test_engine_convergence_contract.py'),
            ('Parallel migration',root/'tests/architecture','test_parallel_migration.py')]
    for name,folder,pattern in suites:
        print(f'[PCC] Experimental candidate suite: {name}',flush=True)
        if not folder.is_dir():
            print(f'[BLOCKED] Missing suite folder {folder}',file=sys.stderr)
            return 2
        rc=subprocess.call([sys.executable,'-m','unittest','discover','-s',str(folder),'-p',pattern,'-q'],cwd=root)
        if rc:
            print(f'[BLOCKED] Experimental candidate suite failed ({name}), exit {rc}',file=sys.stderr)
            return rc
    print('[PCC] Candidate Python contracts passed; Rust/GPU/art/PIE still separately gated',flush=True)
    return 0

if __name__=='__main__':raise SystemExit(main())
