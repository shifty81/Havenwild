#!/usr/bin/env python3
"""Validate coverage and shape of the Havenwild Editor/Authoring V2 audit manifest.

This validator is intentionally not registered in PCC by HW-EDITOR-AUDIT-01; PCC is being
worked on separately. It can be called directly and can later be wired into the canonical
quality gate once the Authoring V2 branch begins.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

ALLOWED={"KEEP","MERGE","ADAPT","DEPRECATE","DELETE_LATER"}
MANIFEST=Path("content/editor/architecture/editor_authoring_v2_audit_manifest_v0_1.json")
NATIVE=Path("apps/haven_editor_native/src/app")

def main()->int:
    if not MANIFEST.exists():
        print(f"FAIL missing {MANIFEST}")
        return 2
    data=json.loads(MANIFEST.read_text(encoding="utf-8"))
    mods=data.get("modules",[])
    paths=[m.get("path","") for m in mods]
    failures=[]
    if len(paths)!=len(set(paths)):
        failures.append("manifest contains duplicate paths")
    for m in mods:
        if m.get("disposition") not in ALLOWED:
            failures.append(f"invalid disposition: {m}")
        p=Path(m.get("path",""))
        if not p.exists():
            failures.append(f"scoped path missing: {p}")
        if not m.get("targetOwner") or not m.get("reason"):
            failures.append(f"incomplete audit record: {p}")
    current={p.as_posix() for p in NATIVE.glob("*.rs")}
    audited={p for p in paths if p.startswith("apps/haven_editor_native/src/app/")}
    missing=sorted(current-audited)
    extra=sorted(audited-current)
    if missing:
        failures.append("native editor files missing from audit: "+", ".join(missing))
    if extra:
        failures.append("audit references absent native editor files: "+", ".join(extra))
    if failures:
        print("EDITOR AUTHORING V2 AUDIT: FAIL")
        for f in failures: print(" -",f)
        return 1
    counts={k:0 for k in sorted(ALLOWED)}
    for m in mods: counts[m["disposition"]]+=1
    print("EDITOR AUTHORING V2 AUDIT: PASS")
    print(f" scoped modules: {len(mods)}")
    print(f" native editor files: {len(current)}")
    print(" dispositions: "+", ".join(f"{k}={v}" for k,v in counts.items()))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
