from __future__ import annotations

import sys


def main() -> int:
    print(
        "W60E3A compile repair is retired and fail-closed.\n"
        "W78 removed the duplicate Pixel Layer panel and promoted its live layer controls "
        "into the canonical Canvas Layers rail. Re-running this historical repair would "
        "reintroduce obsolete GUI authority.\n"
        "Use HavenwildTools.cmd -> Build & Verify -> Full quality gate instead.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
