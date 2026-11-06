"""Synthetic-only tests for read-only HD atlas audit. No proprietary images."""
import importlib.util
import struct
import tempfile
import unittest
import zipfile
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "auditor", Path(__file__).resolve().parents[1] / "tools/audit_hd_jar.py"
)
auditor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(auditor)


def dummy_png(w, h):
    return b'\x89PNG\r\n\x1a\n' + b'\x00\x00\x00\rIHDR' + struct.pack('>II', w, h) + b'\x08\x06\x00\x00\x00'


class HDGeometryTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.jar = Path(temp.name) / "fake.jar"

    def make_archive(self, hd_width=128):
        with zipfile.ZipFile(self.jar, "w") as z:
            z.writestr("005.png", dummy_png(64, 144))
            z.writestr("hd/005.png", dummy_png(hd_width, 288))
            z.writestr("Hd.class", b'\xca\xfe\xba\xbe\x00\x00\x00\x34')
            z.writestr("hd/211_t1.png", dummy_png(16, 16))

    def test_matching_double_res_and_variant(self):
        self.make_archive()
        report = auditor.audit(self.jar)
        self.assertTrue(report["static_checks_passed"])
        self.assertEqual(report["hd_png_matched_2x"], 1)
        self.assertEqual(report["hd_png_variant_only"], 1)

    def test_detect_mismatch(self):
        self.make_archive(hd_width=127)
        report = auditor.audit(self.jar)
        self.assertFalse(report["static_checks_passed"])
        self.assertEqual(len(report["hd_png_invalid"]), 1)


if __name__ == "__main__":
    unittest.main()
