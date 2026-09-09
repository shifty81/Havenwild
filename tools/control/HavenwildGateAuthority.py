#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import webbrowser
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = "havenwild.green_quality_gate.v4"
DEFAULT_PASS = "CC8E17"
DEFAULT_REMOTE = "https://github.com/shifty81/Havenwild.git"
RUNTIME_MEDIA_MANIFEST = "content/runtime_media_manifest_v1.json"

IGNORED_ROOT_PREFIXES = (
    ".git/", ".agents/", ".codex/", ".local/", ".havenwild/",
    "target/", "build/", "logs/", "artifacts/", "assets/", "archive/", "workspace/",
    "content/assets/lpc/source/lpc-terrains-v7/",
    "docs/archive/", "docs/handoffs/", "docs/legacy_project_docs/", "docs/patch/",
    "manifests/packages/", "manifests/patches/", "manifests/rollups/",
    "manifests/handoffs/", "manifests/recovery/",
)

IGNORED_EXTENSIONS = {
    ".pyc", ".pyo", ".tmp", ".temp", ".zip", ".7z", ".rar", ".log",
    ".exe", ".pdb", ".ilk", ".dll",
    ".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tga", ".dds",
    ".wav", ".ogg", ".mp3", ".flac",
    ".glb", ".gltf", ".fbx", ".obj", ".blend",
    ".ttf", ".otf", ".woff", ".woff2",
    ".ase", ".aseprite", ".psd", ".kra", ".gz",
}

ALWAYS_INCLUDE_PREFIXES = (
    "tools/build/",
    "content/build/",
    "docs/readme/",
)

