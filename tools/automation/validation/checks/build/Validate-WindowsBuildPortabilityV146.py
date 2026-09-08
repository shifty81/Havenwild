#!/usr/bin/env python3
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[5]
sh=(ROOT/'tools/build/Build.sh').read_text(encoding='utf-8')
ps=(ROOT/'tools/build/Build.ps1').read_text(encoding='utf-8')
ensure=(ROOT/'tools/automation/dependencies/Ensure-LpcDependency.py').read_text(encoding='utf-8')
errors=[]
for token in ('PYTHONUTF8=1','PYTHONIOENCODING=utf-8'): 
 if token not in sh: errors.append(f'tools/build/Build.sh missing {token}')
for token in ('PYTHONUTF8','PYTHONIOENCODING'):
 if token not in ps: errors.append(f'tools/build/Build.ps1 missing {token}')
for token in ('core.longpaths=true','HAVENWILD_LPC_CACHE','New-Item -ItemType Junction','"mklink", "/J"'):
 if token not in ensure: errors.append(f'Ensure-LpcDependency.py missing structured safeguard {token}')
stage=(ROOT/'tools/automation/release/Stage-ApplicationContent.py').read_text(encoding='utf-8')
for token in ('Stage-ApplicationContent.py', 'copy_application_content'):
 if token not in sh: errors.append(f'tools/build/Build.sh missing filtered staging contract {token}')
for token in ('Stage-ApplicationContent.py', 'Copy-ApplicationContent'):
 if token not in ps: errors.append(f'tools/build/Build.ps1 missing filtered staging contract {token}')
for token in ('EXCLUDED_LICENSED_DIRECTORIES', 'EXCLUDED_LICENSED_FILES', 'licensed_ignore', 'is_under_licensed_source', 'prune_staged_dependency_development', 'staged_forbidden_paths', 'staged dependency-development files remain'):
 if token not in stage: errors.append(f'Stage-ApplicationContent.py missing exclusion contract {token}')
if 'current.resolve().relative_to((ROOT / \"assets\").resolve())' in stage:
 errors.append('Stage-ApplicationContent.py still uses junction-breaking resolved-relative staging logic')
normalize=(ROOT/'tools/automation/project/Normalize-WorkspaceLayout.py').read_text(encoding='utf-8')
for token in ('force_remove', 'stat.S_IWRITE', 'WARNING: staged dependency cleanup deferred; build may continue'):
 if token not in normalize: errors.append(f'Normalize-WorkspaceLayout.py missing read-only cleanup safeguard {token}')

# Rust formatting must happen before source/architecture validation. Otherwise
# rustfmt can expand physical line counts after the architecture gate and make
# the next identical build fail against a stale pre-format ceiling.
all_start = sh.find("  all)")
all_end = sh.find("    ;;", all_start)
all_block = sh[all_start:all_end] if all_start >= 0 and all_end >= 0 else ""
if not all_block:
 errors.append('tools/build/Build.sh all command block missing')
elif all_block.find('normalize_rust_source') < 0:
 errors.append('tools/build/Build.sh all command must normalize Rust formatting')
else:
 validation_position = all_block.find('validate_current_capabilities ')
 if validation_position < 0:
  errors.append('tools/build/Build.sh all command must run current capability validation')
 elif all_block.find('normalize_rust_source') > validation_position:
  errors.append('tools/build/Build.sh must normalize Rust formatting before source validation')
if 'function Normalize-RustSource' not in ps:
 errors.append('tools/build/Build.ps1 missing Normalize-RustSource')
if errors: print('\n'.join('Pass 146 portability: '+e for e in errors)); sys.exit(1)
print('Pass 146 Windows build portability validated')
