#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import webbrowser
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = "havenwild.green_quality_gate.v3"
DEFAULT_PASS = "CC8E9"
DEFAULT_REMOTE = "https://github.com/shifty81/Havenwild.git"
IGNORED_PREFIXES = (
    "logs/",
    "artifacts/",
    ".havenwild/",
    "target/",
    "build/",
    ".local/",
    "workspace/generated/",
    "workspace/cache/",
    "workspace/tmp/",
)

class AuthorityError(RuntimeError):
    pass


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def atomic_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def run_git(root: Path, args: list[str], *, check: bool = True, timeout: int = 15, binary: bool = False):
    cmd = ["git", "-C", str(root), *args]
    try:
        cp = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout, check=False)
    except subprocess.TimeoutExpired as exc:
        raise AuthorityError(f"Git timed out after {timeout}s: {' '.join(args)}") from exc
    if check and cp.returncode != 0:
        err = cp.stderr.decode("utf-8", "replace").strip()
        raise AuthorityError(err or f"Git exited with code {cp.returncode}: {' '.join(args)}")
    if binary:
        return cp.returncode, cp.stdout, cp.stderr
    return cp.returncode, cp.stdout.decode("utf-8", "replace").strip(), cp.stderr.decode("utf-8", "replace").strip()


def git_ready(root: Path) -> bool:
    try:
        code, out, _ = run_git(root, ["rev-parse", "--is-inside-work-tree"], check=False)
        return code == 0 and out.strip().lower() == "true"
    except Exception:
        return False


def normalize_rel(path: str) -> str:
    p = path.replace("\\", "/")
    while p.startswith("./"):
        p = p[2:]
    return p.lstrip("/")


def ignored(rel: str) -> bool:
    p = normalize_rel(rel).lower()
    return any(p.startswith(prefix) for prefix in IGNORED_PREFIXES)


def governed_paths(root: Path) -> list[str]:
    if git_ready(root):
        _, raw, _ = run_git(root, ["ls-files", "-z", "--cached", "--others", "--exclude-standard"], binary=True)
        paths = []
        for part in raw.split(b"\0"):
            if not part:
                continue
            rel = normalize_rel(part.decode("utf-8", "surrogateescape"))
            if rel and not ignored(rel):
                paths.append(rel)
        return sorted(set(paths), key=lambda s: (s.lower(), s))

    paths: list[str] = []
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        rel = normalize_rel(str(p.relative_to(root)))
        if rel.startswith(".git/") or ignored(rel):
            continue
        paths.append(rel)
    return sorted(set(paths), key=lambda s: (s.lower(), s))


def file_digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def snapshot(root: Path) -> dict:
    paths = governed_paths(root)
    h = hashlib.sha256()
    missing: list[str] = []
    for rel in paths:
        p = root / Path(rel)
        if p.is_file():
            digest = file_digest(p)
            state = "FILE"
        else:
            digest = "-"
            state = "MISSING"
            missing.append(rel)
        h.update(rel.encode("utf-8", "surrogateescape"))
        h.update(b"\0")
        h.update(state.encode("ascii"))
        h.update(b"\0")
        h.update(digest.encode("ascii"))
        h.update(b"\n")
    return {"fingerprint": h.hexdigest(), "pathCount": len(paths), "paths": paths, "missingTrackedPaths": missing}


def git_text(root: Path, args: list[str]) -> str:
    if not git_ready(root):
        return ""
    code, out, _ = run_git(root, args, check=False)
    return out.strip() if code == 0 else ""


def current_source_pass(root: Path) -> str:
    candidates = [root / ".havenwild" / "updates" / "last-applied.json", root / ".havenwild" / "last-applied.json"]
    for p in candidates:
        if not p.exists():
            continue
        try:
            data = json.loads(p.read_text(encoding="utf-8-sig"))
            value = str(data.get("pass") or "").strip()
            if value:
                return value
        except Exception:
            pass
    return DEFAULT_PASS


def parse_run_id(session_log: Path) -> str:
    try:
        text = session_log.read_text(encoding="utf-8-sig", errors="replace")
    except OSError:
        text = ""
    matches = re.findall(r"QG-\d{8}-\d{6}-[A-Za-z0-9]+", text)
    if matches:
        return matches[-1]
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    salt = hashlib.sha256(str(session_log).encode("utf-8", "surrogateescape")).hexdigest()[:8]
    return f"QG-{stamp}-{salt}"


def marker_path(root: Path) -> Path:
    return root / ".havenwild" / "last-green-quality-gate.json"


