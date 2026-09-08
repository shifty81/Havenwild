#!/usr/bin/env python3
"""Static validation for the Pass 93A LPC dependency mount contract."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
SCRIPT = ROOT / "tools/automation/dependencies/Ensure-LpcDependency.py"
text = SCRIPT.read_text(encoding="utf-8")

required = [
    "validate_checkout_location",
    "create_directory_link",
    "HAVENWILD_LPC_SOURCE_MODE",
    "mklink /J",
    "symlinks=True",
    "same_file(source, destination_file)",
    "LPC mirror progress",
]
missing = [token for token in required if token not in text]
if missing:
    raise SystemExit("missing LPC dependency mount safeguards: " + ", ".join(missing))
print("Pass 93A LPC dependency mount contract validated")
