#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
build_sh = (ROOT / "tools/build/Build.sh").read_text(encoding="utf-8")
build_cmd = (ROOT / "tools/build/Build.cmd").read_text(encoding="utf-8")
readme = (ROOT / "README.md").read_text(encoding="utf-8")

required_sh = [
    "set -Eeuo pipefail",
    "Havenwild bash build started",
    "Build log:",
    "doctor)",
    "apps) build_apps",
    "client) build_client",
    "cargo clippy --workspace --all-targets -- -D warnings",
]
for marker in required_sh:
    if marker not in build_sh:
        raise SystemExit(f"tools/build/Build.sh missing marker: {marker}")

required_cmd = [
    "HAVENWILD_BASH",
    "Git\\bin\\bash.exe",
    '"%BASH_EXE%" "./tools/build/Build.sh" %*',
]
for marker in required_cmd:
    if marker not in build_cmd:
        raise SystemExit(f"tools/build/Build.cmd missing marker: {marker}")

for forbidden in ("powershell.exe", "tools/build/Build.ps1"):
    if forbidden.lower() in build_cmd.lower():
        raise SystemExit(f"tools/build/Build.cmd still depends on forbidden PowerShell path: {forbidden}")

if "Git Bash (recommended on Windows)" not in readme:
    raise SystemExit("README does not document Git Bash as the canonical Windows build path")
if "do not run `cd .\\havenw` again" not in readme:
    raise SystemExit("README does not explain the repository-root path mistake")

print("Bash build entrypoint validation passed.")
