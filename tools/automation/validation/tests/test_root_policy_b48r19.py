#!/usr/bin/env python3
"""B48R19 regression: two root audits agree on required/optional root files."""
from pathlib import Path
import re
import runpy

ROOT = Path(__file__).resolve().parents[4]
validator = runpy.run_path(str(ROOT / "tools/automation/validation/validate_development_layout.py"))
script = (ROOT / "tools/control/AuditRoot.ps1").read_text(encoding="utf-8-sig")


def powershell_literal_set(variable: str) -> set[str]:
    match = re.search(r"(?m)^\$" + variable + r"=@\(([^\n]*)\)", script)
    assert match is not None, f"PowerShell ${variable} allowlist not found"
    return set(re.findall(r"'([^']+)'", match.group(1)))


required = validator["REQUIRED_ROOT_FILES"]
optional = validator["OPTIONAL_ROOT_FILES"]
allowed = validator["ALLOWED_ROOT_FILES"]
assert required == powershell_literal_set("required"), "required sets drift"
assert optional == powershell_literal_set("optional"), "optional sets drift"
assert allowed == required | optional
assert set(("ForgePY-GUI.cmd", "ForgePY-Install.cmd", "ForgePY-Verify.cmd", "ForgePY.cmd")) <= optional
assert not (allowed - required - optional)
assert not (required & optional)

# The exact B48R18 root with the tracked ForgePY launchers must pass.
actual = set(required | optional)
assert not (actual - allowed) and not (required - actual)
# Optional files must not become mandatory.
assert not (required - set(required))
# Unknown root files and duplicate downloads must remain fail-closed.
for junk in ("surprise.cmd", "unpacked.png", "Havenwild_CUMULATIVE_PCC_Patch_test (1).zip"):
    assert junk not in allowed
    assert {junk} - allowed == {junk}
# Removing a required project authority file must still be detected.
assert required - (actual - {"Cargo.toml"}) == {"Cargo.toml"}
print("PASS: PowerShell/Python required and optional root allowlists agree")
print("PASS: four tracked ForgePY launchers accepted; optional is optional")
print("PASS: unknown root files blocked; required root files enforced")
