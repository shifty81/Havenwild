#!/usr/bin/env python3
from __future__ import annotations
import tempfile
import unittest
from pathlib import Path
from importlib.util import module_from_spec, spec_from_file_location

ROOT = Path(__file__).resolve().parents[3]
SPEC = spec_from_file_location('binding_audit', ROOT/'tools/automation/assets/Audit-SourceFirstVisualBindingsB07.py')
MODULE = module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

class AuditTests(unittest.TestCase):
    def test_source_roles_are_not_misclassified(self):
        report = MODULE.inspect(ROOT)
        self.assertFalse(report['source_pack_production_enabled'])
        entries = {e['role']:e for e in report['bindings']}
        self.assertNotEqual(entries['distinct_building_stair_source']['path'], entries['optional_quarantined_cliff_ramp_source']['path'])
        self.assertFalse(entries['optional_quarantined_cliff_ramp_source']['required'])
        self.assertEqual(len(entries['optional_quarantined_cliff_ramp_source']['expected_sha256']), 64)

    def test_missing_optional_is_a_diagnostic_not_a_fake_generated_source(self):
        report = MODULE.inspect(ROOT)
        optional = next(e for e in report['bindings'] if e['role'] == 'optional_quarantined_cliff_ramp_source')
        self.assertIn(optional['status'], ('available','not_mounted_optional','hash_mismatch'))
        self.assertNotEqual(optional['status'], 'missing_required')
        self.assertFalse(report['original_licensed_art_mutated'])

if __name__ == '__main__': unittest.main()
