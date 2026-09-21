import importlib.util
from pathlib import Path
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
import json
P=Path(__file__).resolve().parents[1]/'tools/gpu_validation_audit.py'
spec=importlib.util.spec_from_file_location('gpu_log_audit',P)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class GpuLogAudit(unittest.TestCase):
    def test_matching_user_vuids_are_not_marked_clean(self):
        raw='AdapterInfo { name: "GTX 1080 Ti", backend: Vulkan }\n'+ '\n'.join('VALIDATION ['+v+']' for v in m.VUIDS)
        data=m.inspect(raw)
        self.assertEqual(data['status'],'VALIDATION_ERROR_OBSERVED')
        self.assertEqual(data['actualAdapterBackend'],'Vulkan')
        self.assertEqual(data['presentLayoutErrorCount'],1)
        self.assertEqual(data['acquireSemaphoreErrorCount'],1)
        self.assertFalse(data['gpuValidated'])
    def test_zero_error_log_still_cannot_claim_verified(self):
        data=m.inspect('Finished `dev` target\n[GUI] Exit code: 0')
        self.assertIn('NOT_A_CLEAN_GPU_CERTIFICATION',data['status'])
        self.assertEqual(data['actualAdapterBackend'],'NOT_IN_LOG')
    def test_cli_is_read_only(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'gpu.log';p.write_text('AdapterInfo { backend: Dx12 }')
            output=StringIO()
            with redirect_stdout(output): self.assertEqual(m.main(['--log',str(p)]),0)
            self.assertEqual(json.loads(output.getvalue())['actualAdapterBackend'],'Dx12')
            self.assertEqual(p.read_text(),'AdapterInfo { backend: Dx12 }')
if __name__=='__main__':unittest.main()
