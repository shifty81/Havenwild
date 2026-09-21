import importlib.util
import tempfile
import unittest
from pathlib import Path
P=Path(__file__).resolve().parents[1]/'tools/elevation_migration_audit.py'
spec=importlib.util.spec_from_file_location('elevation_migration_audit',P)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class ElevationMigrationAudit(unittest.TestCase):
    def test_missing_source_cannot_be_reported_as_policy_success(self):
        with tempfile.TemporaryDirectory() as d:
            report=m.inspect(Path(d))
            self.assertFalse(report['worldgenMigrated'])
            self.assertFalse(report['oldValidatorsRetired'])
            self.assertEqual(report['status'],'LEGACY_ELEVATION_MIGRATION_UNCERTIFIED')
            self.assertTrue(all(x['status']=='SOURCE_ABSENT_NOT_A_NEGATIVE_FINDING' for x in report['findings']))
    def test_known_legacy_rules_are_line_numbered_without_mutation(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            rel=next(iter(m.PATTERNS))
            f=root/rel; f.parent.mkdir(parents=True)
            f.write_text('prefix\n'+m.PATTERNS[rel][0]+'\n')
            report=m.inspect(root)
            self.assertEqual(report['findings'][0]['hits'][0]['line'],2)
            self.assertEqual(f.read_text(),'prefix\n'+m.PATTERNS[rel][0]+'\n')
            self.assertFalse(report['bevyWorldParityCertified'])
if __name__=='__main__':unittest.main()
