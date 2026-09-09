from __future__ import annotations

import json
import tempfile
import zipfile
from pathlib import Path


def find_repo() -> Path:
    p = Path(__file__).resolve()
    for parent in p.parents:
        if (parent / "Cargo.toml").is_file() and (parent / "tools/automation/assets/pcc_assets").is_dir():
            return parent
    raise SystemExit("Havenwild repo root not found")


def main() -> int:
    repo = find_repo()
    import sys
    sys.path.insert(0, str(repo))

    from tools.automation.assets.pcc_assets.authority import (
        build_certification_queue, build_prefab_library, build_promotion_plan,
    )
    from tools.automation.assets.pcc_assets.intake import build_source_manifest
    from tools.automation.assets.pcc_assets.normalization import build_normalization_plan
    from tools.automation.assets.pcc_assets.services import service_registry

    checks = {}

    registry = service_registry()
    ids = {s["service_id"] for s in registry["services"]}
    checks["serviceRegistry"] = {
        "status": "PASS" if {
            "assets.intake.manifest",
            "assets.catalog.scan",
            "assets.prefab.generate",
            "assets.certification.queue",
            "assets.promote.plan",
        }.issubset(ids) else "FAIL"
    }

    with tempfile.TemporaryDirectory(prefix="pcc-asset02-") as td:
        td = Path(td)
        source = td / "source"
        source.mkdir()
        (source / "LICENSE.txt").write_text("Example License\n", encoding="utf-8")
        (source / "asset.json").write_text('{"x":1}\n', encoding="utf-8")
        manifest = build_source_manifest(source, "fixture")
        checks["sourceManifest"] = {
            "status": "PASS" if (
                manifest["summary"]["fileCount"] == 2
                and manifest["summary"]["provenanceEvidenceCount"] == 1
            ) else "FAIL"
        }

        zp = td / "safe.zip"
        with zipfile.ZipFile(zp, "w") as z:
            z.writestr("pack/CREDITS.txt", "Artist\n")
            z.writestr("pack/item.json", "{}")
        zmanifest = build_source_manifest(zp, "zip-fixture")
        checks["zipManifest"] = {
            "status": "PASS" if (
                zmanifest["containerType"] == "zip"
                and zmanifest["summary"]["fileCount"] == 2
            ) else "FAIL"
        }

    inventory = {
        "schema": "pcc.asset.legacy_tool_inventory.v1",
        "summary": {
            "toolCount": 3,
            "byNormalizationTarget": {"catalog": 1, "validate": 2},
        },
        "tools": [
            {"path": "tools/automation/assets/Generate-AssetCatalog.py",
             "normalizationTarget": "catalog",
             "recommendedAction": "extract_reusable_logic_then_wrapper"},
            {"path": "tools/automation/validation/A.py",
             "normalizationTarget": "validate",
             "recommendedAction": "extract_reusable_logic_then_wrapper"},
            {"path": "tools/automation/validation/B.py",
             "normalizationTarget": "validate",
             "recommendedAction": "extract_reusable_logic_then_wrapper"},
        ],
    }
    plan = build_normalization_plan(inventory)
    checks["normalizationPlan"] = {
        "status": "PASS" if (
            plan["sourceInventory"]["toolCount"] == 3
            and any(b["target"] == "catalog" for b in plan["batches"])
        ) else "FAIL"
    }

    catalog = {
        "sheets": [{
            "source": {"path": "fixture.png", "sha256": "a" * 64},
            "assemblies": [{
                "assemblyId": "a1",
                "footprint": [2, 2],
                "sourceRectPx": [0, 0, 64, 64],
                "certification": "candidate",
            }, {
                "assemblyId": "a2",
                "footprint": [3, 2],
                "sourceRectPx": [64, 0, 96, 64],
                "certification": "runtime_certified",
            }],
        }]
    }
    queue = build_certification_queue(catalog)
    promotion = build_promotion_plan(catalog)
    library = build_prefab_library(catalog)
    checks["certificationQueue"] = {
        "status": "PASS" if queue["summary"]["candidateCount"] == 1 else "FAIL"
    }
    checks["promotionSafety"] = {
        "status": "PASS" if (
            promotion["summary"]["promotionCount"] == 1
            and promotion["summary"]["blockedCount"] == 1
        ) else "FAIL"
    }
    checks["prefabLibrary"] = {
        "status": "PASS" if (
            library["summary"]["sourceNativePrefabCount"] == 2
            and library["summary"]["houseGrammarTemplateCount"] == 3
        ) else "FAIL"
    }

    failed = [name for name, rec in checks.items() if rec["status"] != "PASS"]
    result = {
        "schema": "pcc.asset.normalization_validation.v2",
        "status": "FAIL" if failed else "PASS",
        "checks": checks,
        "failed": failed,
    }
    print(json.dumps(result, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
