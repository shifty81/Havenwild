#!/usr/bin/env python3
from pathlib import Path
root = Path(__file__).resolve().parents[3]
checks = {
    "tools/automation/validation/checks/terrain/Validate-LpcMixedCornerTopologyV116.py": ["tools/build/Build.sh", "tools/automation/validation/validate.py"],
    "tools/automation/validation/checks/terrain/Validate-LpcClosedSandGrassCornerTopologyV121.py": ["tools/build/Build.sh", "tools/automation/validation/validate.py"],
}
for rel, forbidden in checks.items():
    text = (root / rel).read_text(encoding="utf-8")
    for token in forbidden:
        assert token not in text, f"{rel} still self-registers through {token}"
v122 = (root / "tools/automation/validation/checks/terrain/Validate-LpcMappedTerrainReplacementV122.py").read_text(encoding="utf-8")
assert "build mapped LPC terrain replacement atlas" in v122
assert "Validate-LpcMappedTerrainReplacementV122.py\"]" not in v122
assert 'require_text("tools/automation/validation/validate.py"' not in v122
print("Pass 156A1 OK: current terrain capability validators no longer require direct historical build registration")
