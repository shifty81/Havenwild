#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
manifest = ROOT / "content/assets/oga_lpc/manifests/oga_lpc_commercial_intake_v0_1.json"
data = json.loads(manifest.read_text(encoding="utf-8"))
allowed = {"CC0-1.0", "CC-BY-4.0", "CC-BY-3.0", "OGA-BY-3.0", "CC-BY-SA-4.0", "CC-BY-SA-3.0"}
for asset in data["assets"]:
    assert asset["commercial_use"] is True, asset["id"]
    assert asset["selected_license"] in allowed, asset["id"]
    assert asset["authors"], asset["id"]
    for rel in asset["files"]:
        assert (ROOT / rel).is_file(), rel
print(f"OGA LPC commercial intake passed: {len(data['assets'])} approved submissions")
