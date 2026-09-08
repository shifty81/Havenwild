#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[5]


def fail(message: str) -> None:
    raise SystemExit(f"N5L HavenwildTools PowerShell parser compatibility validation FAILED: {message}")


def main() -> None:
    path = ROOT / "tools/control/HavenwildTools.ps1"
    if not path.is_file():
        fail("missing tools/control/HavenwildTools.ps1")
    text = path.read_text(encoding="utf-8")

    ambiguous = '$packageHelper:'
    if ambiguous in text:
        fail("unbraced local variable immediately followed by ':' remains; Windows PowerShell parses this as a drive-qualified variable")

    safe = '"Could not remove stale cumulative-patch transport helper {0}: {1}" -f $packageHelper, $_.Exception.Message'
    if safe not in text:
        fail("stale-helper failure message is not using parser-safe format-string interpolation")

    # Catch the same parser trap for ordinary local variables in future edits while
    # allowing intentional PowerShell scope prefixes such as $script:, $global:, and $env:.
    scoped = {"script", "global", "local", "private", "env", "using"}
    for lineno, line in enumerate(text.splitlines(), 1):
        if '"' not in line:
            continue
        for match in re.finditer(r"\$([A-Za-z_][A-Za-z0-9_]*):", line):
            if match.group(1).lower() not in scoped:
                fail(f"potential ambiguous variable-colon interpolation at line {lineno}: {match.group(0)}")

    print("N5L HavenwildTools PowerShell parser compatibility validated")


if __name__ == "__main__":
    main()
