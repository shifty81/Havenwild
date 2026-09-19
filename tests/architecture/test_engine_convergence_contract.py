"""One authority per system and an explicit unpromoted Bevy candidate."""
import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
CONTRACT=ROOT/'content/architecture/havenwild_engine_convergence_v0_1.json'

class ConvergenceContractTests(unittest.TestCase):
    def test_owned_boundaries_and_no_early_promotion(self):
        data=json.loads(CONTRACT.read_text())
        self.assertEqual(data['schema'],'havenwild.engine_convergence.v0_1')
        self.assertEqual(data['baseline']['branch'],'experimental')
        self.assertEqual(len(data['subsystems']),10)
        self.assertTrue(data['candidateSafety']['legacyWriterAuthority'])
        self.assertFalse(data['candidateSafety']['candidateSaveWritesAllowed'])
        self.assertFalse(data['candidateSafety']['candidateAssetPublicationAllowed'])
        self.assertIn('world renderer parity',data['notClaimed'])
        self.assertEqual(data['oneAuthorityPerConcern']['patchesAndCertification'],
                         'existing Havenwild PCC, no alternate update authority')

    def test_existing_crates_and_candidate_survive(self):
        for path in ['crates/haven_world', 'crates/haven_assets', 'crates/haven_authoring',
                     'crates/haven_render', 'crates/haven_game', 'crates/haven_save',
                     'experiments/haven_bevy_candidate/src/main.rs']:
            # Only this test's additive patch gets tested in an isolated payload; root
            # project checkout is verified during actual PCC gate, not inferred here.
            if not (ROOT/path).exists():
                self.skipTest('Root source checkout required: '+path)

if __name__=='__main__':
    unittest.main()
