"""Static contracts; Rust build, Vulkan validation and GPU screenshots remain Windows-only."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


class CandidateLaunchAndShellContracts(unittest.TestCase):
    def test_candidate_child_output_is_host_only_and_exit_is_numeric(self):
        ps = (ROOT / 'tools/control/PccCommandHost.ps1').read_text(encoding='utf-8')
        beginning = ps.split("if($Key -in @('experimental.bevy.status'", 1)[1]
        dispatch = beginning.split("if($Key.StartsWith('pcc.')", 1)[0]
        self.assertIn('-File $script -Root $Root -Action $action |', dispatch)
        self.assertNotIn('-Action $action 2>&1 |', dispatch)
        self.assertIn('ForEach-Object { Write-Host $_ }', dispatch)
        self.assertIn('$result=$LASTEXITCODE', dispatch)
        self.assertIn('return [int]$result', dispatch)
        self.assertNotIn('| Out-String', dispatch)

    def test_candidate_horizontal_menu_and_smaller_bottom_dock(self):
        main = (ROOT / 'experiments/haven_bevy_candidate/src/main.rs').read_text(encoding='utf-8')
        menu = main.split('fn menu(&mut self, ui: &mut egui::Ui)', 1)[1].split('fn toolbar(', 1)[0]
        self.assertIn('ui.horizontal(|ui| {', menu)
        for name in ('File', 'View', 'Help'):
            self.assertIn(f'ui.menu_button("{name}"', menu)
        self.assertIn('activity.preferred_size = [320.0, 150.0];', main)
        self.assertIn('UNAPPROVED', main)
        self.assertNotIn('macroquad::', main)

if __name__ == '__main__':
    unittest.main()
