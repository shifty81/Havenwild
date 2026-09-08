#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[5]
script = ROOT / 'tools/automation/validation/validate_architecture.py'
raise SystemExit(subprocess.call([sys.executable, str(script)], cwd=ROOT))
