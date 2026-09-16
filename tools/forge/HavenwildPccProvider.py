#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, re, shutil, subprocess, sys
from pathlib import Path

FALLBACK_CAPABILITIES = {
    "schema": "havenwild.pcc_capabilities.v2",
    "provider": "forge.internal_pcc.v2",
    "project": "Havenwild",
    "authority": "project-native-pcc",
    "stableCommands": {
        "status": "pcc.status",
        "fullGate": "validation.full-quality-gate",
        "fastGate": "validation.fast-quality-gate",
        "commitPushGreen": "source-control.commit-push-green",
        "laneToggle": "project.lane.toggle",
        "patchLedger": "pcc.patch-ledger",
        "capabilities": "pcc.capabilities",
        "validate": "pcc.validate-v2",
        "validateLifecycle": "pcc.validate-lifecycle",
        "validateEditor": "pcc.validate-editor-v2",
        "vaultStatus": "pcc.vault-status",
        "vaultSync": "pcc.vault-sync",
    },
}

def powershell_executable() -> str:
    for candidate in ("powershell.exe", "pwsh.exe", "pwsh", "powershell"):
        found = shutil.which(candidate)
        if found:
            return found
    return "powershell.exe"

def read_capabilities(root: Path) -> dict:
    path = root / "content/architecture/havenwild_pcc_capabilities_v2.json"
    if path.is_file():
        try:
            return json.loads(path.read_text(encoding="utf-8-sig"))
        except Exception:
            pass
    return json.loads(json.dumps(FALLBACK_CAPABILITIES))

def registered_command_keys(root: Path) -> list[str]:
    keys: set[str] = set()
    pattern = re.compile(r"\bKey\s*=\s*'([^']+)'", re.IGNORECASE)
    for rel in ("tools/control/ProjectCommandRegistry.ps1", "tools/control/PccCommandExtensions.ps1"):
        path = root / rel
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8-sig")
        keys.update(pattern.findall(text))
    return sorted(keys)

def invoke_host(root: Path, key: str) -> int:
    host = root / "tools/control/HavenwildPccHost.ps1"
    cmd = [
        powershell_executable(), "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
        str(host), "-Command", key,
    ]
    return subprocess.call(cmd, cwd=root)

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "action",
        choices=[
            "capabilities", "status", "commands", "command", "full-gate", "fast-gate",
            "lane-toggle", "patch-status", "validate-pcc", "validate-lifecycle", "validate-editor", "vault-status", "vault-sync"
        ],
    )
    ap.add_argument("--root", required=True)
    ap.add_argument("--key")
    ns = ap.parse_args()
    root = Path(ns.root).resolve()

    if ns.action == "capabilities":
        payload = read_capabilities(root)
        keys = registered_command_keys(root)
        payload["registeredCommandCount"] = len(keys)
        payload["registeredCommands"] = keys
        print(json.dumps(payload, indent=2))
        return 0
    if ns.action == "commands":
        print(json.dumps({"schema": "havenwild.pcc_registered_commands.v1", "commands": registered_command_keys(root)}, indent=2))
        return 0
    if ns.action == "status":
        return subprocess.call([sys.executable, str(root / "tools/control/PccQuickState.py"), "--root", str(root), "--pretty"])
    if ns.action == "validate-pcc":
        return subprocess.call([sys.executable, str(root / "tools/validation/Validate-HavenwildPccV2.py"), "--root", str(root)])
    if ns.action == "validate-lifecycle":
        return subprocess.call([sys.executable, str(root / "tools/validation/Validate-HavenwildPccLifecycle.py"), "--root", str(root)])
    if ns.action == "validate-editor":
        return subprocess.call([sys.executable, str(root / "tools/validation/Validate-HavenwildEditorArchitectureV2.py"), "--root", str(root)])

    key = {
        "full-gate": "validation.full-quality-gate",
        "fast-gate": "validation.fast-quality-gate",
        "lane-toggle": "project.lane.toggle",
        "patch-status": "pcc.patch-ledger",
        "vault-status": "pcc.vault-status",
        "vault-sync": "pcc.vault-sync",
        "command": ns.key or "",
    }[ns.action]
    if not key:
        print("--key is required for action=command", file=sys.stderr)
        return 2
    if key not in registered_command_keys(root):
        print(f"command key is not registered: {key}", file=sys.stderr)
        return 2
    return invoke_host(root, key)

if __name__ == "__main__":
    raise SystemExit(main())