REQUIRED_BOOTSTRAP_PATHS = (
    "Cargo.toml",
    "Cargo.lock",
    "HavenwildTools.cmd",
    ".gitignore",
    ".gitattributes",
    "tools/tool_registry.json",
    "tools/control/HavenwildTools.ps1",
    "tools/control/ProjectCommandRegistry.ps1",
    "tools/control/HavenwildGateAuthority.py",
    "tools/build/Build.cmd",
    "tools/build/Build.sh",
    "content/build/validator_registry_v3.json",
    RUNTIME_MEDIA_MANIFEST,
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


def run_git(root: Path, args: list[str], *, check: bool = True, timeout: int = 20, binary: bool = False):
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


def safe_source_path(path: str) -> str:
    rel = normalize_rel(path)
    if not rel or rel.startswith("/") or ":" in rel:
        raise AuthorityError(f"Unsafe runtime-media path: {path}")
    parts = [p for p in rel.split("/") if p]
    if any(p == ".." for p in parts):
        raise AuthorityError(f"Unsafe runtime-media path: {path}")
    return rel


def file_digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_runtime_media(root: Path) -> list[dict]:
    manifest_path = root / RUNTIME_MEDIA_MANIFEST
    if not manifest_path.is_file():
        raise AuthorityError(f"Required runtime-media manifest is missing: {RUNTIME_MEDIA_MANIFEST}")
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        raise AuthorityError(f"Runtime-media manifest is unreadable: {RUNTIME_MEDIA_MANIFEST}") from exc
    if data.get("schema") != "havenwild.runtime_media_manifest.v1":
        raise AuthorityError(f"Unsupported runtime-media manifest schema: {data.get('schema')}")
    assets = data.get("assets")
    if not isinstance(assets, list):
        raise AuthorityError("Runtime-media manifest must contain an assets array.")
    out: list[dict] = []
    seen: set[str] = set()
    for raw in assets:
        if not isinstance(raw, dict):
            raise AuthorityError("Runtime-media asset entries must be objects.")
        if not bool(raw.get("requiredForCleanCheckout", False)):
            continue
        rel = safe_source_path(str(raw.get("path") or ""))
        key = rel.lower()
        if key in seen:
            raise AuthorityError(f"Duplicate runtime-media path: {rel}")
        seen.add(key)
        sha = str(raw.get("sha256") or "").lower()
        if len(sha) != 64 or any(c not in "0123456789abcdef" for c in sha):
            raise AuthorityError(f"Runtime-media entry has invalid SHA-256: {rel}")
        out.append({"path": rel, "sha256": sha, "id": str(raw.get("id") or rel)})
    if not out:
        raise AuthorityError("Runtime-media manifest contains no required clean-checkout assets.")
    return sorted(out, key=lambda x: x["path"].lower())


def required_runtime_media_paths(root: Path) -> set[str]:
    return {entry["path"].lower() for entry in load_runtime_media(root)}


def always_include(rel: str, required_media: set[str] | None = None) -> bool:
    p = normalize_rel(rel).lower()
    if required_media and p in required_media:
        return True
    return any(p.startswith(prefix) for prefix in ALWAYS_INCLUDE_PREFIXES)


def ignored(rel: str, required_media: set[str] | None = None) -> bool:
    p = normalize_rel(rel)
    pl = p.lower()
    if always_include(pl, required_media):
        return False
    if any(pl.startswith(prefix) for prefix in IGNORED_ROOT_PREFIXES):
        return True
    parts = [part.lower() for part in p.split("/") if part]
    if "__pycache__" in parts:
        return True
    name = Path(p).name.lower()
    if name in {"thumbs.db", ".ds_store"}:
        return True
    if Path(name).suffix.lower() in IGNORED_EXTENSIONS:
        return True
    return False


def governed_paths(root: Path) -> tuple[list[str], list[dict]]:
    media = load_runtime_media(root)
    media_paths = {entry["path"].lower() for entry in media}
    paths: list[str] = []
    for current, dirs, files in os.walk(root):
        current_path = Path(current)
        rel_dir = normalize_rel(str(current_path.relative_to(root))) if current_path != root else ""
        kept_dirs = []
        for d in dirs:
            child = normalize_rel(f"{rel_dir}/{d}" if rel_dir else d) + "/"
            if d.lower() == ".git":
                continue
            if ignored(child, media_paths):
                continue
            kept_dirs.append(d)
        dirs[:] = kept_dirs
        for name in files:
            p = current_path / name
            rel = normalize_rel(str(p.relative_to(root)))
            if ignored(rel, media_paths):
                continue
            paths.append(rel)
    return sorted(set(paths), key=lambda s: (s.lower(), s)), media


def validate_checkout_contract(root: Path, paths: list[str], media: list[dict]) -> None:
    path_set = set(paths)
    missing_disk = [p for p in REQUIRED_BOOTSTRAP_PATHS if not (root / Path(p)).is_file()]
    missing_manifest = [p for p in REQUIRED_BOOTSTRAP_PATHS if p not in path_set]
    media_errors: list[str] = []
    for entry in media:
        rel = entry["path"]
        p = root / Path(rel)
        if not p.is_file():
            media_errors.append(f"missing: {rel}")
            continue
        actual = file_digest(p)
        if actual != entry["sha256"]:
            media_errors.append(f"sha256 mismatch: {rel} expected={entry['sha256']} actual={actual}")
        if rel not in path_set:
            media_errors.append(f"not governed: {rel}")
    if missing_disk or missing_manifest or media_errors:
        lines = ["Clean-checkout source contract failed."]
        if missing_disk:
            lines.append("Required bootstrap file(s) missing from working source:")
            lines.extend(f" - {p}" for p in missing_disk)
        if missing_manifest:
            lines.append("Required bootstrap file(s) absent from governed publication manifest:")
            lines.extend(f" - {p}" for p in missing_manifest)
        if media_errors:
            lines.append("Required runtime-media failure(s):")
            lines.extend(f" - {x}" for x in media_errors)
        raise AuthorityError("\n".join(lines))


def snapshot(root: Path) -> dict:
    paths, media = governed_paths(root)
    validate_checkout_contract(root, paths, media)
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
        h.update(rel.encode("utf-8", "surrogateescape")); h.update(b"\0")
        h.update(state.encode("ascii")); h.update(b"\0")
        h.update(digest.encode("ascii")); h.update(b"\n")
    return {
        "fingerprint": h.hexdigest(),
        "pathCount": len(paths),
        "paths": paths,
        "missingTrackedPaths": missing,
        "requiredBootstrapPaths": list(REQUIRED_BOOTSTRAP_PATHS),
        "requiredRuntimeMedia": media,
        "requiredRuntimeMediaPaths": [entry["path"] for entry in media],
    }


def git_text(root: Path, args: list[str]) -> str:
    if not git_ready(root):
        return ""
    code, out, _ = run_git(root, args, check=False)
    return out.strip() if code == 0 else ""


def current_source_pass(root: Path) -> str:
    for p in (root / ".havenwild" / "updates" / "last-applied.json", root / ".havenwild" / "last-applied.json"):
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
    import re
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
        raise AuthorityError("The existing GREEN marker uses a retired source-distribution schema. Run Full Quality Gate once to establish the current clean-checkout contract.")
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
    if sorted(marker.get("requiredBootstrapPaths") or []) != sorted(REQUIRED_BOOTSTRAP_PATHS):
        return False, current, "GREEN record does not certify the current clean-checkout bootstrap contract."
    if sorted(marker.get("requiredRuntimeMediaPaths") or []) != sorted(current["requiredRuntimeMediaPaths"]):
        return False, current, "GREEN record does not certify the current required runtime-media contract."
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
    head_at_gate = git_text(root, ["rev-parse", "--verify", "HEAD"]) or None
    repository_pass_at_gate = None
    previous_marker = None
    try:
        previous_marker = load_marker(root)
    except Exception:
        previous_marker = None
    if previous_marker and head_at_gate and str(previous_marker.get("publishedCommit") or "") == head_at_gate:
        repository_pass_at_gate = str(previous_marker.get("pass") or "").strip() or None
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
        "requiredBootstrapPaths": list(REQUIRED_BOOTSTRAP_PATHS),
        "requiredRuntimeMedia": snap["requiredRuntimeMedia"],
        "requiredRuntimeMediaPaths": snap["requiredRuntimeMediaPaths"],
        "cleanCheckoutContract": "PASS",
        "gitReady": git_ready(root),
        "gitHeadAtGate": head_at_gate,
        "repositoryPassAtGate": repository_pass_at_gate,
        "gitBranchAtGate": git_text(root, ["symbolic-ref", "--quiet", "--short", "HEAD"]) or None,
        "gitRemoteAtGate": git_text(root, ["remote", "get-url", "origin"]) or None,
        "gitUpstreamAtGate": git_text(root, ["rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"]) or None,
        "publishedCommit": None,
        "recordPath": str(record_path),
    }
    atomic_json(record_path, record)
    atomic_json(marker_path(root), record)
    print(f"GREEN GATE MARKER: {marker_path(root)}")
    print(f"QUALITY GATE RECORD: {record_path}")
    print(f"GREEN SOURCE SNAPSHOT: {snap['pathCount']} governed path(s); {snap['fingerprint']}")
    print(f"GREEN PASS: {source_pass}")
    print(f"CLEAN CHECKOUT CONTRACT: PASS ({len(REQUIRED_BOOTSTRAP_PATHS)} bootstrap authorities; {len(snap['requiredRuntimeMediaPaths'])} required runtime media)")
    if git_ready(root):
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
            print(f" Clean ZIP  : {marker.get('cleanCheckoutContract') or '<not certified>'}")
            if not ok:
                print(f" Publication: BLOCKED - {reason}")
                return 1
            print(" Publication: GREEN source certified; initialize Git before publishing.")
            return 0
        except Exception as exc:
            print(f" Publication: BLOCKED - {exc}")
            return 1
    print(f" Branch     : {git_text(root, ['symbolic-ref','--quiet','--short','HEAD']) or '<detached-or-unknown>'}")
    print(f" HEAD       : {git_text(root, ['rev-parse','--verify','HEAD']) or '<unborn: no first commit>'}")
    print(f" Remote     : {git_text(root, ['remote','get-url','origin']) or '<not set>'}")
    print(f" Upstream   : {git_text(root, ['rev-parse','--abbrev-ref','--symbolic-full-name','@{u}']) or '<not set>'}")
    print(f" Work tree  : {worktree_summary(root)}")
    try:
        marker = load_marker(root)
        ok, snap, reason = certify_matches(root, marker)
        print(f" Green gate : {marker.get('pass')} / {marker.get('runId')}")
        print(f" Fingerprint: {str(marker.get('sourceFingerprint') or '')[:16]}...")
        print(f" Clean ZIP  : {marker.get('cleanCheckoutContract') or '<not certified>'}")
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
        run_git(root, ["add", "-f", "-A", f"--pathspec-from-file={name}", "--pathspec-file-nul"], timeout=90)
    finally:
        try:
            os.remove(name)
        except OSError:
            pass
    required_tracked = list(REQUIRED_BOOTSTRAP_PATHS) + snap["requiredRuntimeMediaPaths"]
    for rel in required_tracked:
        code, _, _ = run_git(root, ["ls-files", "--error-unmatch", "--", rel], check=False)
        if code != 0:
            run_git(root, ["reset"], check=False)
            raise AuthorityError(f"Protected staging omitted clean-checkout authority: {rel}")
    ok2, snap2, reason2 = certify_matches(root, marker)
    if not ok2:
        run_git(root, ["reset"], check=False)
        raise AuthorityError(reason2)
    return snap2


