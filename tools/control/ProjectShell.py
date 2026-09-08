#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

DANGEROUS_PATTERNS = [
    r"\bgit\s+reset\s+--hard\b",
    r"\bgit\s+clean\b[^\r\n]*(?:-f|-d)",
    r"\bgit\s+push\b[^\r\n]*(?:--force|-f)\b",
    r"\brm\s+-rf\b",
    r"\brmdir\b[^\r\n]*/s\b",
    r"\bdel\b[^\r\n]*/s\b",
    r"\bremove-item\b[^\r\n]*-recurse\b",
    r"\bformat\b[^\r\n]*[a-z]:",
    r"\bdiskpart\b",
    r"\breg\s+delete\b",
]


def resolve_python_shell(kind: str) -> tuple[list[str], str]:
    kind = kind.lower()
    if kind in {"powershell", "ps", "p"}:
        exe = shutil.which("powershell") or shutil.which("pwsh")
        if not exe:
            raise RuntimeError("PowerShell was not found on PATH")
        return [exe, "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command"], "PowerShell"
    if kind in {"cmd", "command", "c"}:
        exe = shutil.which("cmd") or shutil.which("cmd.exe")
        if not exe:
            raise RuntimeError("Command Prompt (cmd.exe) was not found")
        return [exe, "/d", "/s", "/c"], "Command Prompt"
    if kind in {"bash", "gitbash", "b"}:
        candidates = [
            shutil.which("bash"),
            r"C:\Program Files\Git\bin\bash.exe",
            r"C:\Program Files\Git\usr\bin\bash.exe",
            r"C:\Program Files (x86)\Git\bin\bash.exe",
        ]
        exe = next((str(p) for p in candidates if p and Path(p).is_file()), None)
        if not exe:
            raise RuntimeError("Git Bash was not found")
        return [exe, "-lc"], "Git Bash"
    raise RuntimeError(f"Unknown shell: {kind}")


def command_is_dangerous(command: str) -> list[str]:
    hits = []
    lower = command.lower()
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, lower, flags=re.IGNORECASE):
            hits.append(pattern)
    return hits


def confirm_dangerous(command: str) -> bool:
    hits = command_is_dangerous(command)
    if not hits:
        return True
    print("\nWARNING: this command contains a destructive/high-risk operation:")
    for line in command.splitlines():
        print(f"  {line}")
    answer = input("Type RUN DESTRUCTIVE COMMAND to continue: ").strip()
    return answer == "RUN DESTRUCTIVE COMMAND"


def log_root(root: Path) -> Path:
    path = root / "logs" / "commands"
    path.mkdir(parents=True, exist_ok=True)
    return path


def next_log(root: Path, shell_label: str) -> Path:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    slug = re.sub(r"[^A-Za-z0-9]+", "-", shell_label).strip("-").lower()
    return log_root(root) / f"command-{stamp}-{slug}.log"


def run_command(root: Path, shell_kind: str, command: str) -> int:
    argv, label = resolve_python_shell(shell_kind)
    if not confirm_dangerous(command):
        print("Command cancelled.")
        return 2
    log = next_log(root, label)
    with log.open("w", encoding="utf-8", newline="\n") as out:
        header = [
            "HAVENWILD PROJECT COMMAND",
            f"Started: {datetime.now().isoformat()}",
            f"Project: {root}",
            f"Shell: {label}",
            "Command:",
            command,
            "--- output ---",
        ]
        for line in header:
            out.write(line + "\n")
        out.flush()
        print(f"\nShell   : {label}")
        print(f"Project : {root}")
        print(f"Log     : {log}")
        print("------------------------------------------------------------------------")
        proc = subprocess.Popen(
            [*argv, command],
            cwd=str(root),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )
        assert proc.stdout is not None
        for line in proc.stdout:
            print(line, end="")
            out.write(line)
            out.flush()
        code = proc.wait()
        out.write(f"\n--- exit code: {code} ---\n")
    print("------------------------------------------------------------------------")
    print(f"Exit code: {code}")
    print(f"Saved log: {log}")
    return code


