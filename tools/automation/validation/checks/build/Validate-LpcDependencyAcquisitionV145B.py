#!/usr/bin/env python3
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[5]
SCRIPT = ROOT / 'tools/automation/dependencies/Ensure-LpcDependency.py'
LOCK = ROOT / 'content/assets/intake/lpc_source_lock_v0_1.json'
REQUIRED = [
    LOCK,
    ROOT / 'content/assets/intake/lpc_terrain_summer_complete_map_v0_1.json',
    ROOT / 'content/assets/intake/lpc_terrain_family_mapping_v0_3.json',
    ROOT / 'content/assets/intake/lpc_terrain_promotion_v0_2.json',
]
missing = [str(path.relative_to(ROOT)) for path in REQUIRED if not path.is_file()]
if missing:
    raise SystemExit('Missing LPC bootstrap/runtime contracts:\n- ' + '\n- '.join(missing))
text = SCRIPT.read_text(encoding='utf-8')
required_tokens = [
    'HAVENWILD_LPC_CACHE',
    'LOCALAPPDATA',
    'core.longpaths=true',
    'New-Item -ItemType Junction',
    'HAVENWILD_LPC_ALLOW_COPY_FALLBACK',
    'Physical-copy fallback is disabled on Windows',
]
absent = [token for token in required_tokens if token not in text]
if absent:
    raise SystemExit('LPC acquisition hardening tokens missing:\n- ' + '\n- '.join(absent))
lock = json.loads(LOCK.read_text(encoding='utf-8'))
if lock.get('commit') != 'f07f7f5892e67c932c68f70bb04472f2c64e46bc':
    raise SystemExit('Pinned LPC commit changed unexpectedly')
if not lock.get('lockedFiles'):
    raise SystemExit('LPC lock has no locked files')
print('Pass 145B LPC dependency acquisition and runtime-contract bootstrap validated')
