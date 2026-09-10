#!/usr/bin/env python3
"""Recover a protected Havenwild publication after a false-negative whole-worktree check.

This helper is deliberately strict. It succeeds only when:
  * the current governed source still matches the active GREEN marker;
  * every governed path is tracked and has no HEAD/worktree difference; and
  * refs/remotes/origin/main is exactly the local HEAD.

Non-governed working-tree changes are reported but do not invalidate a governed
source publication. The helper updates only the local GREEN publication marker;
it never commits, pushes, resets, deletes, or alters project source.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import HavenwildGateAuthority as authority

BATCH_SIZE = 64


class ReconcileError(RuntimeError):
    pass


def run_git(root: Path, args: list[str], *, check: bool = False, timeout: int = 60):
    cp = subprocess.run(
        ["git", "-C", str(root), *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=timeout,
    )
    out = cp.stdout.decode("utf-8", "replace").strip()
    err = cp.stderr.decode("utf-8", "replace").strip()
    if check and cp.returncode != 0:
        raise ReconcileError(err or f"git {' '.join(args)} exited with {cp.returncode}")
    return cp.returncode, out, err


def normalize_rel(path: str) -> str:
    return path.replace("\\", "/").lstrip("./")


def chunks(items: list[str], size: int = BATCH_SIZE):
    for start in range(0, len(items), size):
        yield items[start : start + size]


def governed_paths_match_head(root: Path, paths: list[str], head: str) -> tuple[bool, str]:
    if not paths:
        return False, "GREEN marker contains no governed paths."

    # Verify the certified files are actually represented by HEAD. A whole-tree
    # cleanliness check is intentionally not used here.
    code, tracked_z, err = run_git(root, ["ls-files", "-z"], timeout=90)
    if code != 0:
        return False, err or "Unable to enumerate tracked files."
    tracked = {
        normalize_rel(item)
        for item in tracked_z.split("\x00")
        if item
    }
    missing = [rel for rel in paths if normalize_rel(rel) not in tracked]
    if missing:
        preview = ", ".join(missing[:5])
        suffix = " ..." if len(missing) > 5 else ""
        return False, f"{len(missing)} governed path(s) are not tracked by HEAD/index: {preview}{suffix}"

    # git diff HEAD compares both index/worktree state against HEAD. Restrict it
    # to governed paths in small batches so Windows command-line limits remain
    # well below the ceiling even with thousands of certified paths.
    for group in chunks(paths):
        code, _, err = run_git(root, ["diff", "--quiet", "--no-ext-diff", head, "--", *group], timeout=90)
        if code == 1:
            return False, "At least one governed path differs from the certified HEAD."
        if code != 0:
            return False, err or "Unable to compare governed paths with HEAD."
    return True, ""


def persist_publication(root: Path, marker: dict, head: str) -> None:
    marker["committedCommit"] = head
    marker["publishedCommit"] = head
    marker["publishedUtc"] = authority.now_utc()
    marker["repositoryPassAtGate"] = str(marker.get("pass") or "").strip() or None
    authority.atomic_json(authority.marker_path(root), marker)
    record_raw = str(marker.get("recordPath") or "").strip()
    if record_raw:
        try:
            authority.atomic_json(Path(record_raw), marker)
        except Exception:
            # The canonical marker is authoritative; an old per-run record path
            # may have been archived or otherwise unavailable.
            pass


def reconcile(root: Path) -> int:
    if not authority.git_ready(root):
        raise ReconcileError("Git is not initialized.")

    marker = authority.load_marker(root)
    ok, snap, reason = authority.certify_matches(root, marker)
    if not ok:
        raise ReconcileError(f"Current governed source is not the certified GREEN snapshot: {reason}")

    marker_paths = [normalize_rel(str(p)) for p in (marker.get("governedPaths") or [])]
    if marker_paths != [normalize_rel(str(p)) for p in snap.get("paths", [])]:
        raise ReconcileError("GREEN marker governed path list differs from the current certified snapshot.")

    # Refresh the remote-tracking ref when possible. Failure is not ignored if
    # the local ref cannot subsequently prove equality.
    run_git(root, ["fetch", "origin", "main"], timeout=90)
    _, head, _ = run_git(root, ["rev-parse", "--verify", "HEAD"], check=True)
    _, remote_head, _ = run_git(root, ["rev-parse", "--verify", "refs/remotes/origin/main"], check=True)
    if not head or remote_head != head:
        raise ReconcileError(
            f"Remote publication is not proven: local HEAD={head or '<none>'}, origin/main={remote_head or '<none>'}."
        )

    matches, mismatch = governed_paths_match_head(root, marker_paths, head)
    if not matches:
        raise ReconcileError(mismatch)

    persist_publication(root, marker, head)
    print(f"RECONCILE PASS: origin/main = HEAD = {head}")
    print(f"GREEN SOURCE VERIFIED: {len(marker_paths)} governed path(s)")
    worktree = authority.worktree_summary(root)
    if worktree != "Clean":
        print(f"WORKTREE NOTE: {worktree}; remaining changes are outside the certified governed path set.")
    print("PUBLICATION RECONCILED: non-governed worktree state did not invalidate certified source publication")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Reconcile a pushed Havenwild GREEN commit using governed-source scope.")
    ap.add_argument("--root", required=True)
    args = ap.parse_args()
    try:
        return reconcile(Path(args.root).resolve())
    except (ReconcileError, authority.AuthorityError) as exc:
        print(f"RECONCILE BLOCKED: {exc}", file=sys.stderr)
        return 1
    except subprocess.TimeoutExpired as exc:
        print(f"RECONCILE BLOCKED: git timed out: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"RECONCILE BLOCKED: unexpected error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
