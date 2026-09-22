"""Regress exit-code loss when Bevy's renderer requests AppExit::error().

Static contract only; a Windows GPU launch must still validate real behavior.
"""
from pathlib import Path
import unittest

SOURCE = Path(__file__).resolve().parents[1] / "src/main.rs"
GATE = Path(__file__).resolve().parents[1] / "tools/candidate_gate.py"


class CandidateExitTruthTests(unittest.TestCase):
    def test_bevy_exit_is_returned_to_the_process(self):
        source = SOURCE.read_text(encoding="utf-8")
        main = source.split("fn main() -> bevy::app::AppExit {", 1)[1]
        self.assertIn(".add_systems(EguiPrimaryContextPass, (report_original_sheet, gui).chain())", main)
        self.assertIn(".run()\n}", main)
        self.assertNotIn(".run();\n}", main)

    def test_pcc_does_not_replace_real_child_exit_code_with_visual_approval(self):
        gate = GATE.read_text(encoding="utf-8")
        self.assertIn("return exit_code", gate)
        self.assertIn("'gpuRendered':None", gate)
        self.assertIn("'worldRendererParity':False", gate)


if __name__ == "__main__":
    unittest.main()
