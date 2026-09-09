from __future__ import annotations

import json
import tempfile
from pathlib import Path


def find_repo() -> Path:
    p = Path(__file__).resolve()
    for parent in p.parents:
        if (
            (parent / "Cargo.toml").is_file()
            and (parent / "tools/automation/assets/pcc_assets").is_dir()
        ):
            return parent
    raise SystemExit("Havenwild repo root not found")


def main() -> int:
    repo = find_repo()
    import sys
    sys.path.insert(0, str(repo))

    from tools.automation.assets.pcc_assets.cache import AssetCache, hash_records
    from tools.automation.assets.pcc_assets.classify import (
        classify_asset_path, variant_family_key,
    )
    from tools.automation.assets.pcc_assets.catalog import PROFILE_NAMES

    checks = {}

    checks["profiles"] = {
        "status": "PASS" if {
            "smart", "index", "terrain", "structures",
            "characters", "full",
        }.issubset(set(PROFILE_NAMES)) else "FAIL"
    }

    c1 = classify_asset_path(
        "Terrain/cliff_summer.png", 512, 448, 32, 32
    )
    c2 = classify_asset_path(
        "Characters/Body/_Alternate Colors/Amber/Idle.png",
        832, 1344, 32, 32,
    )
    checks["domainRouting"] = {
        "status": "PASS" if (
            c1["domain"] == "terrain"
            and c1["analyzerRoute"] == "sheet_deep"
            and c2["domain"] == "character"
            and c2["analyzerRoute"] == "character_family"
        ) else "FAIL"
    }

    v1 = variant_family_key(
        "Characters/Body/_Alternate Colors/Amber/Idle.png"
    )
    v2 = variant_family_key(
        "Characters/Body/_Alternate Colors/Azure/Idle.png"
    )
    checks["variantFamily"] = {
        "status": "PASS" if v1 == v2 else "FAIL"
    }

    with tempfile.TemporaryDirectory(prefix="pcc-scale01-") as td:
        td = Path(td)
        a = td / "a.bin"
        b = td / "b.bin"
        a.write_bytes(b"same-content")
        b.write_bytes(b"same-content")
        recs = []
        for p in (a, b):
            st = p.stat()
            recs.append({
                "physicalPath": str(p),
                "bytes": st.st_size,
                "mtimeNs": st.st_mtime_ns,
            })

        cache_path = td / "cache.sqlite"
        cache = AssetCache(cache_path)
        first = hash_records(recs, cache, 2)
        second_recs = []
        for p in (a, b):
            st = p.stat()
            second_recs.append({
                "physicalPath": str(p),
                "bytes": st.st_size,
                "mtimeNs": st.st_mtime_ns,
            })
        second = hash_records(second_recs, cache, 2)
        cache.close()

        checks["persistentHashCache"] = {
            "status": "PASS" if (
                first["hashedNow"] == 2
                and second["cacheHits"] == 2
                and second_recs[0]["sha256"] == second_recs[1]["sha256"]
                and cache_path.is_file()
            ) else "FAIL"
        }

    failed = [k for k, v in checks.items() if v["status"] != "PASS"]
    result = {
        "schema": "pcc.asset.scale_validation.v1",
        "status": "FAIL" if failed else "PASS",
        "checks": checks,
        "failed": failed,
    }
    print(json.dumps(result, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
