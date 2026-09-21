"""Check real PCC registry and ForgeGUI evidence surface: no alternate control center."""
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]

class PccInfrastructureContract(unittest.TestCase):
    def test_registry_has_one_dispatcher_and_honest_actions(self):
        registry=(ROOT/'tools/control/PccCommandExtensions.ps1').read_text(encoding='utf-8-sig')
        wrapper=(ROOT/'tools/control/HavenwildBevyCandidate.ps1').read_text(encoding='utf-8-sig')
        self.assertIn('experimental.bevy.infra-audit',registry)
        self.assertIn('experimental.bevy.infra-open',registry)
        self.assertIn('experimental.bevy.infra-pie',registry)
        self.assertIn('PIE handoff ticket (NO GAME LAUNCH)',registry)
        self.assertIn("InfraPackets='render-packets'",wrapper)
        self.assertIn('experiment_spine.py',wrapper)
        self.assertNotIn('BuiltinQualityGate',registry)
    def test_gui_stays_readonly_and_does_not_claim_runtime(self):
        rust=(ROOT/'experiments/haven_bevy_candidate/src/main.rs').read_text()
        self.assertIn('"infrastructure" => {',rust)
        self.assertIn('infrastructure_summary()',rust)
        self.assertIn('promotionAllowed',rust)
        self.assertIn('actual game PIE, and Macroquad retirement: PENDING.',rust)
        self.assertIn('Refresh candidate evidence (read-only)',rust)
    def test_experimental_full_gate_includes_candidate_check_before_green(self):
        pcc=(ROOT/'tools/control/HavenwildTools.ps1').read_text(encoding='utf-8-sig')
        start=pcc.index('function Invoke-FullQualityGate {')
        end=pcc.index('function Complete-FastQualityGate',start)
        gate=pcc[start:end]
        self.assertIn("(Get-ActiveGitBranchName) -eq 'experimental'",gate)
        self.assertIn('mandatory experimental Bevy candidate manifest is missing',gate)
        self.assertIn("if(-not (Test-Path -LiteralPath (Join-Path $Root 'experiments\\haven_bevy_candidate\\Cargo.toml')",gate)
        self.assertLess(gate.index('mandatory experimental Bevy candidate manifest is missing'),
                        gate.index('Bevy candidate infrastructure contract tests'))
        self.assertIn('Validate-HavenwildBevyCandidate.py',gate)
        self.assertIn("-Action Build",gate)
        self.assertIn("Complete-QualityGate 'FAIL'; return",gate)
        self.assertLess(gate.index('Bevy candidate mandatory Cargo check'),
                        gate.index("Write-Color 'PASS sequence Full quality gate'"))
    def test_no_canonical_core_changes_for_infra(self):
        script=(ROOT/'experiments/haven_bevy_candidate/tools/experiment_spine.py').read_text()
        self.assertIn('def guard(',script)
        self.assertIn("'canonicalSaveWriteAllowed': False",script)
        self.assertIn("'launchAllowed':False",script)
        self.assertIn('def atomic(',script)

if __name__=='__main__':unittest.main()
