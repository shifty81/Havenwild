#!/usr/bin/env python3
from pathlib import Path
import json, sys
ROOT = Path(__file__).resolve().parents[5]
registry=json.loads((ROOT/'content/build/generated_output_registry_v2.json').read_text(encoding='utf-8'))
required={
 'tools/build/Build.sh','tools/build/Build.ps1','Cargo.toml','content/validation/validation_manifest_v1.json',
 'content/build/generated_output_registry_v2.json','content/build/validator_registry_v3.json','tools/automation/validation/validation_runner.py',
 'tools/automation/packaging/Create-ChatGPTSourceRollup.py','tools/automation/packaging/Create-SourceOnlyRollup.py',
 'tools/automation/validation/checks/build/Validate-CleanSourceBuildV146.py','tools/automation/reports/Build-ReportV146E.py','tools/automation/reports/Write-BuildAttestationV146E.py','tools/automation/validation/checks/build/Validate-UnifiedBuildReportingV146E.py','tools/automation/validation/checks/build/Validate-BuildAttestationV146E.py','manifests/provenance/BUILD_PROVENANCE.json','docs/archive/pass_history/PASS146E_HANDOFF.md','docs/archive/root_pass_history/UNIFIED_BUILD_REPORTING_AND_ATTESTATION_PASS146E.md','tools/automation/common/atomic_io.py','tools/automation/project/Stamp-GeneratedOutputProvenanceV146D.py','tools/automation/validation/checks/build/Validate-GeneratedOutputProvenanceV146D.py','tools/automation/validation/checks/build/Validate-AtomicGenerationV146D.py','tools/automation/validation/native.py','tools/automation/validation/readonly.py','tools/automation/validation/checks/persistence/Validate-NativeValidatorMigrationV146C.py','docs/archive/pass_history/PASS146C_HANDOFF.md','docs/archive/pass_history/PASS146D_HANDOFF.md','manifests/provenance/legacy_root/GENERATED_ASSET_PROVENANCE_PASS146D.md'
}
for row in registry['outputs']:
 required.add(row['generator'])
 for rel in row['inputs']:
  if not rel.startswith('assets/generated/'): required.add(rel)
missing=sorted(x for x in required if not (ROOT/x).exists())
if missing:
 print('Pass 146 source rollup completeness missing:\n'+'\n'.join(missing)); sys.exit(1)
print(f'Pass 146 source rollup completeness validated: {len(required)} required source files')