def load_marker(root: Path) -> dict:
    path = marker_path(root)
    if not path.exists():
        raise AuthorityError("No canonical GREEN Full Quality Gate exists. Run Full Quality Gate first.")
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        raise AuthorityError(f"Canonical GREEN marker is unreadable: {path}") from exc
    if data.get("schema") != SCHEMA or data.get("result") != "PASS":
        raise AuthorityError("The existing GREEN marker uses a retired schema. Run Full Quality Gate once to replace it with canonical v3.")
    return data


def certify_matches(root: Path, marker: dict) -> tuple[bool, dict, str]:
    current = snapshot(root)
    expected = str(marker.get("sourceFingerprint") or "")
    if not expected:
        return False, current, "GREEN record has no governed-source fingerprint."
    if current["fingerprint"] != expected:
        return False, current, "Governed source changed after the last GREEN Full Quality Gate."
    if int(marker.get("sourcePathCount") or -1) != current["pathCount"]:
        return False, current, "Governed source path set changed after the last GREEN Full Quality Gate."
    return True, current, ""


def finalize(root: Path, session_log: Path) -> int:
    if not session_log.exists():
        raise AuthorityError(f"Full Quality Gate session log is missing: {session_log}")
    text = session_log.read_text(encoding="utf-8-sig", errors="replace")
    pass_i = text.rfind("PASS sequence Full quality gate")
    fail_i = text.rfind("FAIL sequence Full quality gate")
    if pass_i < 0 or pass_i < fail_i:
        raise AuthorityError("Canonical GREEN finalization requires PASS sequence Full quality gate in the active session log.")

    snap = snapshot(root)
    run_id = parse_run_id(session_log)
    source_pass = current_source_pass(root)
    git_is_ready = git_ready(root)
    head = git_text(root, ["rev-parse", "--verify", "HEAD"])
    branch = git_text(root, ["symbolic-ref", "--quiet", "--short", "HEAD"])
    remote = git_text(root, ["remote", "get-url", "origin"])
    upstream = git_text(root, ["rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"])

    record_path = root / ".havenwild" / "quality-gates" / f"{run_id}.json"
    record = {
        "schema": SCHEMA,
        "createdUtc": now_utc(),
        "result": "PASS",
        "pass": source_pass,
        "runId": run_id,
        "sessionLog": str(session_log),
        "sourceFingerprint": snap["fingerprint"],
        "sourcePathCount": snap["pathCount"],
        "governedPaths": snap["paths"],
        "gitReady": git_is_ready,
        "gitHeadAtGate": head or None,
        "gitBranchAtGate": branch or None,
        "gitRemoteAtGate": remote or None,
        "gitUpstreamAtGate": upstream or None,
        "publishedCommit": None,
        "recordPath": str(record_path),
    }
    atomic_json(record_path, record)
    atomic_json(marker_path(root), record)

    print(f"GREEN GATE MARKER: {marker_path(root)}")
    print(f"QUALITY GATE RECORD: {record_path}")
    print(f"GREEN SOURCE SNAPSHOT: {snap['pathCount']} governed path(s); {snap['fingerprint']}")
    print(f"GREEN PASS: {source_pass}")
    if git_is_ready:
        print("SOURCE CONTROL: canonical GREEN snapshot is ready for protected commit/push.")
    else:
        print("SOURCE CONTROL: Git is not initialized; GREEN certification remains valid and Git is optional.")
    return 0


def worktree_summary(root: Path) -> str:
    if not git_ready(root):
        return "Not a repository"
    code, out, _ = run_git(root, ["status", "--porcelain=v1", "--untracked-files=normal"], check=False)
    if code != 0:
        return "Unavailable"
    rows = [x for x in out.splitlines() if x.strip()]
    return "Clean" if not rows else f"Modified ({len(rows)} path(s))"


