#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import sys
sys.dont_write_bytecode = True
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools/automation"))

from validation.aliases import resolve_profile
from validation.context import ValidationContext
from validation.registry import load_registry, topological_order
from validation.reporting import write_combined_report
from validation.result import ValidationIssue, ValidationResult
from validation.native import invoke as invoke_native
from validation.readonly import snapshot as readonly_snapshot, changed as readonly_changed

REGISTRY = ROOT / "content/build/validator_registry_v4.json"
PROFILES = ROOT / "content/build/validation_profiles_v4.json"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def substitute(command: list[str]) -> list[str]:
    return [sys.executable if part == "{python}" else part for part in command]


def cargo_entries(names: list[str]) -> list[dict[str, Any]]:
    commands = {
        "fmt-check": ["cargo", "fmt", "--all", "--", "--check"],
        "check": ["cargo", "check", "--workspace", "--all-targets"],
        "clippy": ["cargo", "clippy", "--workspace", "--all-targets", "--", "-D", "warnings"],
        "test": ["cargo", "test", "--workspace"],
    }
    return [
        {
            "id": f"rust.compile.{name}", "legacy_task_id": f"cargo-{name}",
            "name": f"cargo {name}", "domain": "architecture", "phase": "compile",
            "severity": "error", "runner": "process", "command": commands[name],
            "order": 10000 + offset, "profiles": ["full"], "requires": [],
            "depends_on": [] if offset == 0 else [f"rust.compile.{names[offset-1]}"],
            "read_only": True,
        }
        for offset, name in enumerate(names)
    ]


def profile_entries(profile_name: str, domain_filter: set[str] | None) -> list[dict[str, Any]]:
    registry = load_registry(REGISTRY)
    entries = [entry for entry in registry["validators"] if profile_name in entry.get("profiles", [])]
    if domain_filter:
        entries = [entry for entry in entries if entry["domain"] in domain_filter]
    profiles = load_json(PROFILES)["profiles"]
    if profile_name == "full":
        entries.extend(cargo_entries(profiles["full"].get("cargo", [])))
    return topological_order(entries)


def run_entry(entry: dict[str, Any], context: ValidationContext, prior: dict[str, ValidationResult]) -> ValidationResult:
    started = time.time()
    failed_dependencies = [dep for dep in entry.get("depends_on", []) if dep in prior and prior[dep].status != "passed"]
    if failed_dependencies:
        return ValidationResult(
            validator_id=entry["id"], name=entry["name"], status="skipped",
            domain=entry["domain"], phase=entry["phase"], duration_seconds=time.time() - started,
            issues=[ValidationIssue("HWV-DEPENDENCY-001", "validator dependency did not pass")],
            skipped_because=failed_dependencies,
        )

    missing = [item for item in entry.get("requires", []) if not context.path(item).exists()]
    if missing:
        return ValidationResult(
            validator_id=entry["id"], name=entry["name"], status="failed",
            domain=entry["domain"], phase=entry["phase"], duration_seconds=time.time() - started,
            issues=[ValidationIssue("HWV-PREREQ-001", "required source prerequisite is missing", details={"missing": missing})],
        )

    print(f"START [{entry['domain']}/{entry['phase']}] {entry['name']}", flush=True)
    before = readonly_snapshot(context.root) if entry.get("read_only", True) else None
    if entry.get("runner") == "native":
        result = invoke_native(entry, context.root)
    else:
        command = substitute(entry["command"])
        completed = subprocess.run(command, cwd=context.root)
        status = "passed" if completed.returncode == 0 else "failed"
        issues = [] if status == "passed" else [ValidationIssue("HWV-PROCESS-001", "validator process returned a non-zero exit code", details={"exitCode": completed.returncode})]
        result = ValidationResult(
            validator_id=entry["id"], name=entry["name"], status=status,
            domain=entry["domain"], phase=entry["phase"], duration_seconds=time.time() - started,
            exit_code=completed.returncode, issues=issues, evidence=[" ".join(command)],
        )
    if before is not None:
        modified = readonly_changed(before, readonly_snapshot(context.root))
        if modified:
            result.status = "failed"; result.exit_code = 1
            result.issues.append(ValidationIssue("HWV-QUALITY-001", "validator modified read-only project sources", details={"modified": modified[:50]}))
    result.duration_seconds = time.time() - started
    if result.status == "failed" and result.issues:
        for issue in result.issues:
            location = f" [{issue.path}]" if issue.path else ""
            print(f"ISSUE {issue.code}{location}: {issue.message}", flush=True)
            modified = issue.details.get("modified") if isinstance(issue.details, dict) else None
            if isinstance(modified, list):
                for path in modified:
                    print(f"  modified: {path}", flush=True)
            elif issue.details:
                print(f"  details: {json.dumps(issue.details, sort_keys=True)}", flush=True)
    print(f"{result.status.upper()} {entry['name']} ({result.duration_seconds:.3f}s)", flush=True)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Unified Havenwild validation runner v4")
    parser.add_argument("profile", nargs="?", default="source")
    parser.add_argument("--domain", action="append", choices=["architecture", "content", "world", "editor"])
    parser.add_argument("--continue-on-error", action="store_true")
    parser.add_argument("--list", action="store_true")
    args = parser.parse_args()

    try:
        requested_profile = args.profile
        profile_name = resolve_profile(ROOT, requested_profile)
        profiles = load_json(PROFILES)["profiles"]
        if profile_name not in profiles:
            parser.error(f"unknown profile {requested_profile!r}; choose from {sorted(profiles)}")
        entries = profile_entries(profile_name, set(args.domain or []))
    except Exception as exc:
        print(f"HWV-MANIFEST-001 {exc}")
        return 2

    if args.list:
        if requested_profile != profile_name:
            print(f"alias {requested_profile} -> {profile_name}")
        for entry in entries:
            deps = ",".join(entry.get("depends_on", [])) or "-"
            print(f"{entry['order']:05d} {entry['domain']:12} {entry['id']} deps={deps}")
        return 0

    context = ValidationContext.discover(ROOT)
    started = dt.datetime.now(dt.timezone.utc)
    results: list[dict[str, Any]] = []
    prior: dict[str, ValidationResult] = {}
    for entry in entries:
        result = run_entry(entry, context, prior)
        prior[entry["id"]] = result
        item = result.to_dict(); item["order"] = entry["order"]; item["legacyTaskId"] = entry.get("legacy_task_id")
        results.append(item)
        if result.status == "failed" and not args.continue_on_error:
            break

    summary = {status: sum(1 for item in results if item["status"] == status) for status in ("passed", "failed", "skipped")}
    report = {
        "schema": "havenwild.validation.report.v3", "profile": profile_name,
        "requestedProfile": requested_profile, "registry": str(REGISTRY.relative_to(ROOT)),
        "status": "failed" if summary["failed"] else "passed", "startedAt": started.isoformat(),
        "durationSeconds": round((dt.datetime.now(dt.timezone.utc) - started).total_seconds(), 3),
        "summary": summary, "tasks": results,
    }
    json_path, md_path = write_combined_report(report, context.reports)
    print(f"Validation report: {json_path.relative_to(ROOT)}")
    print(f"Readable report: {md_path.relative_to(ROOT)}")
    return 1 if summary["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
