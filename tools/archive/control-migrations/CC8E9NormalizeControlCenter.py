#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, os, re
from pathlib import Path

TOKEN = 'CC8E9-CANONICAL-GREEN-AUTHORITY'
TAIL = r'''
  # CC8E9-CANONICAL-GREEN-AUTHORITY
  # Full Quality Gate has exactly one post-pass authority. It writes the same
  # canonical record consumed by the header and every protected Git action.
  $script:LastName='Full quality gate'
  $script:LastResult='PASS'
  $script:LastExitCode=0
  $gateAuthority = Join-Path $PSScriptRoot 'HavenwildGateAuthority.py'
  $gatePython = Get-Command python -ErrorAction SilentlyContinue
  if($null -eq $gatePython){ $gatePython = Get-Command py -ErrorAction SilentlyContinue }
  if($null -eq $gatePython -or -not (Test-Path -LiteralPath $gateAuthority)) {
    $script:LastResult='FAIL'; $script:LastExitCode=1
    Write-Color 'FAIL canonical GREEN finalization: HavenwildGateAuthority.py/Python is unavailable.' Red
    New-DebugBundle 'FAIL'
    return
  }
  & $gatePython.Source $gateAuthority finalize --root $Root --session-log $SessionLog 2>&1 | ForEach-Object { Write-Host $_; Add-Content -Path $SessionLog -Value $_ }
  if($LASTEXITCODE -ne 0) {
    $script:LastResult='FAIL'; $script:LastExitCode=1
    Write-Color 'FAIL canonical GREEN finalization. Build/tests passed, but publication certification was not written.' Red
    New-DebugBundle 'FAIL'
    return
  }
  New-DebugBundle 'PASS'
'''


def find_matching_brace(text: str, open_idx: int) -> int:
    depth = 0; i = open_idx; quote = None; block_comment = False; here_quote = None; line_start = True
    while i < len(text):
        if block_comment:
            j = text.find('#>', i)
            if j < 0: return len(text)-1
            i = j + 2; continue
        if here_quote:
            term = here_quote + '@'
            if line_start and text.startswith(term, i):
                i += len(term); here_quote = None; line_start = False; continue
            line_start = text[i] in '\r\n'; i += 1; continue
        c = text[i]
        if quote:
            if quote == "'":
                if c == "'":
                    if i+1 < len(text) and text[i+1] == "'": i += 2; continue
                    quote = None
                line_start = c in '\r\n'; i += 1; continue
            if c == '`': i += 2; continue
            if c == '"': quote = None
            line_start = c in '\r\n'; i += 1; continue
        if text.startswith('<#', i): block_comment = True; i += 2; continue
        if c == '#':
            j = text.find('\n', i)
            if j < 0: return len(text)-1
            i = j + 1; line_start = True; continue
        if c in "'\"":
            if i > 0 and text[i-1] == '@': here_quote = c
            else: quote = c
            line_start = False; i += 1; continue
        if c == '{': depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0: return i
        line_start = c in '\r\n'; i += 1
    raise RuntimeError('Unbalanced PowerShell function braces')


def function_extent(text: str, name: str):
    pat = re.compile(r'(?im)^\s*function\s+' + re.escape(name) + r'\b[^\r\n{]*\{')
    m = pat.search(text)
    if not m: raise RuntimeError(f'Function not found: {name}')
    open_idx = text.find('{', m.start(), m.end()); close_idx = find_matching_brace(text, open_idx)
    return m.start(), open_idx, close_idx


def latest_backup(root: Path) -> Path:
    backup_root = root / '.havenwild' / 'updates' / 'backups'
    if not backup_root.exists(): raise RuntimeError(f'Transactional backup root missing: {backup_root}')
    candidates = []
    for p in backup_root.glob('*/tools/control/HavenwildTools.ps1'):
        if not p.is_file(): continue
        try: text = p.read_text(encoding='utf-8-sig')
        except Exception: continue
        if 'CC8E9 one-time Control Center normalization bootstrap' in text: continue
        if 'PASS sequence Full quality gate' not in text: continue
        candidates.append(p)
    if not candidates: raise RuntimeError('No valid pre-CC8E9 HavenwildTools.ps1 backup was found.')
    candidates.sort(key=lambda p: p.stat().st_mtime_ns, reverse=True)
    return candidates[0]


def patch_tools(text: str) -> str:
    if TOKEN in text: return text
    _, open_idx, close_idx = function_extent(text, 'Invoke-FullQualityGate')
    body = text[open_idx+1:close_idx]
    matches = list(re.finditer(r"(?im)^\s*Write-Color\s+['\"]PASS sequence Full quality gate['\"]\s+Green\s*$", body))
    if not matches: matches = list(re.finditer(r"(?im)^\s*Write-(?:Host|Color).*PASS sequence Full quality gate.*$", body))
    if not matches: raise RuntimeError('Could not locate Full Quality Gate PASS line in Invoke-FullQualityGate.')
    m = matches[-1]; prefix = body[:m.end()]
    return text[:open_idx+1] + prefix + '\n' + TAIL + '\n' + text[close_idx:]


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--root',required=True); args=ap.parse_args(); root=Path(args.root).resolve()
    backup=latest_backup(root); source=backup.read_text(encoding='utf-8-sig'); patched=patch_tools(source)
    if TOKEN not in patched: raise RuntimeError('Normalization token was not installed.')
    live=root/'tools'/'control'/'HavenwildTools.ps1'; tmp=live.with_suffix('.cc8e9.tmp')
    tmp.write_text(patched,encoding='utf-8',newline='\n'); os.replace(tmp,live)
    retired=['tools/control/CC8E2RepairCore.py','tools/control/CC8E3RepairCore.py','tools/control/CC8E5GitBridge.py','tools/control/GitSourceControl.Core.runtime.ps1']
    removed=[]
    for rel in retired:
        p=root/rel
        if p.exists():
            try: p.unlink(); removed.append(rel)
            except OSError: pass
    state=root/'.havenwild'/'updates'/'cc8e9-normalization.json'; state.parent.mkdir(parents=True,exist_ok=True)
    state.write_text(json.dumps({'schema':'havenwild.cc8e9_normalization.v1','sourceBackup':str(backup),'liveSha256':hashlib.sha256(patched.encode('utf-8')).hexdigest(),'retiredActiveCompatibilityFiles':removed},indent=2),encoding='utf-8')
    print('CC8E9 NORMALIZATION PASS: one canonical GREEN/Git authority installed.')
    print(f' - recovered live Control Center: {backup}')
    print(f' - retired compatibility files: {len(removed)}')
    return 0

if __name__=='__main__':
    try: raise SystemExit(main())
    except Exception as exc:
        print(f'CC8E9 NORMALIZATION FAILED: {exc}')
        raise SystemExit(1)
