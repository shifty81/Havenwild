#!/usr/bin/env python3
from pathlib import Path
import json,sys
ROOT = Path(__file__).resolve().parents[5]
required=[
"tools/automation/validation/context.py","tools/automation/validation/result.py","tools/automation/validation/registry.py","tools/automation/validation/reporting.py","tools/automation/validation/generated_outputs.py",
"content/build/validator_registry_v2.json","content/build/validation_error_codes_v1.json"]
missing=[item for item in required if not (ROOT/item).is_file()]
if missing:
 print("HWV-MANIFEST-001 missing unified validation framework files: "+", ".join(missing));sys.exit(1)
registry=json.loads((ROOT/"content/build/validator_registry_v2.json").read_text(encoding="utf-8"))
if registry.get("schema")!="havenwild.validator.registry.v2":
 print("HWV-MANIFEST-001 invalid registry schema");sys.exit(1)
ids=[item["id"] for item in registry.get("validators",[])]
if len(ids)!=len(set(ids)) or not ids:
 print("HWV-MANIFEST-001 validator ids must be unique and non-empty");sys.exit(1)
runner=(ROOT/"tools/automation/validation/validation_runner.py").read_text(encoding="utf-8")
for token in ("validator_registry_v2.json","HWV-DEPENDENCY-001","topological_order","write_combined_report"):
 if token not in runner:
  print(f"HWV-MANIFEST-001 runner missing {token}");sys.exit(1)
print(f"Pass 146B unified validation framework validated: {len(ids)} registered validators")
