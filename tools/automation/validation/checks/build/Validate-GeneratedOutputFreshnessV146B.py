#!/usr/bin/env python3
from pathlib import Path
import json,sys
ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0,str(ROOT/'tools/automation'))
from validation.generated_outputs import inspect_output
registry=json.loads((ROOT/'content/build/generated_output_registry_v2.json').read_text(encoding='utf-8'))
entries=registry.get('outputs',[])
by_output={entry['output']:entry for entry in entries}
errors=[]; summary={}
for entry in entries:
    state=inspect_output(ROOT,entry)
    status=state.status
    if status=='missing-inputs':
        unresolved=[]
        for missing in state.missing_inputs:
            producer=by_output.get(missing)
            if producer is None or producer.get('packaging') not in {'regenerate','cache-or-regenerate'}:
                unresolved.append(missing)
        if unresolved:
            errors.append(f"HWV-ASSET-001 {state.output}: {', '.join(unresolved)}")
        else:
            status='pending-generation'
    elif status=='stale':
        # Pass 146D makes SHA-256 provenance authoritative. Archive extraction and
        # source-control checkout may rewrite mtimes without changing content.
        provenance=ROOT/entry.get('provenance','') if entry.get('provenance') else None
        status='fresh-provenance' if provenance and provenance.is_file() else 'regenerate'
    elif status=='missing-output':
        errors.append(f"HWV-ASSET-002 {state.output}: required packaged output is missing")
    summary[status]=summary.get(status,0)+1
if errors:
    print('\n'.join(errors));sys.exit(1)
print(f"Pass 146B generated-output freshness validated: {summary}")
