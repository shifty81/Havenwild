#!/usr/bin/env python3
from __future__ import annotations

import argparse
import contextlib
import hashlib
import importlib.util
import json
import os
import platform
import queue
import shutil
import shlex
import signal
import socket
import subprocess
import sys
import tempfile
import threading
import time
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Sequence

PRODUCT = "ForgePY Standalone Universal PCC"
VERSION = "1.4.0-hardened"
BUILD = "FORGEPY-STANDALONE-U5-AUTO-ONBOARD"
CONTRACT = "forgepy.universal.v1"
DONOR_BUILD = "FORGEPY-F797"
DONOR_COMMIT = "f00ca0fea2dfa29dc930fcc18ddcedc347a7c6ad"

ALIASES: dict[str, tuple[str, ...]] = {
    "full": ("gate.full", "build.full", "quality.full"),
    "quick": ("gate.fast", "gate.quick", "build.fast", "build.quick"),
    "fast": ("gate.fast", "gate.quick", "build.fast", "build.quick"),
    "build": ("build.default", "build.native", "build.debug", "build"),
    "build-release": ("build.release", "build.default", "build.native", "build"),
    "test": ("test.default", "test", "gate.test"),
    "run": ("run.default", "run.gui", "run.game", "run.client", "run.editor", "run.runtime"),
    "doctor": ("project.health", "project.status"),
    "self-test": ("project.self-test", "control.self-test", "self-test"),
    "debug-bundle": ("diagnostics.bundle",),
    "git-status": ("git.status", "project.status"),
    "git-history": ("git.history",),
    "git-pull": ("git.pull",),
    "push": ("git.push",),
    "commit-green": ("git.commit-green",),
    "patch-status": ("patch.status", "patch.preview"),
    "patch-check": ("patch.preview", "patch.check"),
    "patch-apply": ("patch.apply",),
    "preflight": ("project.preflight", "project.health"),
    "scan": ("project.scan", "project.discover"),
    "rescan": ("project.rescan",),
}

SCAN_SCHEMA = "forgepy.repository.scan.v1"
SCAN_PLAN_SCHEMA = "forgepy.onboarding.plan.v1"
SCAN_SKIP_DIRS = {
    ".git", ".forgepy", ".venv", "venv", "node_modules", "target", "build", "dist", "out",
    "bin", "obj", "__pycache__", ".cache", ".idea", ".vs", "vendor", "third_party", "third-party",
}
SCAN_EXACT_MARKERS = {
    "Cargo.toml", "package.json", "pnpm-lock.yaml", "yarn.lock", "bun.lock", "bun.lockb", "CMakeLists.txt", "pyproject.toml", "requirements.txt", "setup.py", "setup.cfg",
    "tox.ini", "pytest.ini", "Makefile", "makefile", "gradlew", "gradlew.bat", "build.gradle", "build.gradle.kts",
    "pom.xml", "go.mod", "build.zig", "meson.build", "project.godot", "export_presets.cfg",
    "build.cmd", "build.bat", "build.ps1", "build.sh", "test.cmd", "test.bat", "test.ps1", "test.sh",
    "run.cmd", "run.bat", "run.ps1", "run.sh", "configure.cmd", "configure.bat", "configure.ps1", "configure.sh",
    "PROJECT_CONTROL_CENTER.cmd", "main.py", "app.py", "run.py",
}
SCAN_SUFFIX_MARKERS = {".sln", ".slnx", ".csproj", ".fsproj", ".vbproj", ".uproject"}


_OP_EVIDENCE: list[dict[str, Any]] = []
_LOCK_DEPTH: dict[str, int] = {}


def normalize_stdio() -> None:
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def atomic_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")
    fd, tmp_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_name, path)
    finally:
        try:
            os.unlink(tmp_name)
        except FileNotFoundError:
            pass


def read_json(path: Path, default=None):
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return default