def status(root: Path) -> int:
    print("CANONICAL HAVENWILD GIT STATUS")
    print(f" Repository : {root}")
    if not git_ready(root):
        print(" Git        : not initialized")
        try:
            marker = load_marker(root)
            ok, snap, reason = certify_matches(root, marker)
            print(f" Green gate : {marker.get('pass')} / {marker.get('runId')}")
            print(f" Snapshot   : {'MATCH' if ok else 'CHANGED'} ({snap['pathCount']} path(s))")
            if not ok:
                print(f" Publication: BLOCKED - {reason}")
                return 1
            print(" Publication: GREEN source certified; initialize Git before publishing.")
            return 0
        except Exception as exc:
            print(f" Publication: BLOCKED - {exc}")
            return 1

    head = git_text(root, ["rev-parse", "--verify", "HEAD"]) or "<unborn: no first commit>"
    branch = git_text(root, ["symbolic-ref", "--quiet", "--short", "HEAD"]) or "<detached-or-unknown>"
    remote = git_text(root, ["remote", "get-url", "origin"]) or "<not set>"
    upstream = git_text(root, ["rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"]) or "<not set>"
    print(f" Branch     : {branch}")
    print(f" HEAD       : {head}")
    print(f" Remote     : {remote}")
    print(f" Upstream   : {upstream}")
    print(f" Work tree  : {worktree_summary(root)}")
    try:
        marker = load_marker(root)
        ok, snap, reason = certify_matches(root, marker)
        print(f" Green gate : {marker.get('pass')} / {marker.get('runId')}")
        print(f" Fingerprint: {str(marker.get('sourceFingerprint') or '')[:16]}...")
        if not ok:
            print(f" Publication: BLOCKED - {reason}")
            return 1
        print(f" Publication: ELIGIBLE ({snap['pathCount']} governed path(s))")
        return 0
    except Exception as exc:
        print(f" Publication: BLOCKED - {exc}")
        return 1


def ensure_repo(root: Path, remote: str | None) -> int:
    if not git_ready(root):
        subprocess.run(["git", "init", "-b", "main", str(root)], check=True)
    branch = git_text(root, ["symbolic-ref", "--quiet", "--short", "HEAD"])
    if branch and branch != "main":
        run_git(root, ["branch", "-M", "main"])
    target = (remote or "").strip() or git_text(root, ["remote", "get-url", "origin"]) or DEFAULT_REMOTE
    current = git_text(root, ["remote", "get-url", "origin"])
    if current:
        if current != target:
            run_git(root, ["remote", "set-url", "origin", target])
    else:
        run_git(root, ["remote", "add", "origin", target])
    run_git(root, ["fetch", "origin"], check=False, timeout=30)
    print(f"SETUP PASS: main -> origin {target}")
    return 0


def review(root: Path) -> int:
    if not git_ready(root):
        raise AuthorityError("Git is not initialized. Use Initialize / connect first.")
    _, status_text, _ = run_git(root, ["status", "--short", "--branch"], check=False)
    print("GITHUB-CORE REVIEW")
    print(status_text or "Working tree clean.")
    _, stat, _ = run_git(root, ["diff", "--stat"], check=False)
    if stat:
        print("\nTracked diff summary:")
        print(stat)
    return 0


def stage_certified(root: Path, marker: dict) -> dict:
    ok, snap, reason = certify_matches(root, marker)
    if not ok:
        raise AuthorityError(reason + " Rerun Full Quality Gate before protected publication.")
    paths = list(marker.get("governedPaths") or [])
    if sorted(paths, key=lambda s: (s.lower(), s)) != snap["paths"]:
        raise AuthorityError("Canonical GREEN path manifest does not match the current governed path set.")
    if not paths:
        raise AuthorityError("Canonical GREEN snapshot contains no governed source paths.")

    fd, name = tempfile.mkstemp(prefix="havenwild-green-paths-", suffix=".nul")
    try:
        with os.fdopen(fd, "wb") as f:
            for rel in paths:
                f.write(rel.encode("utf-8", "surrogateescape") + b"\0")
        run_git(root, ["add", "-A", f"--pathspec-from-file={name}", "--pathspec-file-nul"], timeout=30)
    finally:
        try:
            os.remove(name)
        except OSError:
            pass

    ok2, snap2, reason2 = certify_matches(root, marker)
    if not ok2:
        run_git(root, ["reset"], check=False)
        raise AuthorityError(reason2)
    return snap2


def commit_green(root: Path, message: str | None) -> str:
    if not git_ready(root):
        raise AuthorityError("Git is not initialized. Use Initialize / connect first.")
    marker = load_marker(root)
    snap = stage_certified(root, marker)
    staged_code, staged, _ = run_git(root, ["diff", "--cached", "--name-only"], check=False)
    if staged_code != 0:
        raise AuthorityError("Unable to inspect staged GREEN source.")
    if not staged.strip():
        head = git_text(root, ["rev-parse", "--verify", "HEAD"])
        if not head:
            raise AuthorityError("No staged GREEN changes exist and the repository has no commit to publish.")
        print(f"COMMIT PASS: no source changes to commit; HEAD already {head}")
        return head
    msg = (message or "").strip() or f"Havenwild green checkpoint - {marker.get('pass')} - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    run_git(root, ["commit", "-m", msg], timeout=60)
    head = git_text(root, ["rev-parse", "HEAD"])
    if not head:
        raise AuthorityError("Commit completed but HEAD could not be resolved.")
    marker["publishedCommit"] = head
    marker["publishedUtc"] = now_utc()
    marker["sourceFingerprint"] = snap["fingerprint"]
    atomic_json(marker_path(root), marker)
    record_raw = str(marker.get("recordPath") or "").strip()
    if record_raw:
        try:
            atomic_json(Path(record_raw), marker)
        except Exception:
            pass
    print(f"GREEN PUBLICATION CERTIFIED: {snap['pathCount']} governed path(s)")
    print(f"COMMIT PASS: {head}")
    return head


