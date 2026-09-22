"""Candidate shell native-stream contract: do not confuse Cargo stderr with failure."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

class CandidateNativeStreamContracts(unittest.TestCase):
    def test_stderr_is_normalized_before_windows_powershell(self):
        gate = (ROOT / 'experiments/haven_bevy_candidate/tools/candidate_gate.py').read_text(encoding='utf-8')
        host = (ROOT / 'tools/control/PccCommandHost.ps1').read_text(encoding='utf-8')
        self.assertIn('subprocess.call(cmd,cwd=candidate,stderr=subprocess.STDOUT)', gate)
        candidate = host.split("if($Key -in @('experimental.bevy.status'", 1)[1]
        candidate = candidate.split("if($Key.StartsWith('pcc.')", 1)[0]
        self.assertIn('$result=$LASTEXITCODE', candidate)
        self.assertIn('return [int]$result', candidate)
        self.assertNotIn('-Action $action 2>&1', candidate)
        self.assertIn('worldRendererParity', gate)
        self.assertIn("'gpuRendered':None", gate)

if __name__ == '__main__':
    unittest.main()
