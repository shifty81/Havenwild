#!/usr/bin/env python3
"""Read-only B48R28A evidence lock, historical policy inventory, and shadow-output comparison.

No game/editor execution, asset publication, PCC command execution, or save writes.
This tool never reports a PCC or runtime certification result.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import Any

BASELINE_COMMIT = "796895a5dd2aae3cbf3dcca37f73a54df94969ad"
FORGE_COMMIT = "eafa8e78efd54142a19e66d8be7b7d3985af23d2"
SCHEMA = "havenwild.parallel_parity_fixture.v1"

# Existence indicates a historical contract, not proof that it is active today.
HISTORICAL_CONTRACTS = {
    "elevation_core": ("crates/haven_core/src/foundation.rs", "MAX_STRUCTURAL_LEVEL"),
    "elevation_normalizer": ("crates/haven_world/src/structural_elevation_normalization.rs", ""),
    "tuple_resolver": ("crates/haven_world/src/terrain_tuple_resolver.rs", ""),
    "draw_plan": ("crates/haven_assets/src/authored_terrain_provider.rs", "AuthoredSurfaceDrawPlanV2"),
    "world_boundary": ("content/worldgen/archipelago_world_skeleton_v1.json", "east_west_wrapped"),
    "season_coordinates": ("content/assets/lpc/lpc_seasonal_terrain_topology_v0_1.json", ""),
    "vault_dependencies": ("content/architecture/pcc_vault_dependencies_v1.json", ""),
    "mapper_gui": ("apps/haven_atlas_mapper_lite/src/main.rs", "macroquad"),
    "pcc_authority": ("tools/forge/HavenwildPccProvider.py", ""),
}


class EvidenceError(ValueError):
    pass


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def safe_rel(value: Any) -> Path:
    if not isinstance(value, str) or not value or "\\" in value or "\x00" in value:
        raise EvidenceError("Invalid relative path")
    p = PurePosixPath(value)
    if not p.parts or p.is_absolute() or any(seg in ("", ".", "..") or seg.endswith((".", " ")) for seg in p.parts) or ":" in value:
        raise EvidenceError(f"Unsafe relative path: {value}")
    return Path(*p.parts)


def existing_file(root: Path, rel: Any) -> Path:
    root = root.resolve(strict=True)
    path = root / safe_rel(rel)
    resolved = path.resolve(strict=True)
    if not resolved.is_relative_to(root) or not resolved.is_file():
        raise EvidenceError(f"File escapes root or is not a file: {rel}")
    return resolved


def json_file(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise EvidenceError(f"Expected JSON object: {path}")
    return value


def git(root: Path, *args: str) -> str | None:
    try:
        run = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True,
                             timeout=8, check=False)
        return run.stdout.strip() if run.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired):
        return None


def evidence_lock(root: Path, forge_root: Path | None = None) -> dict[str, Any]:
    root = root.resolve(strict=True)
    head = git(root, "rev-parse", "HEAD")
    branch = git(root, "symbolic-ref", "--quiet", "--short", "HEAD")
    worktree = git(root, "status", "--porcelain=v1", "--untracked-files=normal")
    last = root / ".havenwild/updates/last-applied.json"
    marker = root / ".havenwild/last-green-quality-gate.json"
    applied = json_file(last) if last.is_file() else None
    certified = json_file(marker) if marker.is_file() else None
    problems: list[str] = []
    if head is None or branch is None or worktree is None:
        problems.append("Git working-tree evidence missing; archive-only source cannot establish live checkout")
    if branch is not None and branch != "experimental":
        problems.append(f"Unexpected branch: {branch}")
    # The original B48R25 commit remains the exact historical comparison anchor;
    # later certified descendants need a separate lineage receipt, not fake SHA equality.
    anchor = git(root, "merge-base", "--is-ancestor", BASELINE_COMMIT, "HEAD")
    if head and head != BASELINE_COMMIT and anchor is None:
        problems.append("B48R25 commit is not demonstrably an ancestor of this checkout")
    if not last.is_file():
        problems.append("PCC applied-patch ledger missing: cannot determine B48R26/R27 state")
    elif applied is None:
        problems.append("PCC applied-patch ledger malformed")
    forge = None
    if forge_root is not None:
        forge_root = forge_root.resolve(strict=True)
        forge = {"path": str(forge_root), "head": git(forge_root, "rev-parse", "HEAD")}
        if forge["head"] != FORGE_COMMIT:
            problems.append("ForgeGUI source does not match pinned dependency commit")
    return {
        "schema": "havenwild.parallel_evidence_lock.v1",
        "inspectionOnly": True,
        "projectRoot": str(root), "branch": branch, "head": head,
        "historicalBaselineCommit": BASELINE_COMMIT,
        "workingTreeClean": worktree == "" if worktree is not None else None,
        "lastApplied": {k: applied.get(k) for k in ("pass", "patchId", "result")}
        if applied else None,
        "lastGate": {k: certified.get(k) for k in ("pass", "result", "runId")}
        if certified else None,
        "forgeGuiPin": FORGE_COMMIT, "forgeGuiObserved": forge,
        "status": "EVIDENCE_INCOMPLETE" if problems else "EVIDENCE_PRESENT_NOT_CERTIFIED",
        "blockers": problems,
        "pccFullGate": "NOT_RUN", "sourceMutation": False,
    }


def policy_inventory(root: Path) -> dict[str, Any]:
    root = root.resolve(strict=True)
    rows = []
    for role, (relative, needle) in HISTORICAL_CONTRACTS.items():
        try:
            file = existing_file(root, relative)
            raw = file.read_bytes()
            rows.append({"role": role, "path": relative, "exists": True,
                         "sha256": digest(raw), "markerPresent": needle.encode() in raw if needle else None,
                         "runtimeActive": "UNDETERMINED_CALL_SITE_AUDIT_REQUIRED"})
        except (FileNotFoundError, EvidenceError, OSError):
            rows.append({"role": role, "path": relative, "exists": False,
                         "runtimeActive": "NOT_ESTABLISHED"})
    return {"schema": "havenwild.parallel_policy_inventory.v1", "inspectionOnly": True,
            "status": "HISTORICAL_INVENTORY_NOT_CERTIFIED",
            "root": str(root), "contracts": rows, "pccFullGate": "NOT_RUN",
            "note": "Historical contract presence is NOT proof that a runtime invokes the path."}


def strict_equal(old: Any, new: Any) -> bool:
    if type(old) is not type(new):
        return False
    if isinstance(old, dict):
        return old.keys() == new.keys() and all(strict_equal(old[k], new[k]) for k in old)
    if isinstance(old, list):
        return len(old) == len(new) and all(strict_equal(a, b) for a, b in zip(old, new))
    return old == new


def first_difference(old: Any, new: Any, where: str = "$", depth: int = 0) -> str:
    if depth > 64:
        return f"{where}: depth limit exceeded"
    if type(old) is not type(new):
        return f"{where}: type differs ({type(old).__name__} vs {type(new).__name__})"
    if isinstance(old, dict):
        if old.keys() != new.keys():
            return f"{where}: keys differ"
        for key in sorted(old):
            if not strict_equal(old[key], new[key]):
                return first_difference(old[key], new[key], f"{where}.{key}", depth + 1)
    elif isinstance(old, list):
        if len(old) != len(new):
            return f"{where}: array lengths differ"
        for index, (a, b) in enumerate(zip(old, new)):
            if not strict_equal(a, b):
                return first_difference(a, b, f"{where}[{index}]", depth + 1)
    elif old != new:
        return f"{where}: value differs"
    return "different encoding only" if old != new else ""


def validate_hash(value: Any, label: str) -> str:
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise EvidenceError(f"{label} must be a lowercase SHA-256 hex string")
    return value


def compare_fixture(baseline: Path, candidate: Path, fixture_path: Path) -> dict[str, Any]:
    baseline, candidate = baseline.resolve(strict=True), candidate.resolve(strict=True)
    if baseline == candidate or baseline.is_relative_to(candidate) or candidate.is_relative_to(baseline):
        raise EvidenceError("Baseline and candidate must be separate non-nested roots")
    fixture_path = fixture_path.resolve(strict=True)
    fixture = json_file(fixture_path)
    if fixture.get("schema") != SCHEMA:
        raise EvidenceError("Unexpected parity fixture schema")
    fixture_id = fixture.get("id")
    if not isinstance(fixture_id, str) or not re.fullmatch(r"[A-Za-z0-9_.-]{1,80}", fixture_id):
        raise EvidenceError("Fixture ID must be stable and safe")
    if not fixture.get("inputs") or not fixture.get("outputs"):
        raise EvidenceError("Fixture must declare both immutable inputs and output comparisons")
    if not isinstance(fixture["inputs"], list) or not isinstance(fixture["outputs"], list):
        raise EvidenceError("Fixture inputs/outputs must be arrays")
    cases: list[dict[str, Any]] = []
    encountered = set()
    for row in fixture["inputs"]:
        if not isinstance(row, dict):
            raise EvidenceError("Invalid input record")
        rel = str(safe_rel(row.get("path")))
        if rel.casefold() in encountered:
            raise EvidenceError(f"Duplicate input/output path: {rel}")
        encountered.add(rel.casefold())
        expected = validate_hash(row.get("sha256"), "input sha256")
        a = digest(existing_file(baseline, rel).read_bytes())
        b = digest(existing_file(candidate, rel).read_bytes())
        cases.append({"kind": "input", "path": rel, "status": "MATCH" if a == b == expected else "BLOCKED",
                      "expectedSha256": expected, "baselineSha256": a, "candidateSha256": b})
    for row in fixture["outputs"]:
        if not isinstance(row, dict):
            raise EvidenceError("Invalid output record")
        rel = str(safe_rel(row.get("path")))
        if rel.casefold() in encountered:
            raise EvidenceError(f"Duplicate input/output path: {rel}")
        encountered.add(rel.casefold())
        comparison = row.get("comparison")
        policy = row.get("policy")
        if comparison not in ("bytes", "json") or policy not in ("preserve", "intentional"):
            raise EvidenceError(f"Unsupported comparison/policy: {rel}")
        raw_a, raw_b = existing_file(baseline, rel).read_bytes(), existing_file(candidate, rel).read_bytes()
        sha_a, sha_b = digest(raw_a), digest(raw_b)
        if comparison == "json":
            a = json.loads(raw_a.decode("utf-8-sig"))
            b = json.loads(raw_b.decode("utf-8-sig"))
            equal = strict_equal(a, b)
            difference = first_difference(a, b) if not equal else ""
        else:
            equal = raw_a == raw_b
            difference = "binary bytes differ" if not equal else ""
        status = "MATCH" if equal else "BLOCKED"
        if policy == "intentional":
            expected_candidate = validate_hash(row.get("expectedCandidateSha256"), "intentional candidate hash")
            expected_baseline = validate_hash(row.get("expectedBaselineSha256"), "intentional baseline hash")
            rationale = row.get("rationale")
            if not isinstance(rationale, str) or len(rationale.strip()) < 20:
                raise EvidenceError("Intentional change requires a meaningful rationale")
            if sha_a == expected_baseline and sha_b == expected_candidate:
                status = "DECLARED_DIFFERENCE_NOT_APPROVED" if not equal else "MATCH"
            else:
                status = "BLOCKED"
        cases.append({"kind": "output", "path": rel, "comparison": comparison, "policy": policy,
                      "status": status, "baselineSha256": sha_a, "candidateSha256": sha_b,
                      "firstDifference": difference})
    blocked = any(row["status"] == "BLOCKED" for row in cases)
    intentional = any(row["status"] == "DECLARED_DIFFERENCE_NOT_APPROVED" for row in cases)
    return {"schema": "havenwild.parallel_comparison_receipt.v1", "fixtureId": fixture_id,
            "fixtureSha256": digest(fixture_path.read_bytes()), "baselineRoot": str(baseline),
            "candidateRoot": str(candidate), "cases": cases,
            "status": "BLOCKED" if blocked else ("REQUIRES_SPECIFICATION_APPROVAL" if intentional else "MATCH_DIAGNOSTIC_ONLY"),
            "pccFullGate": "NOT_RUN", "runtimeParityCertified": False,
            "sourceMutation": False, "note": "Compares EXISTING outputs only; it does not run an engine or certify intentional differences."}


def write_receipt(payload: dict[str, Any], destination: Path | None, protected: list[Path]) -> None:
    if destination is None:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return
    resolved = destination.resolve(strict=False)
    for root in protected:
        if resolved.is_relative_to(root.resolve(strict=True)):
            raise EvidenceError("Receipt output may not overwrite either source workspace")
    resolved.parent.mkdir(parents=True, exist_ok=True)
    temporary = resolved.with_name(resolved.name + f".tmp-{os.getpid()}")
    try:
        temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(temporary, resolved)
    finally:
        temporary.unlink(missing_ok=True)
    print(f"Wrote diagnostic receipt: {resolved}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest="action", required=True)
    lock = subs.add_parser("evidence-lock", help="Observe Git/PCC/Forge state, without mutating it")
    lock.add_argument("--root", type=Path, required=True)
    lock.add_argument("--forge-root", type=Path)
    inventory = subs.add_parser("inventory", help="Inventory historical source contracts without claiming active call sites")
    inventory.add_argument("--root", type=Path, required=True)
    comparison = subs.add_parser("compare", help="Compare already-generated, isolated baseline/candidate fixture outputs")
    comparison.add_argument("--baseline", type=Path, required=True)
    comparison.add_argument("--candidate", type=Path, required=True)
    comparison.add_argument("--fixture", type=Path, required=True)
    for sub in (lock, inventory, comparison):
        sub.add_argument("--out", type=Path, help="Optional diagnostic receipt OUTSIDE source roots")
    args = parser.parse_args(argv)
    try:
        if args.action == "evidence-lock":
            report = evidence_lock(args.root, args.forge_root)
            protected = [args.root] + ([args.forge_root] if args.forge_root else [])
        elif args.action == "inventory":
            report = policy_inventory(args.root)
            protected = [args.root]
        else:
            report = compare_fixture(args.baseline, args.candidate, args.fixture)
            protected = [args.baseline, args.candidate]
        write_receipt(report, args.out, protected)
        return 2 if report["status"] in ("BLOCKED", "EVIDENCE_INCOMPLETE") else 0
    except (EvidenceError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"schema": "havenwild.parallel_migration_error.v1", "error": str(exc),
                          "pccFullGate": "NOT_RUN"}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
