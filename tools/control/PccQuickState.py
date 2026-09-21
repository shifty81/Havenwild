#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, os, re, subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# The quick receipt protects governed source, not the Git index's representation
# of generated Cargo/Python artifacts. The full authority rehashes the complete
# governed tree before it stages or commits anything.
GENERATED_PREFIXES = (
    ".forgepy/state/", ".forgepy/cache/", ".forgepy/build/", ".forgepy/artifacts/",
    "experiments/haven_bevy_candidate/evidence/",
)
GENERATED_DIRS = frozenset({"target", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"})


def generated_path(path: str) -> bool:
    rel = path.replace("\\", "/").lower().lstrip("/")
    return any(rel.startswith(prefix) for prefix in GENERATED_PREFIXES) or any(
        segment in GENERATED_DIRS for segment in rel.split("/")
    )


def run_git(root: Path, *args: str, binary: bool = False) -> tuple[int, bytes | str]:
    try:
        p = subprocess.run(
            ["git", "-C", str(root), *args],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=5,
            text=not binary,
        )
    except Exception:
        return 1, b"" if binary else ""
    return p.returncode, p.stdout


def git(root: Path, *args: str) -> str:
    code, out = run_git(root, *args)
    return str(out).strip() if code == 0 else ""


def read_json(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return None


def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + f".tmp-{os.getpid()}")
    temp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temp.replace(path)


def changed_paths(root: Path) -> list[str]:
    paths: set[str] = set()
    for args in (
        ("diff", "--name-only", "-z"),
        ("diff", "--cached", "--name-only", "-z"),
        ("ls-files", "--others", "--exclude-standard", "-z"),
    ):
        code, raw = run_git(root, *args, binary=True)
        if code != 0:
            continue
        assert isinstance(raw, bytes)
        for item in raw.split(b"\0"):
            if item:
                paths.add(item.decode("utf-8", "surrogateescape").replace("\\", "/"))
    return sorted(p for p in paths if not generated_path(p))


def worktree_fingerprint(root: Path) -> tuple[str, list[str], str]:
    # Hash WORKING SOURCE content and path identity, not Git porcelain or the
    # staging layout. Unstaging a generated build after GREEN cannot change art,
    # game code or the full PCC source fingerprint and must not create fake stale.
    # Git failures must fail closed, never silently produce an empty hash.
    for args in (("diff", "--name-only", "-z"),
                 ("diff", "--cached", "--name-only", "-z"),
                 ("ls-files", "--others", "--exclude-standard", "-z")):
        code, _ = run_git(root, *args, binary=True)
        if code != 0:
            return "", [], "Unavailable"
    paths = changed_paths(root)
    h = hashlib.sha256()
    head = git(root, "rev-parse", "--verify", "HEAD")
    if not head:
        return "", [], "Unavailable"
    h.update(b"HEAD\0" + head.encode("ascii", "replace") + b"\0")
    for rel in paths:
        h.update(rel.encode("utf-8", "surrogateescape")); h.update(b"\0")
        path = root / Path(rel)
        if path.is_file():
            h.update(hashlib.sha256(path.read_bytes()).digest())
        elif path.is_symlink():
            h.update(b"<symlink>")
        else:
            h.update(b"<missing>")
    git_state = "Clean" if not paths else f"Modified ({len(paths)} source path(s))"
    return h.hexdigest(), paths, git_state


def receipt_path(root: Path) -> Path:
    return root / ".havenwild" / "pcc" / "quick-certification.json"


def record_certification(root: Path) -> dict[str, Any]:
    marker = read_json(root / ".havenwild" / "last-green-quality-gate.json") or {}
    if marker.get("result") != "PASS":
        raise RuntimeError("cannot record PCC quick certification without a PASS canonical gate marker")
    branch = git(root, "symbolic-ref", "--quiet", "--short", "HEAD") or "<detached>"
    head = git(root, "rev-parse", "--verify", "HEAD") or None
    fingerprint, paths, git_state = worktree_fingerprint(root)
    if not fingerprint:
        raise RuntimeError("cannot certify quick state: Git/source fingerprint unavailable")
    payload = {
        "schema": "havenwild.pcc_quick_certification.v1",
        "createdUtc": datetime.now(timezone.utc).isoformat(),
        "branch": branch,
        "headAtReceipt": head,
        "gateRunId": marker.get("runId"),
        "markerFingerprint": marker.get("sourceFingerprint"),
        "pass": marker.get("pass"),
        "worktreeFingerprint": fingerprint,
        "changedPathCount": len(paths),
        "gitStateAtReceipt": git_state,
        "mode": "changed-path-content-hash-only",
    }
    atomic_json(receipt_path(root), payload)
    return payload


def state(root: Path) -> dict[str, Any]:
    branch = git(root, "symbolic-ref", "--quiet", "--short", "HEAD") or "<detached>"
    head = git(root, "rev-parse", "--verify", "HEAD") or None
    work_fp, changed, git_state = worktree_fingerprint(root)
    lane = "experimental" if branch == "experimental" else ("main" if branch == "main" else "other")
    marker = read_json(root / ".havenwild" / "last-green-quality-gate.json") or {}
    receipt = read_json(receipt_path(root)) or {}
    last_applied = read_json(root / ".havenwild" / "updates" / "last-applied.json") or {}
    local_patch = str(last_applied.get("pass") or marker.get("pass") or "<unknown>")
    marker_branch = str(marker.get("gitBranchAtGate") or "")
    marker_result = str(marker.get("result") or "")
    published = str(marker.get("publishedCommit") or "") or None
    committed = str(marker.get("committedCommit") or "") or None

    receipt_matches = bool(
        marker_result == "PASS"
        and receipt.get("schema") == "havenwild.pcc_quick_certification.v1"
        and str(receipt.get("branch") or "") == branch
        and bool(work_fp)
        and str(receipt.get("gateRunId") or "") == str(marker.get("runId") or "")
        and str(receipt.get("markerFingerprint") or "") == str(marker.get("sourceFingerprint") or "")
        and str(receipt.get("headAtReceipt") or "") == str(head or "")
        and str(receipt.get("worktreeFingerprint") or "") == work_fp
    )

    gate_state = "NONE"
    if marker_result == "PASS":
        if marker_branch and marker_branch != branch:
            gate_state = "OTHER_LANE"
        elif head and (published == head or committed == head) and git_state == "Clean":
            gate_state = "GREEN"
        elif receipt_matches:
            gate_state = "GREEN"
        else:
            gate_state = "STALE"

    repository_patch = None
    if head and (published == head or committed == head):
        repository_patch = str(marker.get("pass") or "") or None
    if not repository_patch and head:
        subject = git(root, "show", "-s", "--format=%s", head)
        m = re.search(r"Havenwild\s+([A-Za-z0-9_.-]+)\s+(?:—|-)\s+certified GREEN", subject, re.I)
        repository_patch = m.group(1) if m else f"commit {head[:8]}"

    remote_ref = f"refs/remotes/origin/{branch}" if branch not in ("", "<detached>") else ""
    remote_head = git(root, "rev-parse", remote_ref) if remote_ref else ""
    sync = "NO_CERTIFICATION"
    if head:
        if git_state != "Clean":
            sync = "LOCAL_AHEAD_GREEN_UNPUBLISHED" if gate_state == "GREEN" else "LOCAL_MODIFIED_GATE_STALE"
        elif remote_head and remote_head == head:
            sync = "MATCH" if published == head else ("REMOTE_HEAD_MATCH_GREEN_UNRECONCILED" if gate_state == "GREEN" else "REMOTE_HEAD_MATCH_UNCERTIFIED")
        elif remote_head:
            sync = "LOCAL_AHEAD_GREEN_UNPUBLISHED" if gate_state == "GREEN" else "REPOSITORY_MISMATCH"
        else:
            sync = "REMOTE_UNKNOWN"

    return {
        "schema": "havenwild.pcc_quick_state.v1",
        "repository": str(root), "branch": branch, "lane": lane,
        "head": head, "remoteHead": remote_head or None, "gitState": git_state, "gateState": gate_state,
        "localPatch": local_patch, "repositoryPatch": repository_patch, "syncState": sync,
        "publicationEligible": gate_state == "GREEN",
        "changedPathCount": len(changed),
        "quickCertificationReceipt": receipt_matches,
        "mode": "quick-changed-path-hash-no-governed-tree-scan",
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--pretty", action="store_true")
    ap.add_argument("--record-certification", action="store_true")
    ns = ap.parse_args()
    root = Path(ns.root).resolve()
    try:
        payload = record_certification(root) if ns.record_certification else state(root)
    except Exception as exc:
        print(f"PCC quick state error: {exc}", file=os.sys.stderr)
        return 2
    print(json.dumps(payload, indent=2 if ns.pretty else None, sort_keys=ns.pretty))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