def push_main(root: Path) -> int:
    if not git_ready(root):
        raise AuthorityError("Git is not initialized.")
    remote = git_text(root, ["remote", "get-url", "origin"])
    if not remote:
        raise AuthorityError("origin remote is not configured. Use Initialize / connect first.")
    branch = git_text(root, ["symbolic-ref", "--quiet", "--short", "HEAD"]) or "main"
    if branch != "main":
        raise AuthorityError(f"Protected Havenwild publication requires main; current branch is {branch}.")
    run_git(root, ["push", "-u", "origin", "main"], timeout=120)
    print("PUSH PASS: origin/main")
    return 0


def manual_commit(root: Path, message: str | None) -> int:
    if not git_ready(root):
        raise AuthorityError("Git is not initialized.")
    msg = (message or "").strip()
    if not msg:
        raise AuthorityError("Advanced manual commit requires an explicit commit message.")
    run_git(root, ["add", "-A"], timeout=30)
    _, staged, _ = run_git(root, ["diff", "--cached", "--name-only"], check=False)
    if not staged.strip():
        print("MANUAL COMMIT: nothing to commit.")
        return 0
    run_git(root, ["commit", "-m", msg], timeout=60)
    print(f"MANUAL COMMIT PASS: {git_text(root, ['rev-parse','HEAD'])}")
    return 0


def dispatch_git(root: Path, action: str, message: str | None, remote: str | None) -> int:
    a = (action or "Status").strip().lower().replace("_", "").replace("-", "")
    aliases = {
        "status": "status",
        "setup": "setup", "init": "setup", "initialize": "setup", "connect": "setup",
        "review": "review", "reviewcore": "review", "reviewgithubcore": "review",
        "commitgreen": "commitgreen", "commitpushgreen": "commitpushgreen",
        "push": "push", "pushmain": "push", "pull": "pull",
        "open": "open", "openrepo": "open",
        "commitmanual": "manual", "manualcommit": "manual", "advancedcommit": "manual",
    }
    mode = aliases.get(a)
    if not mode:
        raise AuthorityError(f"Unsupported Git action: {action}")
    if mode == "status":
        return status(root)
    if mode == "setup":
        return ensure_repo(root, remote)
    if mode == "review":
        return review(root)
    if mode == "commitgreen":
        commit_green(root, message)
        return 0
    if mode == "commitpushgreen":
        commit_green(root, message)
        return push_main(root)
    if mode == "push":
        return push_main(root)
    if mode == "pull":
        run_git(root, ["pull", "--ff-only", "origin", "main"], timeout=120)
        print("PULL PASS: origin/main fast-forward only")
        return 0
    if mode == "open":
        target = git_text(root, ["remote", "get-url", "origin"]) or remote or DEFAULT_REMOTE
        if target.endswith(".git"):
            target = target[:-4]
        webbrowser.open(target)
        print(f"OPEN PASS: {target}")
        return 0
    if mode == "manual":
        return manual_commit(root, message)
    raise AuthorityError(f"Unsupported Git action: {action}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Canonical Havenwild GREEN gate + Git publication authority")
    sub = ap.add_subparsers(dest="command", required=True)
    f = sub.add_parser("finalize")
    f.add_argument("--root", required=True)
    f.add_argument("--session-log", required=True)
    g = sub.add_parser("git")
    g.add_argument("--root", required=True)
    g.add_argument("--action", required=True)
    g.add_argument("--message")
    g.add_argument("--remote")
    args = ap.parse_args()
    root = Path(args.root).resolve()
    try:
        if args.command == "finalize":
            return finalize(root, Path(args.session_log).resolve())
        return dispatch_git(root, args.action, args.message, args.remote)
    except AuthorityError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    except subprocess.CalledProcessError as exc:
        print(f"FAIL: command exited with {exc.returncode}", file=sys.stderr)
        return exc.returncode or 1
    except Exception as exc:
        print(f"FAIL: unexpected authority error: {exc}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
