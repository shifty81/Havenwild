#!/usr/bin/env python3
"""Reconcile a certified Havenwild GREEN publication on a non-main development lane."""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import HavenwildGateAuthority as authority
import ReconcilePublishedGreen as legacy_reconcile


class LaneReconcileError(RuntimeError):
    pass


def reconcile(root: Path, branch: str) -> int:
    branch = (branch or "").strip()
    if branch != "experimental":
        raise LaneReconcileError(f"Unsupported governed development lane: {branch!r}")
    if not authority.git_ready(root):
        raise LaneReconcileError("Git is not initialized.")

    active = authority.git_text(root, ["symbolic-ref", "--quiet", "--short", "HEAD"])
    if active != branch:
        raise LaneReconcileError(f"Active branch is {active or '<detached>'}; expected {branch}.")

    marker = authority.load_marker(root)
    if str(marker.get("gitBranchAtGate") or "") != branch:
        raise LaneReconcileError(
            f"GREEN gate belongs to {marker.get('gitBranchAtGate') or '<unknown>'}, not {branch}."
        )
    ok, snap, reason = authority.certify_matches(root, marker)
    if not ok:
        raise LaneReconcileError(f"Current governed source is not the certified GREEN snapshot: {reason}")

    marker_paths = [legacy_reconcile.normalize_rel(str(p)) for p in (marker.get("governedPaths") or [])]
    current_paths = [legacy_reconcile.normalize_rel(str(p)) for p in snap.get("paths", [])]
    if marker_paths != current_paths:
        raise LaneReconcileError("GREEN marker governed path list differs from the current certified snapshot.")

    authority.run_git(root, ["fetch", "origin", branch], timeout=90)
    head = authority.git_text(root, ["rev-parse", "--verify", "HEAD"])
    remote_ref = f"refs/remotes/origin/{branch}"
    remote_head = authority.git_text(root, ["rev-parse", "--verify", remote_ref])
    if not head or remote_head != head:
        raise LaneReconcileError(
            f"Remote publication is not proven: local HEAD={head or '<none>'}, origin/{branch}={remote_head or '<none>'}."
        )

    matches, mismatch = legacy_reconcile.governed_paths_match_head(root, marker_paths, head)
    if not matches:
        raise LaneReconcileError(mismatch)

    marker["committedCommit"] = head
    marker["publishedCommit"] = head
    marker["publishedBranch"] = branch
    marker["publishedUtc"] = authority.now_utc()
    marker["repositoryPassAtGate"] = str(marker.get("pass") or "").strip() or None
    authority.atomic_json(authority.marker_path(root), marker)
    record_raw = str(marker.get("recordPath") or "").strip()
    if record_raw:
        try:
            authority.atomic_json(Path(record_raw), marker)
        except Exception:
            pass

    print(f"RECONCILE PASS: origin/{branch} = HEAD = {head}")
    print(f"GREEN SOURCE VERIFIED: {len(marker_paths)} governed path(s)")
    worktree = authority.worktree_summary(root)
    if worktree != "Clean":
        print(f"WORKTREE NOTE: {worktree}; remaining changes are outside the certified governed path set.")
    print(f"PUBLICATION RECONCILED: certified {branch} source is published without moving main")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Reconcile a pushed Havenwild GREEN development-lane commit.")
    ap.add_argument("--root", required=True)
    ap.add_argument("--branch", required=True)
    args = ap.parse_args()
    try:
        return reconcile(Path(args.root).resolve(), args.branch)
    except (LaneReconcileError, authority.AuthorityError) as exc:
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
