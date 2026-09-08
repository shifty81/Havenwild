#!/usr/bin/env python3
from __future__ import annotations

import csv
import gzip
import hashlib
import io
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
def load_json(relative: str) -> dict:
    path = ROOT / relative
    if not path.is_file():
        raise FileNotFoundError(relative)
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    lock = load_json("content/assets/intake/universal_lpc_generator_source_lock_v0_1.json")
    summary = load_json("content/assets/lpc/universal_lpc_character_source_summary_v0_1.json")
    policy = load_json("content/characters/universal_lpc_character_generation_policy_v0_1.json")
    profiles = load_json("content/characters/universal_lpc_npc_generation_profiles_v0_1.json")
    editor = load_json("content/editor/character_studio_universal_lpc_source_v0_1.json")

    if lock.get("schema") != "havenwild.universal_lpc_generator_source_lock.v0_1":
        raise ValueError("unexpected Universal LPC source-lock schema")
    if lock.get("commit") != "0f898bb675a1abe16ce430e82e3bf9daed278690":
        raise ValueError("Universal LPC source commit changed")
    if lock.get("archiveSha256") != "7a6ea376d41090b87182b669c74d5b6832ece92595da290b8f73f49e7fb432fc":
        raise ValueError("Universal LPC archive checksum changed")

    if summary.get("creditRecords") != 13818:
        raise ValueError("Universal LPC credit-record count changed")
    if summary.get("spritesheetFiles") != 88235:
        raise ValueError("Universal LPC spritesheet-file count changed")
    if summary.get("creditLicenseTiers") != {"preferred": 11780, "conditional": 2038}:
        raise ValueError("Universal LPC commercial license-tier summary changed")

    identity = policy.get("identity", {})
    if identity.get("sexValues") != ["Male", "Female"]:
        raise ValueError("Havenwild character sex values must remain Male/Female")
    if identity.get("ageGroups") != ["Child", "Teen", "Adult", "Elder"]:
        raise ValueError("Havenwild age groups changed")
    if identity.get("pronounFieldEnabled") is not False:
        raise ValueError("pronoun fields must remain disabled")
    if len(profiles.get("profiles", [])) < 7:
        raise ValueError("Universal LPC NPC generation profiles are incomplete")
    if editor.get("workspace") != "Character Studio":
        raise ValueError("Universal LPC source must be owned by Character Studio")

    credits_path = ROOT / "content/assets/lpc/licenses/universal_lpc_credits_snapshot_0f898bb6.csv.gz"
    catalog_path = ROOT / "content/assets/lpc/universal_lpc_commercial_catalog_v0_1.json.gz"
    with gzip.open(credits_path, "rt", encoding="utf-8") as stream:
        credits = list(csv.DictReader(stream))
    if len(credits) != 13818:
        raise ValueError("compressed Universal LPC credits snapshot is incomplete")
    with gzip.open(catalog_path, "rt", encoding="utf-8") as stream:
        catalog = json.load(stream)
    if len(catalog.get("records", [])) != 13818:
        raise ValueError("compressed Universal LPC commercial catalog is incomplete")
    tiers = {entry.get("licenseTier") for entry in catalog["records"]}
    if tiers - {"preferred", "conditional"}:
        raise ValueError(f"unexpected license tiers: {sorted(tiers)}")

    mounted = ROOT / lock["mountProjectPath"]
    if mounted.exists():
        for relative in lock["requiredTopLevelPaths"]:
            if not (mounted / relative).exists():
                raise ValueError(f"mounted Universal LPC source missing {relative}")
    else:
        print("INFO Universal LPC source mount absent; static lock, credits, and authority summary validated")

    print("Universal LPC character authority v167V validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
