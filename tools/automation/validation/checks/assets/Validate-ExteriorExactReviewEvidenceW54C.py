#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
CONTRACT = ROOT / "content/buildings/exterior_exact_region_review_contract_v1.json"
EXTERIOR = ROOT / "content/buildings/exterior_grammar_contract_v1.json"
INVENTORY = ROOT / "content/assets/lpc/structure_source_inventory_v1.json"
BUILDER = ROOT / "tools/automation/assets/Build-ExteriorExactReviewEvidenceW54C.py"
WORK = ROOT / "WORKSPACE/generated/structure_review/w54c_exterior_exact/manifest.json"


def need(v, msg):
    if not v:
        raise SystemExit("FAIL W54C exterior exact review evidence: " + msg)


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    need(CONTRACT.is_file(), "review contract missing")
    need(EXTERIOR.is_file(), "W54A exterior contract missing")
    need(INVENTORY.is_file(), "structure source inventory missing")
    need(BUILDER.is_file(), "evidence builder missing")
    c = load(CONTRACT)
    e = load(EXTERIOR)
    inv = load(INVENTORY)

    need(c.get("schema") == "havenwild.exterior_exact_region_review_contract.v1", "schema drift")
    need(c.get("pass") == "167Z109W54C", "pass drift")
    need(c.get("sourceCommit") == "f07f7f5892e67c932c68f70bb04472f2c64e46bc", "pinned LPC commit drift")
    policy = c.get("reviewPolicy", {})
    for key in (
        "humanVisualReviewRequired",
        "exactSourceRectRequiredBeforePublication",
        "wholeBuildingSheetsReferenceOnly",
        "wholeBuildingSheetAsPlaceableForbidden",
        "wrongFacingRotationForbidden",
        "wrongFacingMirroringForbidden",
        "runtimeBindingChangesForbiddenInThisPass",
        "estateRecipeChangesForbiddenInThisPass",
    ):
        need(policy.get(key) is True, f"review policy {key} must remain true")

    roles = c.get("requiredExteriorRoles", [])
    need(len(roles) == len(set(roles)) and len(roles) >= 24, "exterior role queue incomplete or duplicated")
    sources = c.get("sources", [])
    need(len(sources) >= 18, "targeted exterior source queue unexpectedly small")
    paths = [s.get("path") for s in sources]
    need(len(paths) == len(set(paths)), "duplicate source path in W54C queue")

    by_path = {x.get("sourcePath"): x for x in inv.get("entries", [])}
    for s in sources:
        rec = by_path.get(s["path"])
        need(rec is not None, f"source not present in W45A inventory: {s['path']}")
        need(rec.get("role") in {"wall", "window", "door", "roof"}, f"unexpected inventory role for {s['path']}")

    refs = c.get("referenceOnlyBuildingSheets", [])
    need(len(refs) == 3, "three authored whole-building reference sheets required")
    for rel in refs:
        rec = by_path.get(rel)
        need(rec is not None and rec.get("role") == "building_reference", f"building reference inventory mismatch: {rel}")
        cert = rec.get("certification", {})
        need(cert.get("componentRectsReviewed") is False and cert.get("runtimeCertified") is False, f"whole-building reference falsely promoted: {rel}")

    # W54C remains historical evidence authority. Later passes may publish reviewed selections,
    # but unresolved side/back facings must remain fail-closed and the W54C evidence contract
    # itself may not be rewritten retroactively.
    starter = e.get("estateStarterCottage", {})
    need(starter.get("deferredExactFacings") == ["north", "east", "west"], "later exterior authority published unreviewed side/back facings")
    if e.get("pass") == "167Z109W54A":
        need(starter.get("status") == "candidate_exact_frontage", "historical W54A cottage visual status drifted")
    else:
        need(e.get("pass") in {"167Z109W54E"}, "unexpected forward exterior authority pass")
        need(starter.get("status") == "candidate_two_room_exact_frontage_hipped_roof", "forward cottage visual status drifted")

    if WORK.is_file():
        w = load(WORK)
        need(w.get("schema") == "havenwild.exterior_exact_review_evidence.v1", "machine-local evidence schema drift")
        need(w.get("sourceCommit") == c.get("sourceCommit"), "machine-local evidence commit drift")
        need(w.get("publicationAllowed") is False, "machine-local evidence must never be publication authority")
        for src in w.get("sources", []):
            need(src.get("nonEmptyCells", 0) > 0, f"empty evidence source: {src.get('sourcePath')}")
            need(str(src.get("board", "")).endswith(".png"), "evidence board must be PNG")
        print(f"W54C machine-local exterior evidence present: {len(w.get('sources', []))} sheet(s)")
    else:
        print("W54C machine-local exterior evidence deferred (raw LPC dependency not mounted in this checkout)")

    print("PASS W54C exterior exact-source evidence authority")
    print("- W54C itself remains evidence-only; later reviewed selections may publish without rewriting this evidence contract")
    print("- whole-house sheets remain reference-only")
    print("- north/east/west cottage facings remain fail-closed pending exact human review")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