def _persist_marker(root: Path, marker: dict) -> None:
    atomic_json(marker_path(root), marker)
    record_raw = str(marker.get("recordPath") or "").strip()
    if record_raw:
        try:
            atomic_json(Path(record_raw), marker)
        except Exception:
            pass


def _head_matches_certified(root: Path, marker: dict) -> tuple[bool, str | None]:
    """Return whether HEAD contains exactly the currently certified governed source."""
    head = git_text(root, ["rev-parse", "--verify", "HEAD"]) or None
    if not head:
        return False, None
    ok, snap, _ = certify_matches(root, marker)
    if not ok:
        return False, head
    # A clean work tree plus matching governed fingerprint means HEAD is the
    # certified source. Nongoverned local files do not participate in this test.
    if worktree_summary(root) != "Clean":
        return False, head
    return True, head


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
        # Reconciliation path: a previous commit may already contain this exact
        # certified snapshot. Record it as committed, but not yet as published.
        marker["committedCommit"] = head
        marker["committedUtc"] = now_utc()
        marker["sourceFingerprint"] = snap["fingerprint"]
        _persist_marker(root, marker)
        print(f"COMMIT PASS: no source changes to commit; certified HEAD already {head}")
        return head
    msg = (message or "").strip() or f"Havenwild green checkpoint - {marker.get('pass')} - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    run_git(root, ["commit", "-m", msg], timeout=120)
    head = git_text(root, ["rev-parse", "HEAD"])
    if not head:
        raise AuthorityError("Commit completed but HEAD could not be resolved.")
    marker["committedCommit"] = head
    marker["committedUtc"] = now_utc()
    marker["sourceFingerprint"] = snap["fingerprint"]
    _persist_marker(root, marker)
    print(f"GREEN COMMIT CERTIFIED: {snap['pathCount']} governed path(s)")
    print(f"REQUIRED RUNTIME MEDIA TRACKED: {len(snap['requiredRuntimeMediaPaths'])}")
    print(f"CLEAN CHECKOUT CONTRACT: PASS ({len(REQUIRED_BOOTSTRAP_PATHS)} bootstrap authorities tracked)")
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
    run_git(root, ["push", "-u", "origin", "main"], timeout=180)
    # Never infer publication from a successful process exit alone. Refresh the
    # remote-tracking ref and prove origin/main is the exact local HEAD.
    run_git(root, ["fetch", "origin", "main"], timeout=60)
    head = git_text(root, ["rev-parse", "HEAD"])
    remote_head = git_text(root, ["rev-parse", "refs/remotes/origin/main"])
    if not head or remote_head != head:
        raise AuthorityError(f"Push returned successfully but origin/main did not reconcile to local HEAD (local={head or '<none>'}, remote={remote_head or '<none>'}).")
    try:
        marker = load_marker(root)
        matches, certified_head = _head_matches_certified(root, marker)
        if not matches or certified_head != head:
            raise AuthorityError("origin/main matches HEAD, but HEAD no longer matches the certified governed source.")
        marker["committedCommit"] = head
        marker["publishedCommit"] = head
        marker["publishedUtc"] = now_utc()
        marker["repositoryPassAtGate"] = str(marker.get("pass") or "").strip() or None
        _persist_marker(root, marker)
    except AuthorityError:
        raise
    print(f"PUSH PASS: origin/main = {head}")
    print("PUBLICATION RECONCILED: local HEAD, origin/main, and GREEN certification MATCH")
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