def open_shell(root: Path, shell_kind: str) -> int:
    kind = shell_kind.lower()
    if kind in {"powershell", "ps", "p"}:
        exe = shutil.which("powershell") or shutil.which("pwsh")
        if not exe:
            raise RuntimeError("PowerShell was not found")
        subprocess.Popen([exe, "-NoExit", "-Command", f"Set-Location -LiteralPath '{str(root).replace("'", "''")}'"], cwd=str(root))
        return 0
    if kind in {"cmd", "command", "c"}:
        exe = shutil.which("cmd") or shutil.which("cmd.exe")
        if not exe:
            raise RuntimeError("Command Prompt was not found")
        subprocess.Popen([exe, "/K", f'cd /d "{root}"'], cwd=str(root))
        return 0
    if kind in {"bash", "gitbash", "b"}:
        argv, _ = resolve_python_shell("bash")
        exe = argv[0]
        subprocess.Popen([exe, "--login", "-i"], cwd=str(root))
        return 0
    raise RuntimeError(f"Unknown shell: {shell_kind}")


def read_multiline() -> str:
    print("Paste commands below. Enter a line containing only END when finished.")
    lines: list[str] = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line.strip() == "END":
            break
        lines.append(line)
    return "\n".join(lines).strip()


def choose_shell() -> str:
    raw = input("Shell [P]owerShell / [C]MD / [B]ash (default P): ").strip().lower()
    return {"": "powershell", "p": "powershell", "c": "cmd", "b": "bash"}.get(raw, raw)


def show_history(root: Path) -> None:
    files = sorted(log_root(root).glob("command-*.log"), key=lambda p: p.stat().st_mtime, reverse=True)[:20]
    if not files:
        print("No command logs yet.")
        return
    print("RECENT PROJECT COMMAND LOGS")
    for i, path in enumerate(files, 1):
        print(f" {i:2}. {path.name}")


def open_latest(root: Path) -> int:
    files = sorted(log_root(root).glob("command-*.log"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        print("No command logs yet.")
        return 1
    target = files[0]
    if os.name == "nt":
        os.startfile(target)  # type: ignore[attr-defined]
    else:
        print(target)
    return 0


def menu(root: Path) -> int:
    while True:
        print("\n========================================================================")
        print(" HAVENWILD PROJECT SHELL / COMMAND RUNNER")
        print("========================================================================")
        print(f" Project : {root}")
        print("------------------------------------------------------------------------")
        print("  1. Open PowerShell at project root")
        print("  2. Open Command Prompt at project root")
        print("  3. Open Git Bash at project root")
        print("  4. Run / paste one command")
        print("  5. Run / paste multi-line command")
        print("  6. Command history")
        print("  7. Open latest command log")
        print("  0. Back")
        print("------------------------------------------------------------------------")
        choice = input("Select: ").strip()
        try:
            if choice == "0":
                return 0
            if choice == "1":
                open_shell(root, "powershell")
            elif choice == "2":
                open_shell(root, "cmd")
            elif choice == "3":
                open_shell(root, "bash")
            elif choice == "4":
                shell = choose_shell()
                command = input("Paste command: ").strip()
                if command:
                    run_command(root, shell, command)
            elif choice == "5":
                shell = choose_shell()
                command = read_multiline()
                if command:
                    run_command(root, shell, command)
            elif choice == "6":
                show_history(root)
            elif choice == "7":
                open_latest(root)
            else:
                print("Unknown selection.")
        except Exception as exc:
            print(f"FAIL: {exc}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Havenwild project-root shell and logged command runner")
    ap.add_argument("--root", required=True)
    ap.add_argument("--action", default="menu", choices=["menu", "powershell", "cmd", "bash", "run", "history", "latest"])
    ap.add_argument("--shell", default="powershell")
    ap.add_argument("--command")
    args = ap.parse_args()
    root = Path(args.root).resolve()
    if args.action == "menu":
        return menu(root)
    if args.action in {"powershell", "cmd", "bash"}:
        return open_shell(root, args.action)
    if args.action == "run":
        if not args.command:
            raise RuntimeError("--command is required for --action run")
        return run_command(root, args.shell, args.command)
    if args.action == "history":
        show_history(root)
        return 0
    if args.action == "latest":
        return open_latest(root)
    return 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FAIL: {exc}")
        raise SystemExit(1)
