#!/usr/bin/env python3
"""Offline regression using the exact transport bytes and a synthetic Git workspace."""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
SCRIPT=Path(__file__).with_name('ReconcileHeldDuplicatePatch.py')
import os
ORIGINAL=Path(os.environ.get('HAVENWILD_B48R21_TRANSPORT','/nonexistent'))
# If exact user-download bytes are unavailable on a local Windows checkout,
# this optional test cannot manufacture substitute evidence.
def run_fixture(transport: Path) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp)
        subprocess.run(['git','init','-q',str(root)],check=True)
        subprocess.run(['git','-C',str(root),'checkout','-q','-b','experimental'],check=True)
        (root/'HavenwildTools.cmd').write_text('@echo off\n')
        (root/'.havenwild/pcc').mkdir(parents=True)
        (root/'.havenwild/updates').mkdir(parents=True)
        (root/'.havenwild/updates/last-applied.json').write_text(json.dumps({
            'schema':'havenwild.last_applied_patch.v1','pass':'B48R20'}))
        ledger={'schema':'havenwild.pcc_patch_ledger.v1','entries':[{
            'transport':SCRIPT.stem, 'status':'FAILED'}]}
        name='Havenwild_CUMULATIVE_PCC_Patch_B48R7_to_B48R21_EqualPaneMapperWorkflowAndIntakeProgress_20260919 (1).zip'
        ledger['entries'][0].update({'transport':name, 'targetLane':'experimental', 'required':True,
           'message':'Transport disappeared without APPLIED archive evidence; fail closed.'})
        lp=root/'.havenwild/pcc/patch-ledger.json'
        lp.write_text(json.dumps(ledger))
        holding=root/'artifacts/updates/held-duplicate-downloads/fixture'
        holding.mkdir(parents=True)
        shutil.copy2(transport,holding/name)
        run=lambda *flags: subprocess.run([sys.executable,str(SCRIPT),'--root',str(root),*flags],capture_output=True,text=True)
        assert run().returncode==0
        assert json.loads(lp.read_text())['entries'][0]['status']=='FAILED', 'dry run mutated ledger'
        assert run('--apply').returncode==0
        assert json.loads(lp.read_text())['entries'][0]['status']=='DEFERRED'
        assert run('--apply').returncode!=0, 'must not re-clear without exact FAILED evidence'
        assert (holding/name).is_file(), 'held bytes must be preserved'
        print('PASS: known false FAILED transitions to DEFERRED only with exact verified held archive; dry-run safe.')


def test_reconcile_held_duplicate() -> None:
    # These historical transport bytes are not present in ordinary source checkouts.
    # Skip at collection/runtime, never SystemExit while pytest imports this module.
    if not ORIGINAL.is_file():
        import pytest
        pytest.skip("exact B48R21 transport bytes not available; cannot invent audit evidence")
    run_fixture(ORIGINAL)


if __name__ == "__main__":
    if not ORIGINAL.is_file():
        print("SKIP: exact B48R21 transport not available for offline fixture.")
    else:
        run_fixture(ORIGINAL)