def frontdoor_state(root: Path) -> int:
    local_pass = current_source_pass(root)
    payload = {
        "schema": "havenwild.frontdoor_state.v1",
        "localPatch": local_pass,
        "repositoryPatch": None,
        "repositoryCommit": None,
        "gateId": None,
        "gateState": "NONE",
        "syncState": "NO_CERTIFICATION",
        "gitState": worktree_summary(root),
        "publicationEligible": False,
        "governedPathCount": None,
    }
    if git_ready(root):
        head = git_text(root, ["rev-parse", "--verify", "HEAD"]) or None
        payload["repositoryCommit"] = head
    else:
        head = None
    try:
        marker = load_marker(root)
        payload["gateId"] = marker.get("runId")
        ok, snap, reason = certify_matches(root, marker)
        payload["governedPathCount"] = snap.get("pathCount")
        payload["publicationEligible"] = bool(ok)
        payload["gateState"] = "GREEN" if ok else "STALE"
        published = str(marker.get("publishedCommit") or "").strip() or None
        if head and published == head:
            payload["repositoryPatch"] = str(marker.get("pass") or "").strip() or None
        elif head:
            payload["repositoryPatch"] = str(marker.get("repositoryPassAtGate") or "").strip() or None
        if not payload["repositoryPatch"] and head:
            subject = git_text(root, ["show", "-s", "--format=%s", head])
            import re
            m = re.search(r"Havenwild\s+([A-Za-z0-9_.-]+)\s+(?:—|-)\s+certified GREEN", subject, re.I)
            payload["repositoryPatch"] = m.group(1) if m else f"commit {head[:8]}"
        if not ok:
            payload["syncState"] = (
                "FINGERPRINT_MISMATCH_GATE_STALE"
                if payload["gitState"] == "Clean"
                else "LOCAL_MODIFIED_GATE_STALE"
            )
            payload["blockReason"] = reason
        elif not head:
            payload["syncState"] = "GREEN_NOT_PUBLISHED"
        elif published == head and str(marker.get("pass") or "") == local_pass:
            remote_head = git_text(root, ["rev-parse", "refs/remotes/origin/main"]) or None
            payload["syncState"] = "MATCH" if (not remote_head or remote_head == head) else "REPOSITORY_MISMATCH"
        elif published == head:
            payload["syncState"] = "LOCAL_PATCH_AHEAD_UNCERTIFIED"
        else:
            payload["syncState"] = "LOCAL_AHEAD_GREEN_UNPUBLISHED"
    except Exception as exc:
        payload["blockReason"] = str(exc)
    print(json.dumps(payload, separators=(",", ":")))
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
        commit_green(root, message); return 0
    if mode == "commitpushgreen":
        commit_green(root, message); return push_main(root)
    if mode == "push":
        return push_main(root)
    if mode == "pull":
        run_git(root, ["pull", "--ff-only", "origin", "main"], timeout=120)
        print("PULL PASS: origin/main fast-forward only"); return 0
    if mode == "open":
        target = git_text(root, ["remote", "get-url", "origin"]) or remote or DEFAULT_REMOTE
        if target.endswith(".git"):
            target = target[:-4]
        webbrowser.open(target)
        print(f"OPEN PASS: {target}"); return 0
    if mode == "manual":
        return manual_commit(root, message)
    raise AuthorityError(f"Unsupported Git action: {action}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Canonical Havenwild GREEN gate + clean-checkout Git publication authority")
    sub = ap.add_subparsers(dest="command", required=True)
    f = sub.add_parser("finalize")
    f.add_argument("--root", required=True)
    f.add_argument("--session-log", required=True)
    fd = sub.add_parser("frontdoor")
    fd.add_argument("--root", required=True)
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
        if args.command == "frontdoor":
            return frontdoor_state(root)
        return dispatch_git(root, args.action, args.message, args.remote)
    except AuthorityError as exc:
        print(f"FAIL: {exc}", file=sys.stderr); return 1
    except subprocess.CalledProcessError as exc:
        print(f"FAIL: command exited with {exc.returncode}", file=sys.stderr); return exc.returncode or 1
    except Exception as exc:
        print(f"FAIL: unexpected authority error: {exc}", file=sys.stderr); return 1


if __name__ == "__main__":
    raise SystemExit(main())
