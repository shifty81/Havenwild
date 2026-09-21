#!/usr/bin/env python3
"""Classify EXISTING Bevy launch text for reproducible GPU triage. Read-only.
No renderer modification; no automatic GPU/art certification from exit code 0.
"""
import argparse
import json
import re
from pathlib import Path

VUIDS = ('VUID-VkPresentInfoKHR-pImageIndices-01430',
         'VUID-vkAcquireNextImageKHR-semaphore-01286')

def inspect(text: str) -> dict:
    backend = re.findall(r'AdapterInfo\s*\{[^\n]*?backend:\s*([A-Za-z0-9_]+)', text)
    return {
        'schema':'havenwild.experimental.gpu_log_audit.v1',
        'status':'VALIDATION_ERROR_OBSERVED' if any(v in text for v in VUIDS)
                 else 'NO_TARGET_VUID_OBSERVED_IN_PROVIDED_TEXT_NOT_A_CLEAN_GPU_CERTIFICATION',
        'actualAdapterBackend':backend[-1] if backend else 'NOT_IN_LOG',
        'presentLayoutErrorCount':len(re.findall(r'VALIDATION\s+\[' + re.escape(VUIDS[0]), text)),
        'acquireSemaphoreErrorCount':len(re.findall(r'VALIDATION\s+\[' + re.escape(VUIDS[1]), text)),
        'gpuValidated':False,'sourceArtApproved':False,'pieCertified':False,
        'caveat':'Log completeness, driver/validation config and real frame output require separate review',
    }

def main(argv=None) -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--log', type=Path, required=True)
    args=parser.parse_args(argv)
    if not args.log.is_file() or args.log.is_symlink():
        parser.error('Pass one existing regular Bevy console or PCC action log file')
    if args.log.stat().st_size>32*1024*1024:
        parser.error('Log too large (>32 MiB); select the focused Bevy action log')
    print(json.dumps(inspect(args.log.read_text(encoding='utf-8',errors='replace')), indent=2))
    return 0
if __name__ == '__main__':
    raise SystemExit(main())
