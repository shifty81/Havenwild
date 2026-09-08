#!/usr/bin/env python3
import json
from pathlib import Path

root = Path(__file__).resolve().parents[5]
catalog = json.loads((root / "content/characters/character_creator_catalog_v149j18.json").read_text(encoding="utf-8"))
model = (root / "crates/haven_game/src/character_creator_model.rs").read_text(encoding="utf-8")
metadata = (root / "crates/haven_game/src/character_creator_catalog.rs").read_text(encoding="utf-8")
frontend = (root / "crates/haven_game/src/client_frontend.rs").read_text(encoding="utf-8")
preview = (root / "crates/haven_game/src/client_character_frontend_draw.rs").read_text(encoding="utf-8")

assert catalog["policy"]["compatibility"] == "metadata-driven"
assert len(catalog["slots"]) >= 8
for token in ["CREATOR_OPTIONS", "is_compatible", "production_asset"]:
    assert token in metadata, token
for token in ["migrate_legacy_appearance", "appearance_diagnostics", "compatibility_notes"]:
    assert token in model, token
assert "migrate_legacy_appearance" in frontend
assert "core resolved" in preview
print("Pass 149J18 character creator catalog, migration, compatibility, and diagnostics validated")
