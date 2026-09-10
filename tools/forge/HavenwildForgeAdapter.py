#!/usr/bin/env python3
"""Havenwild adapter for Forge/Vault.

This module is intentionally additive. It does not replace, rewrite, or import
Havenwild's internal Project Control Center. Stable Havenwild PCC command keys
are treated as the project-native execution API.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ADAPTER_SCHEMA = "forge.project.adapter.runtime.v1"
ADAPTER_VERSION = "1.0.0"
PROJECT_ID = "havenwild"
PROJECT_NAME = "Havenwild"

REQUIRED_FILES = (
    "Cargo.toml",
    "HavenwildTools.cmd",
    "tools/control/HavenwildTools.ps1",
    "tools/control/ProjectCommandRegistry.ps1",
    "tools/build/Build.cmd",
    ".forge/project.toml",
)
REQUIRED_DIRS = ("apps/haven_editor_native", "crates/haven_game")

COMMANDS: dict[str, dict[str, Any]] = {
    "project.status": {"pcc_key": "project.status", "category": "status", "mutates": False},
    "project.build": {"pcc_key": "build.all", "category": "build", "mutates": True},
    "project.test": {"pcc_key": "test.workspace", "category": "test", "mutates": False},
    "project.validate": {"pcc_key": "validate.source", "category": "validation", "mutates": False},
    "project.quality.full": {"pcc_key": "validation.full-quality-gate", "category": "quality", "mutates": True},
    "project.quality.fast": {"pcc_key": "validation.fast-quality-gate", "category": "quality", "mutates": True},
    "project.run.editor": {"pcc_key": "run.editor", "category": "run", "mutates": False, "interactive": True},
    "project.run.client": {"pcc_key": "run.game", "category": "run", "mutates": False, "interactive": True},
    "project.run.dev": {"pcc_key": "run.development-world", "category": "run", "mutates": False, "interactive": True},
    "project.clean": {"pcc_key": "maintenance.clean", "category": "maintenance", "mutates": True},
    "project.repair": {"pcc_key": "maintenance.repair", "category": "maintenance", "mutates": True},
    "project.doctor": {"pcc_key": "doctor.environment", "category": "diagnostics", "mutates": False},
    "project.assets.refresh": {"pcc_key": "assets.refresh-catalog", "category": "assets", "mutates": True},
    "project.assets.sync": {"pcc_key": "assets.sync-lpc", "category": "assets", "mutates": True},
    "project.update.status": {"pcc_key": "updates.status", "category": "updates", "mutates": False},
    "project.update.apply": {"pcc_key": "updates.apply-pending", "category": "updates", "mutates": True},
    "project.package.patch": {"pcc_key": "package.incremental-patch", "category": "packaging", "mutates": True},
    "project.package.rollup": {"pcc_key": "package.source-rollup", "category": "packaging", "mutates": True},
    "project.package.baseline": {"pcc_key": "package.capture-baseline", "category": "packaging", "mutates": True},
    "project.diagnostics.bundle": {"pcc_key": "diagnostics.create-debug-handoff", "category": "diagnostics", "mutates": True},
    "project.shell": {"pcc_key": "project.shell", "category": "fallback", "mutates": False, "interactive": True},
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def project_root(explicit: str | None = None) -> Path:
    if explicit:
        return Path(explicit).expanduser().resolve()
    return Path(__file__).resolve().parents[2]


def read_json(path: Path) -> dict[str, Any] | None:
    try:
        if not path.is_file():
            return None
        value = json.loads(path.read_text(encoding="utf-8-sig"))
        return value if isinstance(value, dict) else None
    except Exception:
        return None


def run_capture(root: Path, argv: list[str], timeout: int = 12) -> tuple[int, str, str]:
    try:
        cp = subprocess.run(
            argv,
            cwd=str(root),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
        return cp.returncode, cp.stdout.strip(), cp.stderr.strip()
    except (OSError, subprocess.TimeoutExpired) as exc:
        return 127, "", str(exc)


def git_info(root: Path) -> dict[str, Any]:
    git = shutil.which("git")
    if not git:
        return {"available": False, "repository": False, "state": "UNAVAILABLE"}
    code, inside, _ = run_capture(root, [git, "rev-parse", "--is-inside-work-tree"])
    if code != 0 or inside.lower() != "true":
        return {"available": True, "repository": False, "state": "NOT_REPOSITORY"}
    _, head, _ = run_capture(root, [git, "rev-parse", "HEAD"])
    _, branch, _ = run_capture(root, [git, "branch", "--show-current"])
    _, remote, _ = run_capture(root, [git, "remote", "get-url", "origin"])
    _, status, _ = run_capture(root, [git, "status", "--porcelain=v1", "--untracked-files=normal"])
    changed = [line for line in status.splitlines() if line.strip()]
    upstream_code, upstream, _ = run_capture(root, [git, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"])
    ahead = behind = None
    if upstream_code == 0 and upstream:
        count_code, counts, _ = run_capture(root, [git, "rev-list", "--left-right", "--count", f"{upstream}...HEAD"])
        if count_code == 0:
            parts = counts.split()
            if len(parts) == 2:
                try:
                    behind, ahead = int(parts[0]), int(parts[1])
                except ValueError:
                    pass
    return {
        "available": True,
        "repository": True,
        "state": "MODIFIED" if changed else "CLEAN",
        "changed_paths": len(changed),
        "head": head or None,
        "branch": branch or None,
        "origin": remote or None,
        "upstream": upstream if upstream_code == 0 else None,
        "ahead": ahead,
        "behind": behind,
    }


def detect(root: Path) -> dict[str, Any]:
    missing_files = [p for p in REQUIRED_FILES if not (root / p).is_file()]
    missing_dirs = [p for p in REQUIRED_DIRS if not (root / p).is_dir()]
    pcc_available = all((root / p).is_file() for p in (
        "HavenwildTools.cmd",
        "tools/control/HavenwildTools.ps1",
        "tools/control/ProjectCommandRegistry.ps1",
    ))
    matched = len(REQUIRED_FILES) + len(REQUIRED_DIRS) - len(missing_files) - len(missing_dirs)
    total = len(REQUIRED_FILES) + len(REQUIRED_DIRS)
    score = round(matched / total, 3) if total else 0.0
    return {
        "schema": ADAPTER_SCHEMA,
        "adapter_version": ADAPTER_VERSION,
        "project_id": PROJECT_ID,
        "project_name": PROJECT_NAME,
        "root": str(root),
        "detected": not missing_files and not missing_dirs,
        "confidence": score,
        "pcc_available": pcc_available,
        "fallback_cli_enabled": pcc_available,
        "fallback_cli": str(root / "HavenwildTools.cmd") if pcc_available else None,
        "missing_files": missing_files,
        "missing_directories": missing_dirs,
    }


def status(root: Path) -> dict[str, Any]:
    d = detect(root)
    green = read_json(root / ".havenwild" / "last-green-quality-gate.json")
    artifact_index = read_json(root / ".havenwild" / "artifact-index.json")
    last_applied = read_json(root / ".havenwild" / "updates" / "last-applied.json")
    baseline = (root / ".havenwild" / "package-baseline.json").is_file()
    editor_ready = any((root / p).is_file() for p in (
        "target/debug/haven_editor_native.exe", "target/release/haven_editor_native.exe"))
    client_ready = any((root / p).is_file() for p in (
        "target/debug/haven_game.exe", "target/release/haven_game.exe"))
    gate_state = "NONE"
    if green:
        gate_state = "GREEN" if str(green.get("result", "PASS")).upper() == "PASS" else str(green.get("result")).upper()
    return {
        "schema": ADAPTER_SCHEMA,
        "adapter_version": ADAPTER_VERSION,
        "project_id": PROJECT_ID,
        "root": str(root),
        "detected": d["detected"],
        "pcc": {
            "available": d["pcc_available"],
            "fallback_cli_enabled": d["fallback_cli_enabled"],
            "fallback_cli": d["fallback_cli"],
        },
        "build": {"editor_ready": editor_ready, "client_ready": client_ready, "baseline_ready": baseline},
        "quality_gate": {
            "state": gate_state,
            "pass": (green or {}).get("pass"),
            "run_id": (green or {}).get("runId"),
            "created_utc": (green or {}).get("createdUtc"),
            "schema": (green or {}).get("schema"),
            "source_fingerprint": (green or {}).get("sourceFingerprint"),
            "source_path_count": (green or {}).get("sourcePathCount"),
            "published_commit": (green or {}).get("publishedCommit"),
            "clean_checkout_contract": (green or {}).get("cleanCheckoutContract"),
        },
        "last_applied_update": last_applied,
        "git": git_info(root),
        "artifact_index_present": artifact_index is not None,
        "artifact_index": artifact_index,
        "generated_utc": utc_now(),
    }


def describe(root: Path) -> dict[str, Any]:
    return {
        "schema": ADAPTER_SCHEMA,
        "adapter_version": ADAPTER_VERSION,
        "project": {"id": PROJECT_ID, "name": PROJECT_NAME, "root": str(root)},
        "ownership": {
            "forge": ["discovery", "vault-index", "central-artifact-index", "source-control-ui", "run-observability"],
            "havenwild_pcc": ["project-build-semantics", "quality-gates", "project-native-update-apply", "project-specific-tools"],
            "rule": "Do not replace or rewrite Havenwild internal PCC from this adapter.",
        },
        "fallback_cli": {
            "enabled_when_present": True,
            "launcher": "HavenwildTools.cmd",
            "behavior": "Launch existing Havenwild interactive PCC unchanged.",
        },
        "commands": COMMANDS,
        "state": {
            "green_marker": ".havenwild/last-green-quality-gate.json",
            "artifact_index": ".havenwild/artifact-index.json",
            "last_applied_update": ".havenwild/updates/last-applied.json",
        },
        "artifacts": {
            "project_root": "artifacts",
            "packages": ["artifacts/packages"],
            "recovery": ["artifacts/recovery"],
            "debug": ["artifacts/debug-bundles", "artifacts/troubleshooting-bundles"],
            "updates": ["artifacts/updates/applied", "artifacts/updates/failed", "artifacts/updates/undone"],
        },
        "logs": ["logs/sessions", "logs/builds", "logs/validation", "logs/diagnostics", "logs/source-control", "logs/updates", "logs/commands"],
    }


def registry_keys(root: Path) -> set[str]:
    path = root / "tools" / "control" / "ProjectCommandRegistry.ps1"
    if not path.is_file():
        return set()
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    return set(re.findall(r"\bKey\s*=\s*['\"]([^'\"]+)['\"]", text, flags=re.IGNORECASE))


def self_test(root: Path) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    d = detect(root)
    checks.append({"name": "project-detection", "pass": bool(d["detected"]), "detail": d})
    keys = registry_keys(root)
    missing_keys = sorted({str(v["pcc_key"]) for v in COMMANDS.values()} - keys)
    checks.append({"name": "stable-command-keys", "pass": not missing_keys, "missing": missing_keys})
    root_audit = root / "tools" / "control" / "AuditRoot.ps1"
    root_safe = root_audit.is_file() and not (root / "forge.project.toml").exists()
    checks.append({
        "name": "strict-root-preserved",
        "pass": root_safe,
        "detail": "Adapter lives under .forge/; no root forge.project.toml is required.",
    })
    fallback = root / "HavenwildTools.cmd"
    checks.append({"name": "fallback-cli", "pass": fallback.is_file(), "path": str(fallback)})
    ok = all(bool(c.get("pass")) for c in checks)
    return {
        "schema": ADAPTER_SCHEMA,
        "adapter_version": ADAPTER_VERSION,
        "project_id": PROJECT_ID,
        "result": "PASS" if ok else "FAIL",
        "checks": checks,
    }


def pcc_dispatch_argv(root: Path, pcc_key: str) -> list[str]:
    cmd = root / "HavenwildTools.cmd"
    if os.name == "nt" and cmd.is_file():
        return ["cmd.exe", "/d", "/s", "/c", str(cmd), pcc_key]
    ps = shutil.which("pwsh") or shutil.which("powershell")
    ps1 = root / "tools" / "control" / "HavenwildTools.ps1"
    if ps and ps1.is_file():
        return [ps, "-NoProfile", "-File", str(ps1), "-Command", pcc_key]
    raise RuntimeError("Havenwild PCC dispatcher is unavailable on this host.")


def invoke(root: Path, forge_key: str) -> int:
    if forge_key not in COMMANDS:
        raise KeyError(f"Unknown Forge command key: {forge_key}")
    pcc_key = str(COMMANDS[forge_key]["pcc_key"])
    argv = pcc_dispatch_argv(root, pcc_key)
    return subprocess.call(argv, cwd=str(root))


def launch_fallback(root: Path, wait: bool) -> int:
    launcher = root / "HavenwildTools.cmd"
    if not launcher.is_file():
        print("Havenwild CLI fallback is unavailable because HavenwildTools.cmd is missing.", file=sys.stderr)
        return 3
    if os.name == "nt":
        if wait:
            return subprocess.call(["cmd.exe", "/d", "/s", "/c", str(launcher)], cwd=str(root))
        creationflags = getattr(subprocess, "CREATE_NEW_CONSOLE", 0)
        subprocess.Popen(["cmd.exe", "/d", "/s", "/c", str(launcher)], cwd=str(root), creationflags=creationflags)
        return 0
    ps = shutil.which("pwsh") or shutil.which("powershell")
    if not ps:
        print("Havenwild CLI fallback requires Windows PowerShell/pwsh.", file=sys.stderr)
        return 3
    ps1 = root / "tools" / "control" / "HavenwildTools.ps1"
    if wait:
        return subprocess.call([ps, "-NoProfile", "-File", str(ps1)], cwd=str(root))
    subprocess.Popen([ps, "-NoProfile", "-File", str(ps1)], cwd=str(root))
    return 0


def emit(value: Any, as_json: bool) -> None:
    if as_json:
        print(json.dumps(value, indent=2, ensure_ascii=False))
    else:
        if isinstance(value, dict):
            print(json.dumps(value, indent=2, ensure_ascii=False))
        else:
            print(value)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Havenwild Forge/Vault PCC adapter")
    parser.add_argument("--root", help="Havenwild repository root; defaults to adapter-relative root")
    sub = parser.add_subparsers(dest="action", required=True)
    for name in ("describe", "detect", "status", "self-test"):
        p = sub.add_parser(name)
        p.add_argument("--json", action="store_true")
    p_invoke = sub.add_parser("invoke")
    p_invoke.add_argument("forge_key", choices=sorted(COMMANDS))
    p_fallback = sub.add_parser("fallback")
    p_fallback.add_argument("--wait", action="store_true")
    args = parser.parse_args(argv)
    root = project_root(args.root)
    try:
        if args.action == "describe":
            emit(describe(root), args.json); return 0
        if args.action == "detect":
            value = detect(root); emit(value, args.json); return 0 if value["detected"] else 2
        if args.action == "status":
            emit(status(root), args.json); return 0
        if args.action == "self-test":
            value = self_test(root); emit(value, args.json); return 0 if value["result"] == "PASS" else 2
        if args.action == "invoke":
            return invoke(root, args.forge_key)
        if args.action == "fallback":
            return launch_fallback(root, args.wait)
    except Exception as exc:
        print(f"Havenwild Forge adapter error: {exc}", file=sys.stderr)
        return 1
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