def _within(root: Path, path: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def validate_contract(data: dict[str, Any], path: Path) -> dict[str, Any]:
    schema = data.get("schema")
    if schema not in {None, "forge.project.v1"}:
        raise ValueError(f"unsupported contract schema {schema!r}: {path}")
    commands = data.get("commands", [])
    if not isinstance(commands, list):
        raise ValueError(f"commands must be an array: {path}")
    seen_keys: set[str] = set()
    for i, raw in enumerate(commands):
        if not isinstance(raw, dict):
            raise ValueError(f"commands[{i}] must be an object: {path}")
        key = raw.get("key")
        program = raw.get("program")
        if not isinstance(key, str) or not key.strip():
            raise ValueError(f"commands[{i}].key must be a non-empty string: {path}")
        folded = key.strip().casefold()
        if folded in seen_keys:
            raise ValueError(f"duplicate command key {key!r}: {path}")
        seen_keys.add(folded)
        if any(ord(c) < 32 for c in key):
            raise ValueError(f"commands[{i}].key contains control characters: {path}")
        if not isinstance(program, str) or not program.strip():
            raise ValueError(f"commands[{i}].program must be a non-empty string: {path}")
        if "\x00" in program:
            raise ValueError(f"commands[{i}].program contains NUL: {path}")
        pp = Path(program)
        if ("/" in program or "\\" in program) and not pp.is_absolute() and ".." in pp.parts:
            raise ValueError(f"commands[{i}].program may not escape project root via '..': {path}")
        args = raw.get("args", [])
        if not isinstance(args, list) or not all(isinstance(x, (str, int, float)) and "\x00" not in str(x) for x in args):
            raise ValueError(f"commands[{i}].args must be an array of scalar non-NUL values: {path}")
        if "category" in raw and (not isinstance(raw["category"], str) or not raw["category"].strip()):
            raise ValueError(f"commands[{i}].category must be a non-empty string when present: {path}")
        if "risk" in raw and str(raw["risk"]).casefold() not in {"read", "write", "danger"}:
            raise ValueError(f"commands[{i}].risk must be read/write/danger: {path}")
        if "mutates" in raw and not isinstance(raw["mutates"], bool):
            raise ValueError(f"commands[{i}].mutates must be boolean: {path}")
        if "timeoutSeconds" in raw:
            value = raw["timeoutSeconds"]
            if not isinstance(value, (int, float)) or isinstance(value, bool) or value < 0 or value > 86400:
                raise ValueError(f"commands[{i}].timeoutSeconds must be 0..86400: {path}")
        if "cwd" in raw:
            cwd = raw["cwd"]
            if not isinstance(cwd, str) or not cwd.strip():
                raise ValueError(f"commands[{i}].cwd must be a non-empty relative path: {path}")
            cp = Path(cwd)
            if cp.is_absolute() or ".." in cp.parts:
                raise ValueError(f"commands[{i}].cwd must remain within the project root: {path}")
    sd = data.get("stateDirectory", ".forgepy/state")
    if not isinstance(sd, str) or not sd.strip():
        raise ValueError(f"stateDirectory must be a non-empty relative path: {path}")
    state_path = Path(sd)
    if state_path.is_absolute() or ".." in state_path.parts:
        raise ValueError(f"stateDirectory must be a safe relative path: {path}")
    project = data.get("project", {})
    if project is not None and not isinstance(project, dict):
        raise ValueError(f"project must be an object: {path}")
    provider = data.get("provider")
    if provider is not None:
        if not isinstance(provider, dict):
            raise ValueError(f"provider must be an object when present: {path}")
        ptype = str(provider.get("type") or "").strip().casefold()
        if ptype and ptype not in {"internal-pcc", "project-contract", "forgepy-adapter"}:
            raise ValueError(f"provider.type must be internal-pcc/project-contract/forgepy-adapter: {path}")
        if "name" in provider and (not isinstance(provider["name"], str) or not provider["name"].strip()):
            raise ValueError(f"provider.name must be a non-empty string when present: {path}")
    return data

def safe_slug(value: str) -> str:
    out = "".join(c.lower() if c.isalnum() else "-" for c in value.strip())
    while "--" in out:
        out = out.replace("--", "-")
    return out.strip("-") or "project"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()


def sha256_text_lf(path: Path) -> str:
    data = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(data).hexdigest()


def package_hash(path: Path, mode: str) -> str:
    return sha256_text_lf(path) if mode == "text-lf" else sha256_file(path)


def load_policy(root: Path) -> dict[str, Any]:
    defaults: dict[str, Any] = {
        "genericPatchMaxBytes": 128 * 1024 * 1024,
        "operationLockStaleSeconds": 6 * 60 * 60,
        "defaultGateTimeoutSeconds": 60 * 60,
        "defaultBuildTimeoutSeconds": 60 * 60,
        "defaultTestTimeoutSeconds": 60 * 60,
        "defaultRunTimeoutSeconds": 0,
    }
    raw = read_json(root / ".forgepy" / "policy.json", {})
    if isinstance(raw, dict):
        defaults.update(raw)
    return defaults


def _pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
        return True
    except PermissionError:
        return True
    except OSError:
        return False


@contextlib.contextmanager
def operation_lock(root: Path, label: str):
    lock_path = state_dir(root) / "operation.lock"
    key = str(lock_path)
    if _LOCK_DEPTH.get(key, 0) > 0:
        _LOCK_DEPTH[key] += 1
        try:
            yield
        finally:
            _LOCK_DEPTH[key] -= 1
        return
    policy = load_policy(root)
    stale_after = int(policy.get("operationLockStaleSeconds") or 21600)
    payload = {
        "schema": "forgepy.operation.lock.v1",
        "pid": os.getpid(),
        "host": socket.gethostname(),
        "label": label,
        "createdUtc": datetime.now(timezone.utc).isoformat(),
        "createdEpoch": time.time(),
    }
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    while True:
        try:
            fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
                json.dump(payload, f, indent=2, sort_keys=True)
                f.write("\n")
            break
        except FileExistsError:
            existing = read_json(lock_path, {}) or {}
            pid = int(existing.get("pid") or 0) if str(existing.get("pid") or "").isdigit() else 0
            age = max(0.0, time.time() - float(existing.get("createdEpoch") or lock_path.stat().st_mtime))
            same_host = not existing.get("host") or existing.get("host") == socket.gethostname()
            reclaim = (same_host and pid > 0 and not _pid_alive(pid)) or (age > stale_after and (not same_host or pid <= 0))
            if reclaim:
                with contextlib.suppress(OSError):
                    lock_path.unlink()
                continue
            holder = f"pid={pid or '?'} host={existing.get('host') or '?'} label={existing.get('label') or '?'}"
            raise RuntimeError(f"another ForgePY operation is active ({holder}); lock={lock_path}")
    _LOCK_DEPTH[key] = 1
    try:
        yield
    finally:
        _LOCK_DEPTH.pop(key, None)
        with contextlib.suppress(OSError):
            lock_path.unlink()


def terminate_process_tree(p: subprocess.Popen[str]) -> None:
    if p.poll() is not None:
        return
    if os.name == "nt":
        with contextlib.suppress(Exception):
            subprocess.run(["taskkill", "/PID", str(p.pid), "/T", "/F"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    else:
        with contextlib.suppress(Exception):
            os.killpg(p.pid, signal.SIGTERM)
            p.wait(timeout=3)
        if p.poll() is None:
            with contextlib.suppress(Exception):
                os.killpg(p.pid, signal.SIGKILL)
    with contextlib.suppress(Exception):
        p.terminate()
    with contextlib.suppress(Exception):
        p.wait(timeout=2)
    with contextlib.suppress(Exception):
        p.kill()


def command_timeout(root: Path, cmd: dict[str, Any]) -> float | None:
    if "timeoutSeconds" in cmd:
        raw = float(cmd.get("timeoutSeconds") or 0)
        return raw if raw > 0 else None
    env = os.environ.get("FORGEPY_TIMEOUT_SECONDS", "").strip()
    if env:
        try:
            raw = float(env)
            return raw if raw > 0 else None
        except ValueError:
            pass
    category = str(cmd.get("category") or "").casefold()
    policy = load_policy(root)
    key = {
        "gate": "defaultGateTimeoutSeconds",
        "build": "defaultBuildTimeoutSeconds",
        "test": "defaultTestTimeoutSeconds",
        "run": "defaultRunTimeoutSeconds",
    }.get(category)
    raw = float(policy.get(key, 0) or 0) if key else 0
    return raw if raw > 0 else None


def append_operation_history(root: Path, payload: dict[str, Any]) -> None:
    path = state_dir(root) / "operations.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(payload, sort_keys=True, ensure_ascii=False) + "\n"
    with path.open("a", encoding="utf-8", newline="\n") as f:
        f.write(line)
        f.flush()
        os.fsync(f.fileno())


def operation_history(root: Path, count: int = 100) -> list[dict[str, Any]]:
    path = state_dir(root) / "operations.jsonl"
    if not path.is_file():
        return []
    rows: list[dict[str, Any]] = []
    try:
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            if not line.strip():
                continue
            with contextlib.suppress(Exception):
                item = json.loads(line)
                if isinstance(item, dict):
                    rows.append(item)
    except OSError:
        return []
    return rows[-max(1, int(count)):]


def record_evidence(root: Path, cmd: dict[str, Any], code: int, started: float, log_path: Path | None) -> None:
    item: dict[str, Any] = {
        "schema": "forgepy.operation.evidence.v1",
        "createdUtc": datetime.now(timezone.utc).isoformat(),
        "key": str(cmd.get("key") or ""),
        "label": str(cmd.get("label") or cmd.get("key") or ""),
        "category": str(cmd.get("category") or ""),
        "source": str(cmd.get("_source") or "project"),
        "provider": str(cmd.get("_provider") or cmd.get("_source") or "project"),
        "exitCode": int(code),
        "durationSeconds": round(max(0.0, time.monotonic() - started), 3),
    }
    if log_path:
        try:
            item["logPath"] = log_path.relative_to(root).as_posix()
        except ValueError:
            item["logPath"] = str(log_path)
    _OP_EVIDENCE.append(item)
    with contextlib.suppress(Exception):
        append_operation_history(root, item)


def run_capture(argv: Sequence[str], cwd: Path, timeout: float | None = None) -> subprocess.CompletedProcess[str]:
    flags = int(getattr(subprocess, "CREATE_NO_WINDOW", 0)) if os.name == "nt" else 0
    startupinfo = None
    if os.name == "nt":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= int(getattr(subprocess, "STARTF_USESHOWWINDOW", 1))
        startupinfo.wShowWindow = int(getattr(subprocess, "SW_HIDE", 0))
    return subprocess.run(
        list(argv), cwd=str(cwd), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, encoding="utf-8", errors="replace", timeout=timeout,
        check=False, creationflags=flags, startupinfo=startupinfo,
    )


def stream(argv: Sequence[str], cwd: Path, log_path: Path | None = None, *, append: bool = False, timeout: float | None = None) -> int:
    print("[CLI] " + " ".join(_quote(str(x)) for x in argv))
    log = None
    if log_path:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log = log_path.open("a" if append else "w", encoding="utf-8", newline="\n")
    creationflags = 0
    popen_kwargs: dict[str, Any] = {}
    if os.name == "nt":
        creationflags |= int(getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0))
        popen_kwargs["creationflags"] = creationflags
    else:
        popen_kwargs["start_new_session"] = True
    try:
        p = subprocess.Popen(
            list(argv), cwd=str(cwd), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding="utf-8", errors="replace", bufsize=1, **popen_kwargs,
        )
    except FileNotFoundError:
        if log:
            log.close()
        print(f"[FAIL] executable not found: {argv[0]}")
        return 127
    q: queue.Queue[str | None] = queue.Queue()
    def reader() -> None:
        try:
            assert p.stdout is not None
            for line in p.stdout:
                q.put(line)
        finally:
            q.put(None)
    t = threading.Thread(target=reader, name="forgepy-output", daemon=True)
    t.start()
    deadline = time.monotonic() + timeout if timeout else None
    timed_out = False
    try:
        done = False
        while not done:
            if deadline is not None and time.monotonic() >= deadline:
                timed_out = True
                print(f"\n[FAIL] Operation timed out after {timeout:g}s; terminating process tree.")
                terminate_process_tree(p)
                break
            try:
                item = q.get(timeout=0.2)
            except queue.Empty:
                if p.poll() is not None and not t.is_alive():
                    break
                continue
            if item is None:
                done = True
            else:
                print(item, end="")
                if log:
                    log.write(item)
                    log.flush()
        if timed_out:
            return 124
        return int(p.wait())
    except KeyboardInterrupt:
        print("\n[WARN] Operation interrupted; terminating child process tree.")
        terminate_process_tree(p)
        return 130
    finally:
        if log:
            log.close()

def _quote(v: str) -> str:
    if not v or any(c.isspace() for c in v) or '"' in v:
        return '"' + v.replace('"', '\\"') + '"'
    return v


def command(key: str, label: str, category: str, program: str, args: Iterable[str], *, risk="read", mutates=False, source="generated") -> dict[str, Any]:
    return {
        "key": key, "label": label, "category": category, "risk": risk,
        "program": program, "args": list(args), "mutates": bool(mutates), "_source": source,
    }


def has_python_source(root: Path) -> bool:
    if (root / "pyproject.toml").is_file() or (root / "requirements.txt").is_file() or any(root.glob("*.py")):
        return True
    skip = {".git", ".forgepy", ".venv", "venv", "node_modules", "target", "build", "dist", "__pycache__"}
    for top in (root / "app", root / "src", root / "tools", root / "tests"):
        if not top.is_dir():
            continue
        for base, dirs, files in os.walk(top, followlinks=False):
            dirs[:] = [d for d in dirs if d not in skip]
            if any(name.endswith(".py") for name in files):
                return True
    return False


def _scan_candidate(path: Path) -> bool:
    return path.name in SCAN_EXACT_MARKERS or path.suffix.casefold() in SCAN_SUFFIX_MARKERS


def _python_source_signal(root: Path, path: Path) -> bool:
    """Return True for one structural Python source signal without indexing every .py file."""
    if path.suffix.casefold() != ".py":
        return False
    try:
        rel = path.relative_to(root)
    except ValueError:
        return False
    if len(rel.parts) == 1:
        return True
    return rel.parts[0] in {"app", "src", "tools", "tests"}


def _scan_files(root: Path) -> list[Path]:
    """Return structural project markers while avoiding build/vendor trees.

    Git repositories use `git ls-files -co --exclude-standard`, which is much faster than
    recursively stat'ing large working trees and naturally honors .gitignore. Non-Git
    folders use a bounded pruned walk. Exactly one ordinary Python source file is retained
    as a structural signal so a source-only Python repository can be discovered without
    making every Python edit invalidate the build-plan cache.
    """
    max_depth = int(load_policy(root).get("scanMaxDepth") or 7) if (root / ".forgepy/policy.json").is_file() else 7
    found: set[Path] = set()
    python_signal: Path | None = None
    git_exe = shutil.which("git")
    if git_exe and (root / ".git").exists():
        cp = subprocess.run(
            [git_exe, "-C", str(root), "ls-files", "-co", "--exclude-standard", "-z"],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False,
        )
        if cp.returncode == 0:
            for raw in cp.stdout.split(b"\0"):
                if not raw:
                    continue
                rel = raw.decode("utf-8", errors="replace").replace("\\", "/")
                parts = Path(rel).parts
                if len(parts) - 1 > max_depth or any(part in SCAN_SKIP_DIRS for part in parts[:-1]):
                    continue
                path = root / rel
                if not path.is_file():
                    continue
                if _scan_candidate(path):
                    found.add(path)
                elif python_signal is None and _python_source_signal(root, path):
                    python_signal = path
    if not found and python_signal is None:
        for base, dirs, files in os.walk(root, followlinks=False):
            b = Path(base)
            try:
                depth = len(b.relative_to(root).parts)
            except ValueError:
                continue
            dirs[:] = [d for d in dirs if d not in SCAN_SKIP_DIRS and depth < max_depth]
            for name in files:
                path = b / name
                if _scan_candidate(path):
                    found.add(path)
                elif python_signal is None and _python_source_signal(root, path):
                    python_signal = path
    # Root markers may be freshly dropped/untracked even when git discovery is available.
    with contextlib.suppress(OSError):
        for path in root.iterdir():
            if path.is_file() and _scan_candidate(path):
                found.add(path)
            elif path.is_file() and python_signal is None and _python_source_signal(root, path):
                python_signal = path
    if python_signal is not None:
        found.add(python_signal)
    return sorted(found, key=lambda x: x.relative_to(root).as_posix().casefold())


def _scan_signature(root: Path, paths: list[Path]) -> str:
    h = hashlib.sha256()
    for path in paths:
        try:
            st = path.stat()
            rel = path.relative_to(root).as_posix()
            if _python_source_signal(root, path) and not _scan_candidate(path):
                h.update(f"python-source\0{rel}\n".encode("utf-8", errors="replace"))
            else:
                h.update(f"{rel}\0{st.st_size}\0{st.st_mtime_ns}\n".encode("utf-8", errors="replace"))
        except OSError:
            continue
    return h.hexdigest()


def _component_slug(kind: str, cwd: str) -> str:
    tail = "root" if cwd in {"", "."} else safe_slug(cwd.replace("/", "-"))
    return safe_slug(f"{kind}-{tail}")


def _scan_command(key: str, label: str, category: str, program: str, args: Iterable[str], *, cwd: str = ".", risk: str = "read", mutates: bool = False, component: str = "root") -> dict[str, Any]:
    row = command(key, label, category, program, args, risk=risk, mutates=mutates, source="forgepy-scan")
    row["cwd"] = cwd or "."
    row["_provider"] = "forgepy-auto"
    row["_component"] = component
    return row


def _node_program(root: Path, cwd: str, package: dict[str, Any]) -> str:
    declared = str(package.get("packageManager") or "").split("@", 1)[0].strip().casefold()
    base = root if cwd in {"", "."} else root / cwd
    if declared in {"pnpm", "yarn", "npm", "bun"}:
        return declared
    if (base / "pnpm-lock.yaml").is_file():
        return "pnpm"
    if (base / "yarn.lock").is_file():
        return "yarn"
    if (base / "bun.lockb").is_file() or (base / "bun.lock").is_file():
        return "bun"
    return "npm"


def _script_args(program: str, script: str) -> list[str]:
    if program == "yarn":
        return [script]
    if program == "bun":
        return ["run", script]
    if program == "pnpm":
        return ["run", script]
    return ["run", script] if script != "test" else ["test"]


def repository_scan(root: Path, *, force: bool = False) -> dict[str, Any]:
    paths = _scan_files(root)
    signature = _scan_signature(root, paths)
    cache = root / ".forgepy" / "cache" / "repository.scan.v1.json"
    if not force and cache.is_file():
        cached = read_json(cache, {}) or {}
        if cached.get("schema") == SCAN_PLAN_SCHEMA and cached.get("signature") == signature:
            cached["cacheHit"] = True
            return cached

    marker_map: dict[str, list[Path]] = {}
    for path in paths:
        marker_map.setdefault(path.name, []).append(path)

    components: list[dict[str, Any]] = []
    operations: list[dict[str, Any]] = []
    warnings: list[str] = []
    unresolved: list[dict[str, Any]] = []
    seen_ops: set[str] = set()

    def add_component(kind: str, base: Path, markers: list[str], confidence: str = "confirmed") -> str:
        cwd = base.relative_to(root).as_posix() if base != root else "."
        cid = _component_slug(kind, cwd)
        row = {"id": cid, "kind": kind, "cwd": cwd, "markers": sorted(set(markers)), "confidence": confidence}
        if not any(x.get("id") == cid for x in components):
            components.append(row)
        return cid

    def add_op(row: dict[str, Any]) -> None:
        folded = str(row.get("key") or "").casefold()
        if not folded or folded in seen_ops:
            return
        seen_ops.add(folded)
        operations.append(row)

    # Rust: a root Cargo.toml normally owns nested workspace members, so avoid duplicate workspace builds.
    cargo_paths = marker_map.get("Cargo.toml", [])
    cargo_roots = [root / "Cargo.toml"] if (root / "Cargo.toml").is_file() else cargo_paths
    for path in cargo_paths:
        add_component("rust", path.parent, [path.name])
    for path in cargo_roots:
        cwd = path.parent.relative_to(root).as_posix() if path.parent != root else "."
        cid = _component_slug("rust", cwd)
        suffix = cid
        add_op(_scan_command(f"gate.rust.{suffix}", f"Cargo Check ({cwd})", "gate", "cargo", ["check", "--workspace"], cwd=cwd, component=cid))
        add_op(_scan_command(f"build.rust.{suffix}", f"Cargo Build ({cwd})", "build", "cargo", ["build", "--workspace"], cwd=cwd, risk="write", mutates=True, component=cid))
        add_op(_scan_command(f"build-release.rust.{suffix}", f"Cargo Release Build ({cwd})", "build-release", "cargo", ["build", "--workspace", "--release"], cwd=cwd, risk="write", mutates=True, component=cid))
        add_op(_scan_command(f"test.rust.{suffix}", f"Cargo Tests ({cwd})", "test", "cargo", ["test", "--workspace"], cwd=cwd, component=cid))

    # Node: each package with useful scripts is an independently callable component.
    for path in marker_map.get("package.json", []):
        package = read_json(path, {}) or {}
        cwd = path.parent.relative_to(root).as_posix() if path.parent != root else "."
        cid = add_component("node", path.parent, [path.name])
        scripts = package.get("scripts") if isinstance(package.get("scripts"), dict) else {}
        program = _node_program(root, cwd, package)
        for script, category in (("build", "build"), ("test", "test"), ("start", "run"), ("dev", "run")):
            if script not in scripts:
                continue
            if category == "run" and any(str(x.get("category")) == "run" and x.get("_component") == cid for x in operations):
                continue
            key = f"{category}.node.{cid}"
            add_op(_scan_command(key, f"{program} {script} ({cwd})", category, program, _script_args(program, script), cwd=cwd, risk="write" if category == "build" else "read", mutates=(category == "build"), component=cid))

    # CMake: a root CMakeLists usually owns nested subdirectories; otherwise each discovered root can build itself.
    cmake_paths = marker_map.get("CMakeLists.txt", [])
    cmake_roots = [root / "CMakeLists.txt"] if (root / "CMakeLists.txt").is_file() else cmake_paths
    for path in cmake_paths:
        add_component("cmake", path.parent, [path.name])
    for path in cmake_roots:
        cwd = path.parent.relative_to(root).as_posix() if path.parent != root else "."
        cid = _component_slug("cmake", cwd)
        build_dir = ".forgepy/build/cmake" if cwd == "." else f".forgepy/build/cmake/{cid}"
        add_op(_scan_command(f"build.cmake.{cid}", f"CMake Configure + Build ({cwd})", "build", "__forgepy_internal__", ["cmake-build", build_dir], cwd=cwd, risk="write", mutates=True, component=cid))

    # Python packaging/source components. Build = syntax/compile verification unless a project contract declares a stronger build.
    python_markers = []
    for name in ("pyproject.toml", "requirements.txt", "setup.py", "setup.cfg"):
        python_markers.extend(marker_map.get(name, []))
    py_dirs = sorted({p.parent for p in python_markers})
    if not py_dirs and has_python_source(root):
        py_dirs = [root]
    for base in py_dirs:
        cwd = base.relative_to(root).as_posix() if base != root else "."
        markers = [p.name for p in python_markers if p.parent == base] or ["Python source"]
        cid = add_component("python", base, markers, "detected")
        add_op(_scan_command(f"gate.python.{cid}", f"Python Syntax Check ({cwd})", "gate", "__forgepy_internal__", ["python-syntax", cwd], cwd=cwd, component=cid))
        add_op(_scan_command(f"build.python.{cid}", f"Python Verify ({cwd})", "build", "__forgepy_internal__", ["python-syntax", cwd], cwd=cwd, component=cid))
        tests = base / "tests"
        if tests.is_dir():
            if importlib.util.find_spec("pytest") is not None:
                add_op(_scan_command(f"test.python.{cid}", f"Pytest ({cwd})", "test", "python", ["-m", "pytest", "-q"], cwd=cwd, component=cid))
            else:
                add_op(_scan_command(f"test.python.{cid}", f"unittest ({cwd})", "test", "python", ["-m", "unittest", "discover", "-s", "tests"], cwd=cwd, component=cid))
        for candidate in ("main.py", "app.py", "run.py", "app/main.py", "src/main.py"):
            if (base / candidate).is_file():
                add_op(_scan_command(f"run.python.{cid}", f"Run {candidate} ({cwd})", "run", "python", [candidate], cwd=cwd, component=cid))
                break

    # .NET/MSBuild: prefer solutions; fall back to project files.
    dotnet_paths = [p for p in paths if p.suffix.casefold() in {".sln", ".slnx", ".csproj", ".fsproj", ".vbproj"}]
    by_dir: dict[Path, list[Path]] = {}
    for path in dotnet_paths:
        by_dir.setdefault(path.parent, []).append(path)
    for base, rows in sorted(by_dir.items(), key=lambda x: x[0].as_posix().casefold()):
        solutions = sorted([x for x in rows if x.suffix.casefold() in {".sln", ".slnx"}])
        targets = solutions[:1] or sorted(rows)[:1]
        if not targets:
            continue
        target = targets[0]
        cwd = base.relative_to(root).as_posix() if base != root else "."
        cid = add_component("dotnet", base, [x.name for x in rows])
        msbuild = find_msbuild()
        if msbuild and target.suffix.casefold() == ".sln":
            add_op(_scan_command(f"build.dotnet.{cid}", f"MSBuild {target.name} ({cwd})", "build", msbuild, [target.name, "/m"], cwd=cwd, risk="write", mutates=True, component=cid))
        else:
            add_op(_scan_command(f"build.dotnet.{cid}", f"dotnet build {target.name} ({cwd})", "build", "dotnet", ["build", target.name], cwd=cwd, risk="write", mutates=True, component=cid))
        add_op(_scan_command(f"test.dotnet.{cid}", f"dotnet test {target.name} ({cwd})", "test", "dotnet", ["test", target.name], cwd=cwd, component=cid))

    # Make / Gradle / Maven / Go / Zig / Meson.
    make_dirs = sorted({p.parent for name in ("Makefile", "makefile") for p in marker_map.get(name, [])})
    for base in make_dirs:
        cwd = base.relative_to(root).as_posix() if base != root else "."
        markers = [p.name for name in ("Makefile", "makefile") for p in marker_map.get(name, []) if p.parent == base]
        cid = add_component("make", base, markers)
        add_op(_scan_command(f"build.make.{cid}", f"Make Build ({cwd})", "build", "make", [], cwd=cwd, risk="write", mutates=True, component=cid))
        add_op(_scan_command(f"test.make.{cid}", f"Make Test ({cwd})", "test", "make", ["test"], cwd=cwd, component=cid))

    gradle_dirs = sorted({p.parent for name in ("gradlew", "gradlew.bat", "build.gradle", "build.gradle.kts") for p in marker_map.get(name, [])})
    for base in gradle_dirs:
        cwd = base.relative_to(root).as_posix() if base != root else "."
        wrapper = next((base / name for name in ("gradlew.bat", "gradlew") if (base / name).is_file()), None)
        prog = wrapper.name if wrapper else "gradle"
        markers = [p.name for name in ("gradlew", "gradlew.bat", "build.gradle", "build.gradle.kts") for p in marker_map.get(name, []) if p.parent == base]
        cid = add_component("gradle", base, markers)
        add_op(_scan_command(f"build.gradle.{cid}", f"Gradle Build ({cwd})", "build", prog, ["build"], cwd=cwd, risk="write", mutates=True, component=cid))
        add_op(_scan_command(f"test.gradle.{cid}", f"Gradle Test ({cwd})", "test", prog, ["test"], cwd=cwd, component=cid))
    for path in marker_map.get("pom.xml", []):
        cwd = path.parent.relative_to(root).as_posix() if path.parent != root else "."
        cid = add_component("maven", path.parent, [path.name])
        add_op(_scan_command(f"build.maven.{cid}", f"Maven Package ({cwd})", "build", "mvn", ["package", "-DskipTests"], cwd=cwd, risk="write", mutates=True, component=cid))
        add_op(_scan_command(f"test.maven.{cid}", f"Maven Test ({cwd})", "test", "mvn", ["test"], cwd=cwd, component=cid))
    for path in marker_map.get("go.mod", []):
        cwd = path.parent.relative_to(root).as_posix() if path.parent != root else "."
        cid = add_component("go", path.parent, [path.name])
        add_op(_scan_command(f"build.go.{cid}", f"Go Build ({cwd})", "build", "go", ["build", "./..."], cwd=cwd, risk="write", mutates=True, component=cid))
        add_op(_scan_command(f"test.go.{cid}", f"Go Test ({cwd})", "test", "go", ["test", "./..."], cwd=cwd, component=cid))
    for path in marker_map.get("build.zig", []):
        cwd = path.parent.relative_to(root).as_posix() if path.parent != root else "."
        cid = add_component("zig", path.parent, [path.name])
        add_op(_scan_command(f"build.zig.{cid}", f"Zig Build ({cwd})", "build", "zig", ["build"], cwd=cwd, risk="write", mutates=True, component=cid))
        add_op(_scan_command(f"test.zig.{cid}", f"Zig Test ({cwd})", "test", "zig", ["build", "test"], cwd=cwd, component=cid))
    for path in marker_map.get("meson.build", []):
        cwd = path.parent.relative_to(root).as_posix() if path.parent != root else "."
        cid = add_component("meson", path.parent, [path.name])
        bdir = f".forgepy/build/meson/{cid}"
        add_op(_scan_command(f"build.meson.{cid}", f"Meson Compile ({cwd})", "build", "__forgepy_internal__", ["meson-build", bdir], cwd=cwd, risk="write", mutates=True, component=cid))

    # Conventional scripts are useful fallback providers. Generate only when a component-level operation of that category is absent in the same cwd.
    script_names = {
        "build": ("build.cmd", "build.bat", "build.ps1", "build.sh"),
        "test": ("test.cmd", "test.bat", "test.ps1", "test.sh"),
        "run": ("run.cmd", "run.bat", "run.ps1", "run.sh"),
    }
    for category, names in script_names.items():
        for name in names:
            for path in marker_map.get(name, []):
                cwd = path.parent.relative_to(root).as_posix() if path.parent != root else "."
                if any(str(x.get("category")) == category and str(x.get("cwd") or ".") == cwd for x in operations):
                    continue
                cid = add_component("script", path.parent, [path.name], "detected")
                add_op(_scan_command(f"{category}.script.{cid}", f"Project {category.title()} Script ({cwd})", category, path.name, [], cwd=cwd, risk="write" if category == "build" else "read", mutates=(category == "build"), component=cid))

    # Detection-only project types that need environment-specific configuration before a reliable build can be synthesized.
    for path in [p for p in paths if p.suffix.casefold() == ".uproject"]:
        cwd = path.parent.relative_to(root).as_posix() if path.parent != root else "."
        cid = add_component("unreal", path.parent, [path.name], "detected")
        unresolved.append({"component": cid, "severity": "info", "message": f"Unreal project {path.name} detected; declare Engine/UBT command in a project adapter for deterministic builds."})
    for path in marker_map.get("project.godot", []):
        cwd = path.parent.relative_to(root).as_posix() if path.parent != root else "."
        cid = add_component("godot", path.parent, [path.name], "detected")
        add_op(_scan_command(f"run.godot.{cid}", f"Run Godot Project ({cwd})", "run", "godot", ["--path", "."], cwd=cwd, component=cid))
        if not (path.parent / "export_presets.cfg").is_file():
            unresolved.append({"component": cid, "severity": "info", "message": "Godot export presets not found; run is available but no automatic export/package operation was generated."})

    pcc = root / "PROJECT_CONTROL_CENTER.cmd"
    if pcc.is_file():
        text = pcc.read_text(encoding="utf-8", errors="replace")[:4096]
        if "ForgePY-owned launcher:" not in text:
            unresolved.append({"component": "project-pcc", "severity": "info", "message": "Existing project-owned PROJECT_CONTROL_CENTER.cmd detected and preserved. Add project.control.json to declare its semantic operations explicitly."})

    # Default semantic operations are composites for build/test/check so mixed repositories behave like one project.
    category_members = {
        cat: [str(x.get("key")) for x in operations if x.get("category") == cat]
        for cat in ("gate", "build", "build-release", "test", "run")
    }
    defaults: dict[str, Any] = {}
    if category_members["gate"]:
        defaults["gate.fast"] = category_members["gate"]
    if category_members["build"]:
        defaults["build.default"] = category_members["build"]
    if category_members["build-release"]:
        defaults["build.release"] = category_members["build-release"]
    if category_members["test"]:
        defaults["test.default"] = category_members["test"]
    if category_members["run"]:
        # Running every client/tool at once is unsafe; choose the shallowest/root run target as the default.
        run_rows = [x for x in operations if x.get("category") == "run"]
        run_rows.sort(key=lambda x: (0 if x.get("cwd") == "." else 1, len(Path(str(x.get("cwd") or ".")).parts), str(x.get("key"))))
        defaults["run.default"] = [str(run_rows[0].get("key"))]

    kinds = sorted({str(x.get("kind")) for x in components})
    if not operations:
        warnings.append("No deterministic build/test/run operations could be synthesized. Add a project.control.json or ForgePY adapter for this repository.")
    max_components = int(load_policy(root).get("scanMaxComponents") or 96) if (root / ".forgepy/policy.json").is_file() else 96
    if len(components) > max_components:
        warnings.append(f"Component scan found {len(components)} components; only the first {max_components} are shown in the plan.")
        components = components[:max_components]

    plan = {
        "schema": SCAN_PLAN_SCHEMA,
        "scanSchema": SCAN_SCHEMA,
        "signature": signature,
        "generatedUtc": datetime.now(timezone.utc).isoformat(),
        "root": str(root),
        "cacheHit": False,
        "markerCount": len(paths),
        "componentCount": len(components),
        "kinds": kinds,
        "components": components,
        "operations": operations,
        "defaults": defaults,
        "warnings": warnings,
        "unresolved": unresolved,
    }
    cache.parent.mkdir(parents=True, exist_ok=True)
    atomic_json(cache, plan)
    return plan


def detect_kind(root: Path) -> str:
    try:
        plan = repository_scan(root)
        kinds = [str(x) for x in plan.get("kinds") or [] if x]
        return "-".join(kinds) if kinds else "generic"
    except Exception:
        kinds: list[str] = []
        if (root / "Cargo.toml").is_file(): kinds.append("rust")
        if has_python_source(root): kinds.append("python")
        if (root / "package.json").is_file(): kinds.append("node")
        if (root / "CMakeLists.txt").is_file(): kinds.append("cmake")
        return "-".join(kinds) if kinds else "generic"

def explicit_contract_path(root: Path) -> Path | None:
    for rel in (
        "project.control.json",
        ".forgepy/adapters/project.control.json",
        ".pcc/project.control.json",
        "tools/pcc/project.control.json",
    ):
        path = root / rel
        if path.is_file():
            return path
    return None


def load_explicit(root: Path) -> dict[str, Any] | None:
    path = explicit_contract_path(root)
    if path is None:
        return None
    data = read_json(path)
    if not isinstance(data, dict):
        raise ValueError(f"invalid JSON: {path}")
    return validate_contract(data, path)


def project_identity_path(root: Path) -> Path:
    return root / ".forgepy" / "project.identity.json"


def load_project_identity(root: Path) -> dict[str, Any] | None:
    path = project_identity_path(root)
    if not path.is_file():
        return None
    data = read_json(path)
    if not isinstance(data, dict) or data.get("schema") != "forgepy.project.identity.v1":
        raise ValueError(f"invalid ForgePY project identity: {path}")
    value = str(data.get("uuid") or "")
    try:
        uuid.UUID(value)
    except Exception as exc:
        raise ValueError(f"invalid ForgePY project UUID in {path}: {value!r}") from exc
    return data


def ensure_project_identity(root: Path, project_name: str | None = None) -> dict[str, Any]:
    existing = load_project_identity(root)
    if existing:
        return existing
    payload = {
        "schema": "forgepy.project.identity.v1",
        "uuid": str(uuid.uuid4()),
        "projectNameAtOnboarding": project_name or root.name,
        "rootNameAtOnboarding": root.name,
        "createdUtc": datetime.now(timezone.utc).isoformat(),
        "createdBy": BUILD,
    }
    atomic_json(project_identity_path(root), payload)
    return payload


def provider_descriptor(root: Path, explicit: dict[str, Any] | None = None) -> dict[str, Any]:
    explicit = explicit if explicit is not None else load_explicit(root)
    path = explicit_contract_path(root) if explicit else None
    if not explicit or path is None:
        return {
            "type": "forgepy-auto",
            "name": "ForgePY Automatic Discovery",
            "source": "forgepy-generated",
            "precedence": 4,
        }
    rel = path.relative_to(root).as_posix()
    declared = explicit.get("provider") if isinstance(explicit.get("provider"), dict) else {}
    if rel == "project.control.json":
        ptype = str(declared.get("type") or "project-contract")
        precedence = 1 if ptype == "internal-pcc" else 2
        default_name = "Project Internal PCC" if ptype == "internal-pcc" else "Project Contract"
    else:
        ptype = str(declared.get("type") or "forgepy-adapter")
        precedence = 3
        default_name = "ForgePY Project Adapter"
    return {
        "type": ptype,
        "name": str(declared.get("name") or default_name),
        "source": rel,
        "precedence": precedence,
    }


def discover_capabilities(root: Path, data: dict[str, Any]) -> list[dict[str, Any]]:
    caps: list[dict[str, Any]] = []
    provider = data.get("_provider") or {}
    def add(key: str, label: str, confidence: str, evidence: list[str], owner: str = "forgepy-discovery") -> None:
        caps.append({
            "key": key, "label": label, "confidence": confidence,
            "evidence": evidence, "provider": owner,
        })
    if (root / "Cargo.toml").is_file(): add("stack.rust", "Rust / Cargo", "confirmed", ["Cargo.toml"])
    if has_python_source(root):
        evidence = [x for x in ("pyproject.toml", "requirements.txt") if (root / x).is_file()] or ["Python source discovered"]
        add("stack.python", "Python", "detected", evidence)
    if (root / "package.json").is_file(): add("stack.node", "Node / npm", "confirmed", ["package.json"])
    if (root / "CMakeLists.txt").is_file(): add("stack.cmake", "CMake", "confirmed", ["CMakeLists.txt"])
    dotnet_files = sorted([*root.glob("*.sln"), *root.glob("*.slnx"), *root.glob("*.csproj"), *root.glob("*.fsproj"), *root.glob("*.vbproj")])
    if dotnet_files: add("stack.dotnet", ".NET / MSBuild", "confirmed", [p.name for p in dotnet_files[:4]])
    if (root / "gradlew").exists() or (root / "gradlew.bat").exists(): add("stack.gradle", "Gradle", "confirmed", ["gradlew/gradlew.bat"])
    if (root / "Makefile").is_file(): add("stack.make", "Make", "confirmed", ["Makefile"])
    if provider.get("type") == "internal-pcc":
        add("provider.internal-pcc", "Project Internal PCC", "declared", [str(provider.get("source") or "project.control.json")], "internal-pcc")
    categories: dict[str, list[dict[str, Any]]] = {}
    for cmd in data.get("commands", []):
        if not isinstance(cmd, dict):
            continue
        categories.setdefault(str(cmd.get("category") or "other"), []).append(cmd)
    for category in ("gate", "build", "test", "run"):
        rows = categories.get(category, [])
        keys = [str(x.get("key") or "") for x in rows if x.get("key")]
        if not keys:
            continue
        explicit_rows = [x for x in rows if str(x.get("_source")) == "explicit"]
        owners = {str(x.get("_provider") or x.get("_source") or "project") for x in rows}
        owner = str(provider.get("type") or "project-contract") if explicit_rows else (next(iter(owners)) if len(owners) == 1 else "mixed")
        add(f"operation.{category}", f"{category.title()} operations", "declared" if explicit_rows else "detected", keys[:8], owner)
    if git_available(root): add("service.git", "Git repository", "confirmed", [".git", shutil.which("git") or "git"], "forgepy-core")
    add("service.patch-intake", "Root patch intake", "confirmed", ["*.patch", "safe git apply workflow"], "forgepy-core")
    add("service.certification", "GREEN certification", "confirmed", ["source fingerprint", "gate receipts"], "forgepy-core")
    return caps


def find_msbuild() -> str | None:
    direct = shutil.which("msbuild") or shutil.which("MSBuild.exe")
    if direct:
        return direct
    if os.name != "nt":
        return None
    pf86 = os.environ.get("ProgramFiles(x86)")
    if not pf86:
        return None
    vswhere = Path(pf86) / "Microsoft Visual Studio" / "Installer" / "vswhere.exe"
    if not vswhere.is_file():
        return None
    cp = run_capture([str(vswhere), "-latest", "-products", "*", "-requires", "Microsoft.Component.MSBuild", "-find", r"MSBuild\**\Bin\MSBuild.exe"], Path.cwd(), 15)
    for line in cp.stdout.splitlines():
        candidate = Path(line.strip())
        if candidate.is_file():
            return str(candidate)
    return None


def project_python(root: Path) -> str:
    override = os.environ.get("FORGEPY_PROJECT_PYTHON", "").strip()
    if override:
        candidate = Path(override)
        if candidate.is_file() or shutil.which(override):
            return str(candidate) if candidate.is_file() else str(shutil.which(override))
    candidates = [
        root / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python"),
        root / "venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python"),
    ]
    for candidate in candidates:
        if candidate.is_file():
            return str(candidate)
    return sys.executable


def command_cwd(root: Path, cmd: dict[str, Any]) -> Path:
    rel = str(cmd.get("cwd") or ".")
    path = (root / rel).resolve()
    if not _within(root, path):
        raise ValueError(f"operation cwd escapes project root: {rel}")
    if not path.is_dir():
        raise ValueError(f"operation cwd does not exist or is not a directory: {rel}")
    return path


def generated_commands(root: Path) -> list[dict[str, Any]]:
    plan = repository_scan(root)
    out = [dict(x) for x in (plan.get("operations") or []) if isinstance(x, dict)]
    defaults = plan.get("defaults") if isinstance(plan.get("defaults"), dict) else {}

    def add_composite(key: str, category: str, members: list[str]) -> None:
        if not members:
            return
        row = command(key, f"ForgePY {category.title()} ({len(members)} target{'s' if len(members) != 1 else ''})", category, "__forgepy_internal__", ["composite-category", category], risk="write" if category in {"build", "gate"} else "read", mutates=(category == "build"), source="forgepy-scan")
        row["_provider"] = "forgepy-auto"
        row["_defaultAlias"] = True
        row["_members"] = list(members)
        out.append(row)

    add_composite("gate.fast", "gate", list(defaults.get("gate.fast") or []))
    add_composite("build.default", "build", list(defaults.get("build.default") or []))
    add_composite("build.release", "build-release", list(defaults.get("build.release") or []))
    add_composite("test.default", "test", list(defaults.get("test.default") or []))
    run_members = list(defaults.get("run.default") or [])
    if run_members:
        target = next((x for x in out if x.get("key") == run_members[0]), None)
        if target:
            alias = dict(target)
            alias["key"] = "run.default"
            alias["label"] = f"Default Run → {target.get('label') or target.get('key')}"
            alias["_defaultAlias"] = True
            alias["_aliasFor"] = str(target.get("key"))
            out.append(alias)
    return out

def merge_contract(root: Path) -> dict[str, Any]:
    explicit = load_explicit(root)
    provider = provider_descriptor(root, explicit)
    declared: list[dict[str, Any]] = []
    if explicit:
        for raw in explicit.get("commands", []):
            if isinstance(raw, dict) and raw.get("key") and raw.get("program"):
                item = dict(raw)
                item["_source"] = "explicit"
                item["_provider"] = provider.get("type")
                declared.append(item)
    index = {str(x["key"]).casefold(): x for x in declared}
    for item in generated_commands(root):
        item.setdefault("_provider", "forgepy-auto")
        index.setdefault(str(item["key"]).casefold(), item)
    commands = list(index.values())
    keys = {str(x["key"]).casefold() for x in commands}
    if not any(k in keys for k in ("gate.full", "build.full", "quality.full")):
        full = command("gate.full", "ForgePY Composite Full Gate", "gate", "__forgepy_internal__", ["composite-full"], risk="write", mutates=True)
        full["_provider"] = "forgepy-core"
        commands.append(full)
    project = (explicit or {}).get("project") or {}
    persisted_identity = load_project_identity(root)
    identity = {
        "id": str(project.get("id") or safe_slug(root.name)),
        "uuid": str((persisted_identity or {}).get("uuid") or ""),
        "name": str(project.get("name") or root.name),
        "kind": str(project.get("kind") or detect_kind(root)),
    }
    for key in ("version", "build", "candidateVersion", "candidateBuild"):
        if project.get(key):
            identity[key] = str(project[key])
    discovery = {
        "source": provider["source"],
        "provider": provider["type"],
        "providerName": provider["name"],
        "precedence": provider["precedence"],
        "precedenceOrder": ["internal-pcc", "project-contract", "forgepy-adapter", "forgepy-auto"],
    }
    plan = repository_scan(root)
    discovery.update({
        "scanSchema": plan.get("schema"),
        "scanSignature": plan.get("signature"),
        "scanCacheHit": bool(plan.get("cacheHit")),
        "componentCount": int(plan.get("componentCount") or 0),
        "markerCount": int(plan.get("markerCount") or 0),
        "kinds": list(plan.get("kinds") or []),
        "unresolvedCount": len(plan.get("unresolved") or []),
    })
    data = {
        "schema": "forge.project.v1",
        "project": identity,
        "commands": commands,
        "stateDirectory": str((explicit or {}).get("stateDirectory") or ".forgepy/state"),
        "_provider": provider,
        "_pccDiscovery": discovery,
        "_scanPlan": plan,
    }
    data["capabilities"] = discover_capabilities(root, data)
    return data


def find_command(data: dict[str, Any], key: str) -> dict[str, Any] | None:
    commands = [x for x in data.get("commands", []) if isinstance(x, dict)]
    index = {str(x.get("key", "")).casefold(): x for x in commands}
    if key.casefold() in index:
        return index[key.casefold()]
    for alias in ALIASES.get(key, ()):
        if alias.casefold() in index:
            return index[alias.casefold()]
    return None


def git_available(root: Path) -> bool:
    return bool(shutil.which("git")) and (root / ".git").exists()


def git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return run_capture([shutil.which("git") or "git", "-C", str(root), *args], root)


def git_porcelain_entries(root: Path) -> list[tuple[str, str, str | None]]:
    if not git_available(root):
        return []
    cp = git(root, "status", "--porcelain=v1", "-z", "--untracked-files=all")
    if cp.returncode != 0:
        return []
    parts = cp.stdout.split("\0")
    out: list[tuple[str, str, str | None]] = []
    i = 0
    while i < len(parts):
        rec = parts[i]
        i += 1
        if not rec:
            continue
        if len(rec) < 3:
            continue
        code = rec[:2]
        path = rec[3:] if rec[2:3] == " " else rec[2:].lstrip()
        original = None
        if (code[0] in {"R", "C"} or code[1] in {"R", "C"}) and i < len(parts):
            original = parts[i] or None
            i += 1
        out.append((code, path.replace("\\", "/"), original.replace("\\", "/") if original else None))
    return out


def git_status(root: Path) -> dict[str, Any]:
    result = {"ready": git_available(root), "clean": False, "branch": "", "head": "", "staged": 0, "unstaged": 0, "untracked": 0, "ahead": None, "behind": None}
    if not result["ready"]:
        return result
    entries = git_porcelain_entries(root)
    staged = unstaged = untracked = 0
    for code, _, _ in entries:
        if code == "??":
            untracked += 1
            continue
        if code[0] not in {" ", "?"}: staged += 1
        if code[1] not in {" ", "?"}: unstaged += 1
    result.update(clean=not entries, staged=staged, unstaged=unstaged, untracked=untracked)
    result["branch"] = git(root, "branch", "--show-current").stdout.strip()
    h = git(root, "rev-parse", "HEAD")
    if h.returncode == 0: result["head"] = h.stdout.strip()
    ab = git(root, "rev-list", "--left-right", "--count", "HEAD...@{upstream}")
    if ab.returncode == 0:
        parts = ab.stdout.split()
        if len(parts) == 2 and all(x.isdigit() for x in parts):
            result["ahead"], result["behind"] = map(int, parts)
    return result

def git_history(root: Path, count: int = 12) -> list[dict[str, str]]:
    if not git_available(root):
        return []
    cp = git(root, "log", f"-n{int(count)}", "--date=iso-strict", "--pretty=format:%H%x09%ad%x09%s")
    out: list[dict[str, str]] = []
    if cp.returncode != 0:
        return out
    for line in cp.stdout.splitlines():
        parts = line.split("\t", 2)
        if len(parts) == 3:
            out.append({"sha": parts[0], "date": parts[1], "subject": parts[2]})
    return out


def source_fingerprint(root: Path) -> str:
    if not git_available(root):
        return ""
    h = hashlib.sha256()
    head = git(root, "rev-parse", "HEAD")
    if head.returncode != 0:
        return ""
    h.update(b"HEAD\0" + head.stdout.strip().encode("ascii", "replace") + b"\0")
    intake = _patch_intake_names(root) if "_patch_intake_names" in globals() else set()
    volatile = volatile_runtime_prefixes(root) if "volatile_runtime_prefixes" in globals() else (".forgepy/state/", ".forgepy/artifacts/", ".forgepy/build/", ".forgepy/cache/")

    changed = git(root, "diff", "--name-only", "-z", "HEAD", "--")
    tracked_paths = sorted(x for x in changed.stdout.split("\0") if x) if changed.returncode == 0 else []
    for rel in tracked_paths:
        rel_norm = rel.replace("\\", "/")
        if rel_norm.startswith(volatile):
            continue
        path = root / rel
        h.update(b"T\0" + rel_norm.encode("utf-8", "surrogatepass") + b"\0")
        if path.is_symlink():
            h.update(b"L\0" + os.readlink(path).encode("utf-8", "surrogatepass"))
        elif path.is_file():
            h.update(sha256_file(path).encode("ascii"))
        elif path.is_dir() and (path / ".git").exists():
            sub = run_capture([shutil.which("git") or "git", "-C", str(path), "rev-parse", "HEAD"], root, 10)
            h.update(b"S\0" + sub.stdout.strip().encode("ascii", "replace"))
        else:
            h.update(b"<missing>")

    untracked = git(root, "ls-files", "--others", "--exclude-standard", "-z")
    if untracked.returncode == 0:
        for rel in sorted(x for x in untracked.stdout.split("\0") if x):
            rel_norm = rel.replace("\\", "/")
            if rel_norm in intake or rel_norm.startswith(volatile):
                continue
            path = root / rel
            h.update(b"U\0" + rel_norm.encode("utf-8", "surrogatepass") + b"\0")
            if path.is_symlink():
                h.update(b"L\0" + os.readlink(path).encode("utf-8", "surrogatepass"))
            elif path.is_file():
                h.update(sha256_file(path).encode("ascii"))
            else:
                h.update(b"<nonfile>")
    return h.hexdigest()

def resolve_program(value: str) -> str:
    low = value.strip().casefold()
    if low in {"python", "python.exe", "python3"}: return sys.executable
    if low in {"pwsh", "pwsh.exe"}: return shutil.which("pwsh") or shutil.which("powershell") or "powershell.exe"
    if low in {"powershell", "powershell.exe"}: return shutil.which("powershell") or shutil.which("pwsh") or "powershell.exe"
    if low in {"cmd", "cmd.exe"}: return os.environ.get("COMSPEC") or "cmd.exe"
    return shutil.which(value) or value


def argv_for(root: Path, cmd: dict[str, Any]) -> list[str]:
    raw = str(cmd.get("program") or "").strip()
    args = [str(x).replace("{root}", str(root)).replace("${ROOT}", str(root)) for x in (cmd.get("args") or [])]
    if raw == "__forgepy_internal__":
        return [raw, *args]
    work = command_cwd(root, cmd)
    cwd_candidate = work / raw
    root_candidate = root / raw
    if raw.strip().casefold() in {"python", "python.exe", "python3"}:
        program = project_python(root)
    elif cwd_candidate.is_file():
        program = str(cwd_candidate)
    elif root_candidate.is_file():
        program = str(root_candidate)
    else:
        program = resolve_program(raw)
    suffix = Path(program).suffix.casefold()
    if os.name == "nt" and suffix in {".cmd", ".bat"}:
        return [os.environ.get("COMSPEC") or "cmd.exe", "/d", "/s", "/c", program, *args]
    if suffix == ".ps1":
        return [resolve_program("pwsh"), "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", program, *args]
    if suffix in {".py", ".pyw"}:
        return [project_python(root), program, *args]
    if suffix == ".sh":
        return [resolve_program("bash"), program, *args]
    return [program, *args]


def state_dir(root: Path) -> Path:
    explicit = load_explicit(root)
    rel = str((explicit or {}).get("stateDirectory") or ".forgepy/state")
    path = (root / rel).resolve()
    if not _within(root, path):
        raise ValueError(f"unsafe stateDirectory outside project root: {rel}")
    path.mkdir(parents=True, exist_ok=True)
    return path


def volatile_runtime_prefixes(root: Path) -> tuple[str, ...]:
    prefixes = [".forgepy/state/", ".forgepy/artifacts/", ".forgepy/build/", ".forgepy/cache/", ".forgepy/runtime/__pycache__/"]
    try:
        rel = state_dir(root).relative_to(root).as_posix().rstrip("/") + "/"
        if rel not in prefixes:
            prefixes.append(rel)
    except Exception:
        pass
    return tuple(prefixes)


def python_syntax_check(root: Path, scope: str = ".") -> int:
    skip = {".git", ".forgepy", ".venv", "venv", "node_modules", "target", "build", "dist", "__pycache__"}
    checked = 0
    failures = 0
    paths: list[Path] = []
    scan_root = (root / scope).resolve() if scope not in {"", "."} else root
    if not _within(root, scan_root) or not scan_root.is_dir():
        print(f"[FAIL] Invalid Python syntax scope: {scope}")
        return 2
    for base, dirs, files in os.walk(scan_root, followlinks=False):
        dirs[:] = [d for d in dirs if d not in skip]
        b = Path(base)
        paths.extend(b / name for name in files if name.endswith(".py"))
    for path in sorted(paths):
        try:
            source = path.read_text(encoding="utf-8-sig")
            compile(source, str(path), "exec")
            checked += 1
        except Exception as exc:
            failures += 1
            print(f"[FAIL] Python syntax: {path.relative_to(root)}: {exc}")
    if checked == 0 and failures == 0:
        print("[WARN] No Python source files found for syntax verification.")
        return 0
    print(f"[{'PASS' if failures == 0 else 'FAIL'}] Python syntax: {checked} file(s), {failures} failure(s)")
    return 1 if failures else 0


def run_operation(root: Path, data: dict[str, Any], op: str) -> int:
    cmd = find_command(data, op)
    if not cmd:
        print(f"[FAIL] operation unavailable: {op}")
        return 2
    try:
        with operation_lock(root, f"operation:{cmd.get('key') or op}"):
            started = time.monotonic()
            log_path: Path | None = None
            if cmd.get("program") == "__forgepy_internal__":
                internal = (cmd.get("args") or [""])[0]
                if internal == "composite-full":
                    return composite_full(root, data)
                if internal == "python-syntax":
                    print(f"[INFO] {cmd.get('label') or cmd.get('key')} [{cmd.get('_source', 'project')}]")
                    args = list(cmd.get("args") or [])
                    scope = str(args[1] if len(args) > 1 else cmd.get("cwd") or ".")
                    code = python_syntax_check(root, scope)
                    record_evidence(root, cmd, code, started, None)
                    return code
                if internal == "composite-category":
                    args = list(cmd.get("args") or [])
                    category = str(args[1] if len(args) > 1 else cmd.get("category") or "")
                    code = composite_category(root, data, category)
                    record_evidence(root, cmd, code, started, None)
                    return code
                if internal in {"cmake-build", "meson-build"}:
                    args = list(cmd.get("args") or [])
                    default_dir = ".forgepy/build/cmake" if internal == "cmake-build" else ".forgepy/build/meson"
                    build_dir_rel = str(args[1] if len(args) > 1 else default_dir)
                    build_dir = (root / build_dir_rel).resolve()
                    if not _within(root, build_dir):
                        print(f"[FAIL] Build directory escapes project root: {build_dir_rel}")
                        return 2
                    op_cwd = command_cwd(root, cmd)
                    print(f"[INFO] {cmd.get('label') or cmd.get('key')} [{cmd.get('_source', 'project')}]")
                    stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
                    log_path = state_dir(root) / "logs" / f"{stamp}-{internal}.log"
                    timeout = command_timeout(root, cmd)
                    if internal == "cmake-build":
                        code = stream([resolve_program("cmake"), "-S", ".", "-B", str(build_dir)], op_cwd, log_path, timeout=timeout)
                        if code == 0:
                            code = stream([resolve_program("cmake"), "--build", str(build_dir)], op_cwd, log_path, append=True, timeout=timeout)
                    else:
                        if not (build_dir / "build.ninja").exists():
                            code = stream([resolve_program("meson"), "setup", str(build_dir), "."], op_cwd, log_path, timeout=timeout)
                        else:
                            code = 0
                        if code == 0:
                            code = stream([resolve_program("meson"), "compile", "-C", str(build_dir)], op_cwd, log_path, append=True, timeout=timeout)
                    print(f"[{'PASS' if code == 0 else 'FAIL'}] {cmd.get('key')} exit={code}")
                    record_evidence(root, cmd, code, started, log_path)
                    return code
                print(f"[FAIL] unknown internal operation: {internal}")
                return 2
            stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
            log_path = state_dir(root) / "logs" / f"{stamp}-{str(cmd.get('key')).replace('.', '-')}.log"
            print(f"[INFO] {cmd.get('label') or cmd.get('key')} [{cmd.get('_source', 'project')}]")
            try:
                op_cwd = command_cwd(root, cmd)
            except ValueError as exc:
                print(f"[FAIL] {exc}")
                code = 2
                record_evidence(root, cmd, code, started, log_path)
                return code
            code = stream(argv_for(root, cmd), op_cwd, log_path, timeout=command_timeout(root, cmd))
            print(f"[{'PASS' if code == 0 else 'FAIL'}] {cmd.get('key')} exit={code}")
            record_evidence(root, cmd, code, started, log_path)
            return code
    except RuntimeError as exc:
        print(f"[FAIL] {exc}")
        return 75

def write_green_receipt(root: Path, data: dict[str, Any], operations: list[str], started: float | None = None) -> None:
    gs = git_status(root)
    receipt = {
        "schema": "forgepy.green.v3",
        "result": "GREEN",
        "createdUtc": datetime.now(timezone.utc).isoformat(),
        "projectId": (data.get("project") or {}).get("id", safe_slug(root.name)),
        "projectUuid": (data.get("project") or {}).get("uuid", ""),
        "projectName": (data.get("project") or {}).get("name", root.name),
        "runtimeBuild": BUILD,
        "runtimeVersion": VERSION,
        "branch": gs.get("branch"),
        "head": gs.get("head"),
        "sourceFingerprint": source_fingerprint(root),
        "operations": operations,
        "operationEvidence": list(_OP_EVIDENCE),
    }
    if started is not None:
        receipt["durationSeconds"] = round(max(0.0, time.monotonic() - started), 3)
    atomic_json(state_dir(root) / "last-green.json", receipt)
    atomic_json(state_dir(root) / "last-gate.json", receipt)
    with contextlib.suppress(FileNotFoundError):
        (state_dir(root) / "last-failure.json").unlink()
    print("[PASS] Full gate GREEN receipt written.")

def write_failure_receipt(root: Path, data: dict[str, Any], code: int, started: float, operations: list[str]) -> None:
    receipt = {
        "schema": "forgepy.gate.failure.v1",
        "result": "FAIL",
        "createdUtc": datetime.now(timezone.utc).isoformat(),
        "projectId": (data.get("project") or {}).get("id", safe_slug(root.name)),
        "projectUuid": (data.get("project") or {}).get("uuid", ""),
        "projectName": (data.get("project") or {}).get("name", root.name),
        "runtimeBuild": BUILD,
        "runtimeVersion": VERSION,
        "exitCode": int(code),
        "durationSeconds": round(max(0.0, time.monotonic() - started), 3),
        "operations": operations,
        "operationEvidence": list(_OP_EVIDENCE),
        "sourceFingerprint": source_fingerprint(root),
    }
    atomic_json(state_dir(root) / "last-failure.json", receipt)
    atomic_json(state_dir(root) / "last-gate.json", receipt)


def certify_full(root: Path, data: dict[str, Any]) -> int:
    cmd = find_command(data, "full")
    if not cmd:
        print("[FAIL] Full gate unavailable.")
        return 2
    try:
        with operation_lock(root, "certify-full"):
            _OP_EVIDENCE.clear()
            started = time.monotonic()
            code = run_operation(root, data, "full")
            operations = [str(x.get("key") or "") for x in _OP_EVIDENCE] or [str(cmd.get("key") or "gate.full")]
            if code == 0:
                write_green_receipt(root, data, operations, started)
            else:
                write_failure_receipt(root, data, code, started, operations)
                print(f"[FAIL] Full gate failure receipt written (exit={code}).")
            return code
    except RuntimeError as exc:
        print(f"[FAIL] {exc}")
        return 75

def composite_category(root: Path, data: dict[str, Any], category: str) -> int:
    candidates = [x for x in data.get("commands", []) if isinstance(x, dict)]
    ordered: list[dict[str, Any]] = []
    seen_impl: set[tuple[str, str, tuple[str, ...]]] = set()
    for cmd in candidates:
        if str(cmd.get("category", "")).casefold() != category.casefold():
            continue
        if cmd.get("_defaultAlias") or cmd.get("_composite"):
            continue
        key = str(cmd.get("key", "")).casefold()
        if key in {"gate.full", "build.full", "quality.full"} or key.startswith("build-release.") or key == "build.release":
            continue
        args = tuple(str(x) for x in (cmd.get("args") or []))
        if cmd.get("program") == "__forgepy_internal__" and args[:1] in {("composite-full",), ("composite-category",)}:
            continue
        impl = (str(cmd.get("program") or ""), str(cmd.get("cwd") or "."), args)
        if impl in seen_impl:
            continue
        seen_impl.add(impl)
        ordered.append(cmd)
    if not ordered:
        print(f"[FAIL] No {category} operations were discovered.")
        return 2
    print(f"[INFO] ForgePY composite {category}: {len(ordered)} operation(s)")
    for cmd in ordered:
        code = run_operation(root, {"commands": [cmd]}, str(cmd["key"]))
        if code != 0:
            print(f"[FAIL] Composite {category} stopped at {cmd['key']}")
            return code
    return 0


def composite_full(root: Path, data: dict[str, Any]) -> int:
    # Run unique component operations in gate → build → test order. Default aliases are
    # presentation/semantic dispatchers and are deliberately not executed a second time.
    ordered: list[dict[str, Any]] = []
    seen_impl: set[tuple[str, str, tuple[str, ...]]] = set()
    for category in ("gate", "build", "test"):
        for cmd in [x for x in data.get("commands", []) if isinstance(x, dict)]:
            if str(cmd.get("category", "")).casefold() != category:
                continue
            if cmd.get("_defaultAlias") or cmd.get("_composite"):
                continue
            key = str(cmd.get("key", "")).casefold()
            args = tuple(str(x) for x in (cmd.get("args") or []))
            if key in {"gate.full", "build.full", "quality.full"} or key.startswith("build-release.") or key == "build.release":
                continue
            if cmd.get("program") == "__forgepy_internal__" and args[:1] in {("composite-full",), ("composite-category",)}:
                continue
            impl = (str(cmd.get("program") or ""), str(cmd.get("cwd") or "."), args)
            if impl in seen_impl:
                continue
            seen_impl.add(impl)
            ordered.append(cmd)
    if not ordered:
        print("[FAIL] No build/test/check operations were discovered.")
        return 2
    print(f"[INFO] ForgePY composite full gate: {len(ordered)} operation(s)")
    for cmd in ordered:
        code = run_operation(root, {"commands": [cmd]}, str(cmd["key"]))
        if code != 0:
            print(f"[FAIL] Full gate stopped at {cmd['key']}")
            return code
    return 0

def patch_candidates(root: Path, *, include_hash: bool = False) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    max_hash = int(load_policy(root).get("genericPatchMaxBytes") or 128 * 1024 * 1024)
    for p in sorted(root.iterdir()):
        if not p.is_file() or p.is_symlink():
            continue
        low = p.name.casefold()
        if p.suffix.casefold() == ".patch" or (p.suffix.casefold() == ".zip" and any(x in low for x in ("patch", "update", "handoff", "root_drop", "root-drop"))):
            size = p.stat().st_size
            kind = "unified-diff" if p.suffix.casefold() == ".patch" else "transport-zip"
            digest = sha256_file(p) if include_hash and kind == "unified-diff" and size <= max_hash else None
            out.append({
                "path": p.name, "bytes": size, "sha256": digest,
                "hashStatus": "ready" if digest else ("deferred" if kind == "unified-diff" else "not-required"),
                "kind": kind,
            })
    return out

def _patch_intake_names(root: Path) -> set[str]:
    return {str(x["path"]).replace("\\", "/") for x in patch_candidates(root, include_hash=False)}


def git_clean_except_intake(root: Path) -> tuple[bool, list[str]]:
    if not git_available(root):
        return False, ["Git repository unavailable"]
    intake = _patch_intake_names(root)
    volatile = volatile_runtime_prefixes(root)
    blockers: list[str] = []
    for code, rel, original in git_porcelain_entries(root):
        paths = [rel] + ([original] if original else [])
        if code == "??" and all(p in intake or p.startswith(volatile) for p in paths if p):
            continue
        if all(p and p.startswith(volatile) for p in paths):
            continue
        blockers.append(f"{code} {rel}" + (f" <- {original}" if original else ""))
    return not blockers, blockers

def _patch_touched_paths(path: Path) -> list[str]:
    touched: set[str] = set()
    def add(raw: str) -> None:
        raw = raw.strip()
        if not raw or raw == "/dev/null":
            return
        try:
            vals = shlex.split(raw)
            value = vals[0] if vals else raw
        except ValueError:
            value = raw.split("\t", 1)[0].strip('"')
        value = value.split("\t", 1)[0]
        if value.startswith("a/") or value.startswith("b/"):
            value = value[2:]
        if value and value != "/dev/null":
            touched.add(value.replace("\\", "/"))
    try:
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.startswith("diff --git "):
                try:
                    parts = shlex.split(line)
                except ValueError:
                    parts = line.split(" ")
                for value in parts[2:4]:
                    add(value)
            elif line.startswith(("--- ", "+++ ")):
                add(line[4:])
            elif line.startswith(("rename from ", "rename to ", "copy from ", "copy to ")):
                add(line.split(" ", 2)[2])
    except OSError:
        return []
    return sorted(touched)

def _generic_patch_policy(root: Path, path: Path) -> tuple[bool, str]:
    try:
        if path.is_symlink():
            return False, "symbolic-link patch inputs are rejected to prevent time-of-check/time-of-use substitution"
        resolved = path.resolve(strict=True)
    except OSError as exc:
        return False, f"patch file is unavailable: {exc}"
    if resolved.suffix.casefold() != ".patch":
        return False, "Universal portable mode only validates raw .patch files; ZIP transports require a project-owned provider."
    max_bytes = int(load_policy(root).get("genericPatchMaxBytes") or 128 * 1024 * 1024)
    if resolved.stat().st_size > max_bytes:
        return False, f"patch exceeds the {max_bytes} byte generic safety limit"
    protected = {
        ".git/", ".forgepy/runtime/", ".forgepy/package/", ".forgepy/adapters/", ".forgepy/pcc.json", ".forgepy/policy.json",
        ".forgepy/runtime.lock", ".forgepy/.gitignore", ".forgepy/project.identity.json", ".forgepy/gui/", ".pcc/",
        "project.control.json", "forgepy.cmd", "forgepy-gui.cmd", "forgepy-install.cmd", "forgepy-verify.cmd", "project_control_center.cmd",
    }
    touched = _patch_touched_paths(resolved)
    if not touched:
        return False, "patch touched-path set could not be determined safely"
    for rel in touched:
        low = rel.casefold()
        if any(low == p.rstrip("/") or low.startswith(p) for p in protected):
            return False, f"generic project patch may not modify protected ForgePY/Git control path: {rel}"
        candidate = (root / rel).resolve()
        if not _within(root, candidate):
            return False, f"patch path escapes project root: {rel}"
    return True, ""

def generic_patch_check(root: Path, path: Path) -> int:
    ok, reason = _generic_patch_policy(root, path)
    if not ok:
        print(f"[FAIL] {reason}")
        return 2
    if not git_available(root):
        print("[FAIL] Git is required for generic patch validation.")
        return 2
    cp = git(root, "apply", "--check", "--whitespace=error-all", str(path.resolve()))
    print(cp.stdout, end="")
    print("[PASS] Patch applies cleanly." if cp.returncode == 0 else "[FAIL] Patch precheck failed.")
    return cp.returncode


def archive_applied_patch(root: Path, path: Path, before_head: str, touched: list[str]) -> Path:
    digest = sha256_file(path)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    dest_dir = root / ".forgepy" / "artifacts" / "patches" / "applied" / f"{stamp}-{digest[:12]}"
    dest_dir.mkdir(parents=True, exist_ok=False)
    dest = dest_dir / path.name
    tracked = False
    if _within(root, path.resolve()) and git_available(root):
        try:
            rel = str(path.resolve().relative_to(root)).replace("\\", "/")
            tracked = git(root, "ls-files", "--error-unmatch", "--", rel).returncode == 0
        except ValueError:
            tracked = False
    if _within(root, path.resolve()) and not tracked:
        shutil.move(str(path), str(dest))
    else:
        shutil.copy2(path, dest)
    atomic_json(dest_dir / "receipt.json", {
        "schema": "forgepy.patch.receipt.v1",
        "appliedUtc": datetime.now(timezone.utc).isoformat(),
        "sha256": digest,
        "originalName": path.name,
        "beforeHead": before_head,
        "touchedPaths": touched,
        "runtimeBuild": BUILD,
    })
    return dest


def generic_patch_apply(root: Path, path: Path) -> int:
    try:
        with operation_lock(root, f"patch-apply:{path.name}"):
            ok, reason = _generic_patch_policy(root, path)
            if not ok:
                print(f"[FAIL] {reason}")
                return 2
            st = git_status(root)
            if not st.get("ready"):
                print("[FAIL] Git repository required for generic patch application.")
                return 2
            clean, blockers = git_clean_except_intake(root)
            if not clean:
                print("[FAIL] Generic patch application requires source/index cleanliness; intake patch files are ignored for this check.")
                for line in blockers[:20]: print(f"       {line}")
                return 2
            digest_before = sha256_file(path)
            fingerprint_before = source_fingerprint(root)
            code = generic_patch_check(root, path)
            if code != 0:
                return code
            if sha256_file(path) != digest_before:
                print("[FAIL] Patch changed after precheck; refusing application.")
                return 2
            if source_fingerprint(root) != fingerprint_before:
                print("[FAIL] Project source changed during patch precheck; refusing application.")
                return 2
            touched = _patch_touched_paths(path)
            before_head = str(st.get("head") or "")
            cp = git(root, "apply", "--whitespace=error-all", str(path.resolve()))
            print(cp.stdout, end="")
            if cp.returncode == 0:
                archived = archive_applied_patch(root, path, before_head, touched)
                receipt = read_json(archived.parent / "receipt.json", {}) or {}
                receipt.update({"sourceFingerprintBefore": fingerprint_before, "sourceFingerprintAfter": source_fingerprint(root)})
                atomic_json(archived.parent / "receipt.json", receipt)
                print(f"[PASS] Patch applied and archived for lineage: {archived.relative_to(root)}")
                print("[INFO] Changes remain uncommitted until a Full Gate certifies them.")
            return cp.returncode
    except RuntimeError as exc:
        print(f"[FAIL] {exc}")
        return 75

def package_manifest_path(root: Path) -> Path:
    return root / ".forgepy" / "package" / "manifest.json"


def verify_package(root: Path, *, verbose: bool = True) -> int:
    manifest = read_json(package_manifest_path(root))
    if not isinstance(manifest, dict):
        if verbose: print("[WARN] ForgePY package manifest is missing or invalid; integrity cannot be verified.")
        return 2
    failures = 0
    if manifest.get("product") != PRODUCT or manifest.get("version") != VERSION or manifest.get("build") != BUILD:
        if verbose: print("[FAIL] package manifest identity does not match running runtime")
        failures += 1
    items = manifest.get("files", [])
    if not isinstance(items, list):
        if verbose: print("[FAIL] package manifest files must be an array")
        return 1
    seen: set[str] = set()
    for item in items:
        if not isinstance(item, dict) or not item.get("path") or not item.get("sha256"):
            failures += 1
            continue
        rel = str(item["path"]).replace("\\", "/")
        if rel in seen:
            if verbose: print(f"[FAIL] duplicate package manifest path: {rel}")
            failures += 1
            continue
        seen.add(rel)
        mode = str(item.get("hashMode") or "raw")
        if mode not in {"raw", "text-lf"}:
            if verbose: print(f"[FAIL] unsupported hash mode for {rel}: {mode}")
            failures += 1
            continue
        raw_path = root / rel
        if raw_path.is_symlink():
            if verbose: print(f"[FAIL] package file may not be a symlink: {rel}")
            failures += 1
            continue
        path = raw_path.resolve()
        if not _within(root, path) or not path.is_file():
            if verbose: print(f"[FAIL] package file missing/unsafe: {rel}")
            failures += 1
            continue
        actual = package_hash(path, mode)
        if actual != str(item["sha256"]):
            if verbose: print(f"[FAIL] package hash mismatch: {rel}")
            failures += 1
    declared_count = manifest.get("fileCountExcludingManifest")
    if isinstance(declared_count, int) and declared_count != len(items):
        if verbose: print(f"[FAIL] package file-count mismatch: declared={declared_count} actual={len(items)}")
        failures += 1
    if verbose: print(f"[{'PASS' if failures == 0 else 'FAIL'}] ForgePY package integrity: {failures} failure(s)")
    return 1 if failures else 0

def status_payload(root: Path, data: dict[str, Any]) -> dict[str, Any]:
    source_clean, blockers = git_clean_except_intake(root) if git_available(root) else (False, [])
    sdir = state_dir(root)
    last_gate = read_json(sdir / "last-gate.json", {}) or {}
    last_green = read_json(sdir / "last-green.json", {}) or {}
    last_failure = read_json(sdir / "last-failure.json", {}) or {}
    lock = read_json(sdir / "operation.lock", {}) if (sdir / "operation.lock").exists() else {}
    green_current = False
    if last_green.get("sourceFingerprint") and git_available(root):
        with contextlib.suppress(Exception):
            green_current = source_fingerprint(root) == last_green.get("sourceFingerprint")
    return {
        "schema": "forgepy.universal.status.v4",
        "runtime": {
            "product": PRODUCT, "version": VERSION, "build": BUILD, "contract": CONTRACT,
            "donorBuild": DONOR_BUILD, "donorCommit": DONOR_COMMIT, "gui": True,
        },
        "project": data.get("project"),
        "identity": load_project_identity(root),
        "discovery": data.get("_pccDiscovery"),
        "provider": data.get("_provider"),
        "capabilities": data.get("capabilities") or discover_capabilities(root, data),
        "git": git_status(root), "sourceClean": source_clean, "sourceBlockers": blockers[:20],
        "operations": len(data.get("commands", [])), "patchCandidates": len(patch_candidates(root)), "root": str(root),
        "greenCurrent": green_current,
        "lastGreen": {k: last_green.get(k) for k in ("result", "createdUtc", "durationSeconds", "runtimeBuild", "projectUuid") if k in last_green},
        "lastGate": {k: last_gate.get(k) for k in ("result", "createdUtc", "exitCode", "durationSeconds", "runtimeBuild") if k in last_gate},
        "lastFailure": {k: last_failure.get(k) for k in ("result", "createdUtc", "exitCode", "durationSeconds", "runtimeBuild") if k in last_failure},
        "operationLock": lock or None,
        "scan": {
            "schema": (data.get("_scanPlan") or {}).get("schema"),
            "signature": (data.get("_scanPlan") or {}).get("signature"),
            "cacheHit": bool((data.get("_scanPlan") or {}).get("cacheHit")),
            "markerCount": int((data.get("_scanPlan") or {}).get("markerCount") or 0),
            "componentCount": int((data.get("_scanPlan") or {}).get("componentCount") or 0),
            "kinds": list((data.get("_scanPlan") or {}).get("kinds") or []),
            "warnings": list((data.get("_scanPlan") or {}).get("warnings") or []),
            "unresolved": list((data.get("_scanPlan") or {}).get("unresolved") or []),
        },
    }


def onboarding_plan_path(root: Path) -> Path:
    return state_dir(root) / "onboarding.plan.json"


def persist_onboarding_plan(root: Path, plan: dict[str, Any]) -> None:
    atomic_json(onboarding_plan_path(root), plan)


def snapshot_payload(root: Path, data: dict[str, Any], *, include_patch_hash: bool = False, history_count: int = 20) -> dict[str, Any]:
    return {
        "schema": "forgepy.snapshot.v1",
        "status": status_payload(root, data),
        "operations": data.get("commands", []),
        "patches": patch_candidates(root, include_hash=include_patch_hash),
        "gitHistory": git_history(root, history_count),
        "buildPlan": data.get("_scanPlan") or repository_scan(root),
    }


def write_scan_adapter(root: Path, *, overwrite_generated: bool = False) -> Path:
    path = root / ".forgepy" / "adapters" / "project.control.json"
    if path.exists() and not overwrite_generated:
        existing = read_json(path, {}) or {}
        if existing.get("generatedBy") != BUILD:
            raise RuntimeError(f"Refusing to overwrite existing project adapter: {path}")
    plan = repository_scan(root, force=True)
    commands = [dict(x) for x in plan.get("operations", []) if isinstance(x, dict)]
    for row in commands:
        row.pop("_provider", None)
        row.pop("_source", None)
        row.pop("_component", None)
    payload = {
        "schema": "forge.project.v1",
        "provider": {"type": "forgepy-adapter", "name": "ForgePY Generated Project Adapter"},
        "project": {"id": safe_slug(root.name), "name": root.name, "kind": "-".join(plan.get("kinds") or []) or "generic"},
        "commands": commands,
        "generatedBy": BUILD,
        "sourceScanSignature": plan.get("signature"),
    }
    atomic_json(path, payload)
    return path

def debug_bundle(root: Path, payload: dict[str, Any]) -> Path:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    out = root / ".forgepy" / "artifacts" / "debug" / f"ForgePY_DebugBundle_{stamp}.zip"
    out.parent.mkdir(parents=True, exist_ok=True)
    state = state_dir(root)
    meta = {
        "schema": "forgepy.debug_bundle.v1", "createdUtc": datetime.now(timezone.utc).isoformat(),
        "projectRoot": str(root), "python": sys.version, "platform": platform.platform(),
        "status": payload, "gitHistory": git_history(root, 8),
    }
    meta_path = state / "debug-metadata.json"
    atomic_json(meta_path, meta)
    safe_files = ("project.control.json", "pyproject.toml", "Cargo.toml", "package.json", "CMakeLists.txt", "requirements.txt", ".gitignore", "README.md", "README.txt")
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(meta_path, "debug-metadata.json")
        for name in safe_files:
            p = root / name
            if p.is_file(): z.write(p, f"project/{name}")
        logs = state / "logs"
        if logs.is_dir():
            for p in sorted(logs.glob("*.log"))[-8:]: z.write(p, f"logs/{p.name}")
        for name in ("generated.project.control.json", "last-green.json"):
            p = state / name
            if p.is_file(): z.write(p, name)
    return out


def commit_green(root: Path, message: str | None = None) -> int:
    try:
        with operation_lock(root, "commit-green"):
            receipt = state_dir(root) / "last-green.json"
            data = read_json(receipt)
            if not isinstance(data, dict):
                print("[FAIL] No GREEN receipt. Run a successful generated full gate first.")
                return 2
            current = source_fingerprint(root)
            if not current or current != data.get("sourceFingerprint"):
                print("[FAIL] Source changed since the GREEN receipt.")
                return 2
            cp = git(root, "add", "-A")
            if cp.returncode != 0:
                print(cp.stdout, end="")
                return cp.returncode
            for item in patch_candidates(root):
                git(root, "reset", "--", str(item["path"]))
            unstage = {".forgepy/state", ".forgepy/artifacts", ".forgepy/build", ".forgepy/cache", ".forgepy/runtime/__pycache__"}
            for prefix in volatile_runtime_prefixes(root): unstage.add(prefix.rstrip("/"))
            for rel in sorted(unstage): git(root, "reset", "--", rel)
            quiet = git(root, "diff", "--cached", "--quiet")
            if quiet.returncode == 0:
                print("[PASS] GREEN receipt is current; nothing needs committing.")
                return 0
            msg = message or f"GREEN {data.get('projectName', root.name)} - ForgePY Full Gate"
            cp = git(root, "commit", "-m", msg)
            print(cp.stdout, end="")
            return cp.returncode
    except RuntimeError as exc:
        print(f"[FAIL] {exc}")
        return 75

def persist_generated(root: Path, data: dict[str, Any]) -> None:
    atomic_json(state_dir(root) / "generated.project.control.json", data)


def doctor(root: Path, data: dict[str, Any]) -> int:
    failures = 0
    print(f"[PASS] Runtime: {PRODUCT} {VERSION} ({BUILD})")
    print(f"[PASS] Python: {sys.version.split()[0]} — {sys.executable}")
    print(f"[PASS] Root: {root}")
    try:
        scan = repository_scan(root)
        print(f"[PASS] Discovery: {scan.get('componentCount', 0)} component(s), {len(scan.get('operations') or [])} synthesized operation(s), cache={'hit' if scan.get('cacheHit') else 'fresh'}")
        for issue in scan.get("warnings") or []:
            print(f"[WARN] Discovery: {issue}")
        for issue in scan.get("unresolved") or []:
            if isinstance(issue, dict):
                print(f"[INFO] Discovery unresolved: {issue.get('message')}")
    except Exception as exc:
        print(f"[FAIL] Repository discovery scan failed: {exc}"); failures += 1
    if sys.version_info < (3, 10):
        print("[FAIL] Python 3.10+ is required."); failures += 1
    try:
        probe = state_dir(root) / ".write-probe"
        probe.write_text("ok", encoding="utf-8"); probe.unlink()
        print(f"[PASS] State directory writable: {state_dir(root)}")
    except Exception as exc:
        print(f"[FAIL] State directory is not writable: {exc}"); failures += 1
    try:
        free = shutil.disk_usage(root).free
        print(f"[PASS] Disk free: {free / (1024**3):.2f} GiB")
        if free < 512 * 1024 * 1024:
            print("[WARN] Less than 512 MiB free space may break builds/patch archival.")
    except OSError as exc:
        print(f"[WARN] Disk-space probe failed: {exc}")
    ppython = project_python(root)
    print(f"[PASS] Project Python: {ppython}")
    gui_path = root / ".forgepy" / "gui" / "pcc_gui.py"
    if gui_path.is_file():
        try:
            compile(gui_path.read_text(encoding="utf-8-sig"), str(gui_path), "exec")
            print(f"[PASS] PCC GUI source: {gui_path.relative_to(root)}")
        except Exception as exc:
            print(f"[FAIL] PCC GUI source invalid: {exc}"); failures += 1
    else:
        print("[FAIL] PCC GUI source missing."); failures += 1
    try:
        import tkinter  # noqa: F401
        print("[PASS] Tk GUI runtime available")
    except Exception as exc:
        print(f"[WARN] Tk GUI runtime unavailable; console PCC fallback remains usable: {exc}")
    try:
        ident = load_project_identity(root)
        if ident:
            print(f"[PASS] Project UUID: {ident.get('uuid')}")
        else:
            print("[INFO] Project identity not initialized yet; run ForgePY init/install once.")
    except Exception as exc:
        print(f"[FAIL] Project identity invalid: {exc}"); failures += 1
    if git_available(root):
        ver = git(root, "--version").stdout.strip()
        print(f"[PASS] Git: {ver or 'available'}")
    else:
        print("[WARN] Git repository/tool unavailable; patch and GREEN commit workflows are limited.")
    contract = explicit_contract_path(root)
    if contract:
        try:
            load_explicit(root); print(f"[PASS] {contract.relative_to(root)} parses and validates")
        except Exception as exc:
            print(f"[FAIL] project contract invalid: {exc}"); failures += 1
    else:
        print("[INFO] No explicit project contract; generated discovery is active.")
    tool_rows: dict[tuple[str, str], set[str]] = {}
    tool_commands = [x for x in data.get("commands", []) if isinstance(x, dict)] + generated_commands(root)
    for c in tool_commands:
        p = str(c.get("program", "")).strip()
        if not p or p.startswith("__"):
            continue
        cwd = str(c.get("cwd") or ".")
        tool_rows.setdefault((p, cwd), set()).add(str(c.get("category", "")))
    for (tool, cwd), categories in sorted(tool_rows.items()):
        if tool == "__forgepy_internal__":
            continue
        try:
            work = command_cwd(root, {"cwd": cwd})
        except ValueError:
            work = root
        candidate_cwd = work / tool
        candidate_root = root / tool
        low = tool.casefold()
        ok = (
            low in {"python", "python.exe", "python3"}
            or candidate_cwd.is_file()
            or candidate_root.is_file()
            or (Path(tool).is_absolute() and Path(tool).is_file())
            or bool(shutil.which(tool))
        )
        # Shell/PowerShell wrappers additionally require their interpreter on this platform.
        suffix = Path(tool).suffix.casefold()
        if ok and suffix == ".sh":
            ok = bool(shutil.which("bash"))
        elif ok and suffix == ".ps1":
            ok = bool(shutil.which("pwsh") or shutil.which("powershell"))
        required = bool(categories & {"gate", "build", "build-release", "test"})
        level = "PASS" if ok else ("FAIL" if required else "WARN")
        where = f" @ {cwd}" if cwd not in {"", "."} else ""
        print(f"[{level}] tool {tool}{where}: {'available' if ok else 'not available'} ({','.join(sorted(categories)) or 'uncategorized'})")
        if not ok and required:
            failures += 1
    lock = state_dir(root) / "operation.lock"
    if lock.exists():
        info = read_json(lock, {}) or {}
        pid = int(info.get("pid") or 0) if str(info.get("pid") or "").isdigit() else 0
        if info.get("host") == socket.gethostname() and _pid_alive(pid):
            print(f"[WARN] Active ForgePY operation lock: pid={pid} label={info.get('label')}")
        else:
            print("[WARN] Stale/unverifiable ForgePY operation lock exists; next operation can reclaim it after policy age threshold.")
    if package_manifest_path(root).is_file():
        failures += 1 if verify_package(root) != 0 else 0
    print(f"[{'PASS' if failures == 0 else 'FAIL'}] Doctor complete.")
    return 1 if failures else 0

def self_test(root: Path) -> int:
    failures = 0
    try:
        data = merge_contract(root)
        assert data["schema"] == "forge.project.v1"
        print("[PASS] Contract discovery")
    except Exception as e:
        print(f"[FAIL] Contract discovery: {e}")
        failures += 1
    try:
        runtime_source = Path(__file__).read_text(encoding="utf-8-sig")
        compile(runtime_source, str(Path(__file__).resolve()), "exec")
        print("[PASS] Runtime syntax")
    except Exception as e:
        print(f"[FAIL] Runtime syntax: {e}")
        failures += 1
    try:
        gui_path = root / ".forgepy" / "gui" / "pcc_gui.py"
        gui_source = gui_path.read_text(encoding="utf-8-sig")
        compile(gui_source, str(gui_path), "exec")
        print("[PASS] GUI source syntax")
    except Exception as e:
        print(f"[FAIL] GUI source syntax: {e}")
        failures += 1
    try:
        with tempfile.TemporaryDirectory(prefix="forgepy-selftest-") as td:
            troot = Path(td)
            (troot / "app.py").write_text("print('ok')\n", encoding="utf-8")
            generated = merge_contract(troot)
            assert find_command(generated, "full") is not None
            assert find_command(generated, "build") is not None
            assert (generated.get("_scanPlan") or {}).get("componentCount", 0) >= 1
            assert python_syntax_check(troot) == 0
        print("[PASS] Synthetic Python project discovery")
    except Exception as e:
        print(f"[FAIL] Synthetic project discovery: {e}")
        failures += 1
    if package_manifest_path(root).is_file():
        if verify_package(root, verbose=False) == 0:
            print("[PASS] Package manifest integrity")
        else:
            print("[FAIL] Package manifest integrity")
            failures += 1
    print(f"[{'PASS' if failures == 0 else 'FAIL'}] ForgePY standalone self-test.")
    return 1 if failures else 0


def ensure_runtime_gitignore(root: Path) -> None:
    path = root / ".forgepy" / ".gitignore"
    required = ["state/", "artifacts/", "build/", "cache/", "__pycache__/", "runtime/__pycache__/", "tests/__pycache__/"]
    if path.exists():
        text = path.read_text(encoding="utf-8", errors="replace")
        existing = {line.strip() for line in text.splitlines()}
        missing = [x for x in required if x not in existing]
        if not missing:
            return
        with path.open("a", encoding="utf-8", newline="\n") as f:
            if text and not text.endswith(("\n", "\r")):
                f.write("\n")
            f.write("# ForgePY volatile runtime state\n")
            for item in missing:
                f.write(item + "\n")
        print(f"[PASS] Extended .forgepy/.gitignore with {len(missing)} ForgePY runtime rule(s).")
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# ForgePY volatile runtime state\n" + "\n".join(required) + "\n", encoding="utf-8")
        print("[PASS] Created .forgepy/.gitignore")


def default_pcc_launcher_text() -> str:
    return (
        '@echo off\r\n'
        'setlocal EnableExtensions\r\n'
        'rem ForgePY-owned launcher: forgepy.pcc.launcher.v5\r\n'
        'cd /d "%~dp0"\r\n'
        'if /I "%~1"=="--cli" goto cli\r\n'
        'if "%~1"=="" (\r\n'
        '  call "%~dp0ForgePY-GUI.cmd"\r\n'
        '  exit /b %errorlevel%\r\n'
        ')\r\n'
        'call "%~dp0ForgePY.cmd" %*\r\n'
        'exit /b %errorlevel%\r\n'
        ':cli\r\n'
        'shift\r\n'
        'call "%~dp0ForgePY.cmd" menu %*\r\n'
        'exit /b %errorlevel%\r\n'
    )


def _legacy_forgepy_launcher(text: str) -> bool:
    normalized = text.replace('\r\n', '\n').strip()
    legacy = '''@echo off
setlocal EnableExtensions
cd /d "%~dp0"
if "%~1"=="" (
  call "%~dp0ForgePY.cmd" menu
) else (
  call "%~dp0ForgePY.cmd" %*
)
exit /b %errorlevel%'''.strip()
    return normalized == legacy or 'ForgePY-owned launcher: forgepy.pcc.launcher.v5' in normalized or 'ForgePY-owned launcher: forgepy.pcc.launcher.v4' in normalized


def init_repo(root: Path) -> int:
    try:
        with operation_lock(root, 'init'):
            fp = root / '.forgepy'
            for name in ('state', 'artifacts', 'build', 'cache', 'adapters'):
                (fp / name).mkdir(parents=True, exist_ok=True)
            ensure_runtime_gitignore(root)
            scan = repository_scan(root, force=True)
            persist_onboarding_plan(root, scan)
            print(f"[PASS] Repository scan: {scan.get('componentCount', 0)} component(s), {len(scan.get('operations') or [])} synthesized operation(s), {scan.get('markerCount', 0)} marker(s).")
            for issue in (scan.get("warnings") or []) + [str(x.get("message")) for x in (scan.get("unresolved") or []) if isinstance(x, dict)]:
                print(f"[INFO] Discovery: {issue}")
            preliminary = merge_contract(root)
            identity = ensure_project_identity(root, str((preliminary.get('project') or {}).get('name') or root.name))
            print(f"[PASS] Project identity: {identity.get('uuid')}")
            pcc = root / 'PROJECT_CONTROL_CENTER.cmd'
            if not pcc.exists():
                pcc.write_text(default_pcc_launcher_text(), encoding='utf-8', newline='')
                print('[PASS] Created GUI-first PROJECT_CONTROL_CENTER.cmd')
            else:
                text = pcc.read_text(encoding='utf-8', errors='replace')
                if _legacy_forgepy_launcher(text):
                    pcc.write_text(default_pcc_launcher_text(), encoding='utf-8', newline='')
                    print('[PASS] Upgraded ForgePY-owned PROJECT_CONTROL_CENTER.cmd to GUI-first launcher.')
                else:
                    print('[INFO] Existing project-owned PROJECT_CONTROL_CENTER.cmd preserved.')
            data = merge_contract(root)
            persist_generated(root, data)
            print('[PASS] ForgePY project-local state initialized.')
            return 0
    except RuntimeError as exc:
        print(f"[FAIL] {exc}")
        return 75


def git_pull_ff_only(root: Path) -> int:
    try:
        with operation_lock(root, "git-pull"):
            st = git_status(root)
            if not st.get("ready"):
                print("[FAIL] Git repository unavailable.")
                return 2
            clean, blockers = git_clean_except_intake(root)
            if not clean:
                print("[FAIL] Refusing pull with source/index changes.")
                for line in blockers[:20]: print(f"       {line}")
                return 2
            return stream([shutil.which("git") or "git", "-C", str(root), "pull", "--ff-only"], root, timeout=600)
    except RuntimeError as exc:
        print(f"[FAIL] {exc}")
        return 75

def git_push_safe(root: Path) -> int:
    try:
        with operation_lock(root, "git-push"):
            st = git_status(root)
            if not st.get("ready"):
                print("[FAIL] Git repository unavailable.")
                return 2
            if not st.get("branch"):
                print("[FAIL] Refusing push from detached HEAD.")
                return 2
            upstream = git(root, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}")
            if upstream.returncode != 0:
                print("[FAIL] Current branch has no upstream; configure it explicitly before ForgePY pushes.")
                return 2
            return stream([shutil.which("git") or "git", "-C", str(root), "push"], root, timeout=600)
    except RuntimeError as exc:
        print(f"[FAIL] {exc}")
        return 75

def interactive_patch_intake(root: Path, data: dict[str, Any]) -> None:
    candidates = patch_candidates(root, include_hash=True)
    if not candidates:
        return
    print(f"\n[PATCH] {len(candidates)} root intake candidate(s) found.")
    for i, item in enumerate(candidates, 1):
        digest = str(item.get("sha256") or "hash-deferred")[:12]
        print(f"  {i}. {item['path']}  {item['kind']}  {digest}")
    if not sys.stdin.isatty():
        print("[INFO] Non-interactive session: no patch is applied automatically.")
        return
    answer = input("Review/apply an intake patch now? [y/N]: ").strip().casefold()
    if answer not in {"y", "yes"}:
        return
    if len(candidates) == 1:
        selected = candidates[0]
    else:
        raw = input("Patch number: ").strip()
        if not raw.isdigit() or not 1 <= int(raw) <= len(candidates):
            print("[WARN] Invalid selection; intake left untouched.")
            return
        selected = candidates[int(raw) - 1]
    path = root / str(selected["path"])
    declared = find_command(data, "patch-apply")
    if declared and declared.get("_source") == "explicit":
        print("[INFO] Project-owned patch provider is authoritative; use its patch workflow from the menu/CLI.")
        return
    if path.suffix.casefold() != ".patch":
        print("[INFO] ZIP transport is retained for the project-owned provider; generic ForgePY will not unpack/apply it.")
        return
    if generic_patch_check(root, path) != 0:
        return
    confirm = input("Patch precheck passed. Apply it and archive the intake file? [y/N]: ").strip().casefold()
    if confirm in {"y", "yes"}:
        generic_patch_apply(root, path)


def menu(root: Path, data: dict[str, Any]) -> int:
    interactive_patch_intake(root, data)
    while True:
        payload = status_payload(root, data)
        p = payload["project"] or {}
        g = payload["git"] or {}
        print("\n" + "=" * 72)
        print(" FORGEPY PROJECT CONTROL CENTER")
        print("=" * 72)
        print(f" Project : {p.get('name')} [{p.get('kind')}] — {root}")
        if g.get("ready"):
            state = "clean" if g.get("clean") else ("source-clean + intake" if payload.get("sourceClean") else "modified")
            print(f" Git     : {g.get('branch') or '(detached)'} / {state} @ {str(g.get('head') or '')[:12]}")
        else:
            print(" Git     : unavailable/not initialized")
        print(f" Provider: {payload['discovery'].get('provider')} / {payload['discovery'].get('source')}")
        print(f" Patches : {payload['patchCandidates']} root intake candidate(s)")
        print("-" * 72)
        print(" 1. FULL QUALITY GATE / CERTIFY GREEN")
        print(" 2. QUICK GATE")
        print(" 3. BUILD")
        print(" 4. TEST")
        print(" 5. RUN")
        print(" 6. PATCH INTAKE / STATUS")
        print(" 7. DOCTOR + PACKAGE VERIFY")
        print(" 8. DEBUG BUNDLE")
        print(" 9. COMMIT CURRENT GREEN")
        print("10. PUSH (safe upstream only)")
        print("11. PULL (fast-forward only)")
        print("12. OPERATIONS")
        print(" 0. EXIT")
        print("=" * 72)
        if not sys.stdin.isatty():
            return 0
        choice = input("Select: ").strip()
        if choice == "0":
            return 0
        actions = {"2": "quick", "3": "build", "4": "test", "5": "run"}
        if choice == "1":
            certify_full(root, data)
        elif choice in actions:
            run_operation(root, data, actions[choice])
        elif choice == "6":
            print(json.dumps(patch_candidates(root, include_hash=True), indent=2))
            interactive_patch_intake(root, data)
        elif choice == "7":
            doctor(root, data)
        elif choice == "8":
            out = debug_bundle(root, status_payload(root, data)); print(f"[PASS] Debug bundle: {out}")
        elif choice == "9":
            commit_green(root)
        elif choice == "10":
            git_push_safe(root)
        elif choice == "11":
            git_pull_ff_only(root)
        elif choice == "12":
            for x in sorted(data.get("commands", []), key=lambda v: (str(v.get("category", "")), str(v.get("key", "")))):
                print(f"{str(x.get('key','')):24} {str(x.get('category','')):12} {str(x.get('risk','read')):6} {x.get('label','')} [{x.get('_source','project')}]")
        else:
            print("[WARN] Unknown selection.")
        data = merge_contract(root)
        persist_generated(root, data)


def serve_jsonl(root: Path) -> int:
    print(json.dumps({"ready": True, "schema": "forgepy.universal.jsonl.v2", "build": BUILD}), flush=True)
    for line in sys.stdin:
        try:
            req = json.loads(line)
            op = str(req.get("op") or "status")
            data = merge_contract(root)
            persist_generated(root, data)
            if op == "status": result = {"ok": True, "status": status_payload(root, data)}
            elif op == "operations": result = {"ok": True, "operations": data.get("commands", [])}
            elif op == "capabilities": result = {"ok": True, "capabilities": data.get("capabilities", [])}
            elif op == "identity": result = {"ok": True, "identity": data.get("project", {})}
            elif op == "patches": result = {"ok": True, "patches": patch_candidates(root, include_hash=bool(req.get("includeHash")))}
            elif op == "history": result = {"ok": True, "history": operation_history(root, int(req.get("count") or 100))}
            elif op == "scan": result = {"ok": True, "buildPlan": repository_scan(root, force=bool(req.get("force")))}
            elif op == "snapshot": result = {"ok": True, "snapshot": snapshot_payload(root, data, include_patch_hash=bool(req.get("includePatchHash")), history_count=int(req.get("historyCount") or 20))}
            elif op == "run":
                key = str(req.get("key") or "")
                with contextlib.redirect_stdout(sys.stderr):
                    code = certify_full(root, data) if key.casefold() in {"full", "gate.full", "build.full", "quality.full"} else run_operation(root, data, key)
                result = {"ok": code == 0, "exitCode": code}
            else: result = {"ok": False, "error": f"unknown op: {op}"}
        except Exception as e:
            result = {"ok": False, "error": str(e)}
        print(json.dumps(result), flush=True)
    return 0


def main(argv=None) -> int:
    normalize_stdio()
    if sys.version_info < (3, 10):
        print("[FAIL] ForgePY requires Python 3.10 or newer.")
        return 127
    ap = argparse.ArgumentParser(prog="ForgePY", description="Drop-in universal project control runtime")
    ap.add_argument("--root", default=None)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("command", nargs="?", default="status")
    ap.add_argument("extra", nargs="*")
    ns = ap.parse_args(argv)
    root = Path(ns.root or os.getcwd()).resolve()

    if ns.command == "init":
        try:
            return init_repo(root)
        except Exception as exc:
            print(f"[FAIL] ForgePY initialization failed: {exc}")
            return 2
    if ns.command == "runtime-self-test":
        return self_test(root)
    if ns.command == "serve-jsonl":
        return serve_jsonl(root)
    if ns.command == "package-verify":
        return verify_package(root)
    if ns.command == "gui":
        gui_path = root / ".forgepy" / "gui" / "pcc_gui.py"
        if not gui_path.is_file():
            print(f"[FAIL] PCC GUI source missing: {gui_path}")
            return 2
        return subprocess.call([sys.executable, str(gui_path), "--root", str(root)], cwd=str(root))

    # Repository scanning is intentionally available before contract merging so a scan is
    # one discovery pass, not a merge-triggered scan followed by another scan.
    if ns.command in {"scan", "rescan", "onboarding-plan"}:
        plan = repository_scan(root, force=(ns.command == "rescan"))
        persist_onboarding_plan(root, plan)
        if ns.json or ns.command == "onboarding-plan":
            print(json.dumps(plan, indent=2))
        else:
            print(f"[PASS] Repository scan: {plan.get('componentCount', 0)} component(s), {len(plan.get('operations') or [])} synthesized operation(s), {plan.get('markerCount', 0)} marker(s).")
            print(f"[INFO] Kinds: {', '.join(plan.get('kinds') or []) or 'none'}")
            for issue in plan.get("warnings") or []:
                print(f"[WARN] {issue}")
            for issue in plan.get("unresolved") or []:
                if isinstance(issue, dict): print(f"[INFO] {issue.get('message')}")
        return 0

    try:
        data = merge_contract(root)
        persist_generated(root, data)
    except Exception as exc:
        print(f"[FAIL] Project contract discovery/validation failed: {exc}")
        return 2

    # Project-owned semantic commands outrank ForgePY generic helpers.
    if ns.command in {"self-test", "doctor", "debug-bundle", "git-status", "git-history", "commit-green", "patch-status", "patch-check", "patch-apply"}:
        declared = find_command(data, ns.command)
        if declared and declared.get("_source") == "explicit":
            return run_operation(root, data, ns.command)
    if ns.command == "self-test":
        return self_test(root)
    if ns.command == "menu":
        return menu(root, data)

    if ns.command == "status":
        payload = status_payload(root, data)
        if ns.json:
            print(json.dumps(payload, indent=2))
        else:
            r, p, g = payload["runtime"], payload["project"], payload["git"]
            print(f"{r['product']} {r['version']} ({r['build']})")
            print(f"Project: {p.get('name')} [{p.get('kind')}] — {root}")
            print(f"Provider: {payload['discovery'].get('provider')} / {payload['discovery'].get('source')}")
            print(f"Git: {(g.get('branch') or '(detached)') + ' ' + str(g.get('head',''))[:12] + ' — ' + ('clean' if g.get('clean') else 'dirty') if g.get('ready') else 'unavailable/not initialized'}")
            print(f"Operations: {payload['operations']}  Patch candidates: {payload['patchCandidates']}")
        return 0
    if ns.command in {"discover", "contract"}:
        print(json.dumps(data, indent=2)); return 0
    if ns.command == "snapshot":
        print(json.dumps(snapshot_payload(root, data, include_patch_hash=False, history_count=20), indent=2)); return 0
    if ns.command == "onboarding-apply":
        try:
            path = write_scan_adapter(root)
            print(f"[PASS] Generated project adapter: {path}")
            return 0
        except RuntimeError as exc:
            print(f"[FAIL] {exc}")
            return 2
    if ns.command == "capabilities":
        print(json.dumps(data.get("capabilities", []), indent=2)); return 0
    if ns.command == "identity":
        print(json.dumps(data.get("project", {}), indent=2)); return 0
    if ns.command == "history":
        count = int(ns.extra[0]) if ns.extra and str(ns.extra[0]).isdigit() else 100
        print(json.dumps(operation_history(root, count), indent=2)); return 0
    if ns.command == "operations":
        if ns.json:
            print(json.dumps(data.get("commands", []), indent=2))
        else:
            for x in sorted(data.get("commands", []), key=lambda v: (str(v.get("category", "")), str(v.get("key", "")))):
                print(f"{str(x.get('key','')):24} {str(x.get('category','')):12} {str(x.get('risk','read')):6} {x.get('label','')} [{x.get('_source','project')}]")
        return 0
    if ns.command in {"doctor", "preflight"}:
        return doctor(root, data)
    if ns.command == "debug-bundle":
        out = debug_bundle(root, status_payload(root, data)); print(f"[PASS] Debug bundle: {out}"); return 0
    if ns.command == "git-status":
        print(json.dumps(git_status(root), indent=2)); return 0
    if ns.command == "git-history":
        print(json.dumps(git_history(root), indent=2)); return 0
    if ns.command == "commit-green":
        return commit_green(root, " ".join(ns.extra).strip() or None)
    if ns.command == "push":
        declared = find_command(data, "push")
        return run_operation(root, data, "push") if declared else git_push_safe(root)
    if ns.command == "git-pull":
        declared = find_command(data, "git-pull")
        return run_operation(root, data, "git-pull") if declared else git_pull_ff_only(root)
    if ns.command == "patch-status":
        print(json.dumps(patch_candidates(root, include_hash=True), indent=2)); return 0
    if ns.command in {"patch-check", "patch-apply"}:
        if not ns.extra:
            print(f"[FAIL] {ns.command} requires a patch path"); return 2
        path = Path(ns.extra[0]); path = path if path.is_absolute() else root / path
        return generic_patch_check(root, path) if ns.command == "patch-check" else generic_patch_apply(root, path)
    if ns.command == "full":
        return certify_full(root, data)
    if ns.command in {"quick", "fast", "build", "build-release", "test", "run"}:
        return run_operation(root, data, ns.command)
    if find_command(data, ns.command):
        return run_operation(root, data, ns.command)
    print(f"[FAIL] Unknown/unavailable command: {ns.command}")
    print("Use `ForgePY.cmd operations` to list available project operations.")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
