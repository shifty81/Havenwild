#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

DEFAULT_REMOTE = "https://github.com/shifty81/Havenwild.git"


class RepairError(RuntimeError):
    pass


def run(cmd: list[str], *, cwd: Path | None = None, check: bool = True, timeout: int = 120) -> subprocess.CompletedProcess[str]:
    cp = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=timeout,
        check=False,
    )
    if check and cp.returncode != 0:
        detail = (cp.stderr or cp.stdout).strip()
        raise RepairError(detail or f"Command failed ({cp.returncode}): {' '.join(cmd)}")
    return cp


def git(root: Path, *args: str, check: bool = True, timeout: int = 120) -> subprocess.CompletedProcess[str]:
    return run(["git", "-C", str(root), *args], check=check, timeout=timeout)


def git_text(root: Path, *args: str) -> str:
    cp = git(root, *args, check=False)
    return cp.stdout.strip() if cp.returncode == 0 else ""


def git_repo(root: Path) -> bool:
    return git_text(root, "rev-parse", "--is-inside-work-tree").lower() == "true"


def has_commit(root: Path) -> bool:
    return git(root, "rev-parse", "--verify", "HEAD", check=False).returncode == 0


def is_ancestor(root: Path, older: str, newer: str) -> bool:
    return git(root, "merge-base", "--is-ancestor", older, newer, check=False).returncode == 0


def load_authority(root: Path):
    authority_path = root / "tools" / "control" / "HavenwildGateAuthority.py"
    if not authority_path.is_file():
        raise RepairError(f"Canonical source authority is missing: {authority_path}")
    spec = importlib.util.spec_from_file_location("havenwild_gate_authority", authority_path)
    if spec is None or spec.loader is None:
        raise RepairError("Unable to load Havenwild source authority")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def safe_backup_name(root: Path) -> str:
    base = "havenwild-local-history-backup-" + datetime.now().strftime("%Y%m%d-%H%M%S")
    name = base
    index = 2
    existing = set(git_text(root, "branch", "--format=%(refname:short)").splitlines())
    while name in existing:
        name = f"{base}-{index}"
        index += 1
    return name


def ensure_origin(root: Path, remote: str) -> None:
    current = git_text(root, "remote", "get-url", "origin")
    if current:
        if current != remote:
            git(root, "remote", "set-url", "origin", remote)
            print(f"Origin updated: {remote}")
    else:
        git(root, "remote", "add", "origin", remote)
        print(f"Origin added: {remote}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Safely attach or repair a Havenwild working folder against origin/main without overwriting working files.")
    ap.add_argument("--root", required=True)
    ap.add_argument("--remote", default=DEFAULT_REMOTE)
    args = ap.parse_args()

    root = Path(args.root).resolve()
    remote = (args.remote or DEFAULT_REMOTE).strip() or DEFAULT_REMOTE
    if not root.is_dir():
        raise RepairError(f"Project root does not exist: {root}")
    if shutil.which("git") is None:
        raise RepairError("Git was not found on PATH")

    authority = load_authority(root)
    before = authority.snapshot(root)
    marker = None
    green_ok = False
    green_reason = "No GREEN marker"
    try:
        marker = authority.load_marker(root)
        green_ok, _, green_reason = authority.certify_matches(root, marker)
    except Exception as exc:  # local state can still be attached, but divergence adoption requires GREEN proof
        green_reason = str(exc)

    print("HAVENWILD GIT WORKING-FOLDER REPAIR")
    print(f" Project     : {root}")
    print(f" Remote      : {remote}")
    print(f" Green source: {'MATCH' if green_ok else 'NOT CERTIFIED'}")

    if not git_repo(root):
        run(["git", "init", "-b", "main", str(root)], timeout=30)
        print("Git repository initialized.")

    branch = git_text(root, "symbolic-ref", "--quiet", "--short", "HEAD")
    if branch and branch != "main":
        git(root, "branch", "-M", "main")
        print(f"Local branch renamed: {branch} -> main")

    ensure_origin(root, remote)
    git(root, "fetch", "origin", "main", timeout=180)
    if git(root, "rev-parse", "--verify", "origin/main", check=False).returncode != 0:
        raise RepairError("origin/main could not be resolved after fetch")

    remote_head = git_text(root, "rev-parse", "origin/main")
    local_head = git_text(root, "rev-parse", "--verify", "HEAD") if has_commit(root) else ""

    action = "none"
    backup = ""
    if not local_head:
        action = "adopt-remote"
    elif local_head == remote_head:
        action = "already-aligned"
    elif is_ancestor(root, local_head, remote_head):
        action = "fast-forward-adopt"
    elif is_ancestor(root, remote_head, local_head):
        action = "keep-local-ahead"
    else:
        action = "divergent-adopt"

    print(f" Local HEAD  : {local_head or '<unborn>'}")
    print(f" origin/main : {remote_head}")
    print(f" Relationship: {action}")

    if action in {"adopt-remote", "fast-forward-adopt", "divergent-adopt"}:
        if action == "divergent-adopt":
            if not green_ok:
                raise RepairError(
                    "Local and remote histories diverge, and the working source is not certified by the current GREEN marker. "
                    f"Refusing automatic history adoption. GREEN detail: {green_reason}"
                )
            backup = safe_backup_name(root)
            git(root, "branch", backup, local_head)
            print(f"Backup branch created: {backup}")

        # Mixed reset is deliberate: history/index are attached to origin/main while
        # every working-tree file remains exactly as it was before this operation.
        git(root, "reset", "--mixed", "origin/main", timeout=120)
        print("Local main adopted origin/main history without overwriting working files.")

    # For the local-ahead case, preserve local commits and simply attach upstream.
    git(root, "branch", "--set-upstream-to=origin/main", "main")

    after = authority.snapshot(root)
    if before["fingerprint"] != after["fingerprint"] or before["pathCount"] != after["pathCount"]:
        raise RepairError("Governed working-source bytes changed during Git repair; operation must be inspected before continuing")

    if marker is not None:
        ok_after, _, reason_after = authority.certify_matches(root, marker)
        if green_ok and not ok_after:
            raise RepairError(f"GREEN source certification changed during Git repair: {reason_after}")

    print("WORKING SOURCE PRESERVATION: PASS")
    print(f" Governed paths: {after['pathCount']}")
    print(f" Fingerprint   : {after['fingerprint']}")
    if backup:
        print(f" Recovery ref  : {backup}")
    status = git(root, "status", "--short", "--branch", check=False).stdout.strip()
    print("\nGit status after repair:")
    print(status or "## main...origin/main")
    print("\nREPAIR PASS: origin/main history is attached and the working source was preserved.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RepairError as exc:
        print(f"FAIL: {exc}")
        raise SystemExit(1)
    except subprocess.TimeoutExpired as exc:
        print(f"FAIL: command timed out: {exc}")
        raise SystemExit(1)
