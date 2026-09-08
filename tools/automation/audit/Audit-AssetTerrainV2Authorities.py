#!/usr/bin/env python3
from pathlib import Path
import json,re,sys
ROOT=Path(__file__).resolve().parents[3]
patterns={
 "terrain_resolver":["terrain","transition","autotile","wang"],
 "cliff_structure":["cliff","elevation","contour","ramp","connector"],
 "asset_provider":["lpc","elizawy","v7","asset_browser","asset_intake"],
 "editor_client":["dev_client_bridge","development_session","runtime_editor","prepared_canvas"]
}
roots=[ROOT/"crates",ROOT/"apps",ROOT/"content/editor",ROOT/"content/worldgen",ROOT/"content/assets"]
rows=[]
for root in roots:
 if not root.exists(): continue
 for p in root.rglob("*"):
  if not p.is_file() or p.suffix.lower() not in {".rs",".json",".ron",".toml"}: continue
  rel=p.relative_to(ROOT).as_posix().lower()
  hits=[k for k,words in patterns.items() if any(w in rel for w in words)]
  if hits: rows.append({"path":p.relative_to(ROOT).as_posix(),"lanes":hits})
report={"schema":"havenwild.asset_terrain_v2.legacy_authority_inventory.v1","files":rows,
 "counts":{k:sum(k in r["lanes"] for r in rows) for k in patterns}}
out=ROOT/"artifacts/audits/asset_terrain_v2_legacy_authority_inventory.json"
out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
print(json.dumps(report["counts"],indent=2));print(out)
