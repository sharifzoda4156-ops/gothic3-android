"""Offline checks with synthetic JAR fixtures only; no game content."""
import importlib.util
import tempfile
import unittest
import zipfile
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "preparer", Path(__file__).resolve().parents[1] / "tools/prepare_midlet.py"
)
preparer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preparer)


class TestPreparation(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.upstream = self.root / "upstream"
        (self.upstream / "app/src/midlet").mkdir(parents=True)
        (self.upstream / "app/src/midlet/AndroidManifest.xml").write_text("<manifest/>")
        gradle_id = 'applicationId "com.example.androidlet.' + '$' + '{apkName.toLowerCase()}"\n'
        (self.upstream / "app/build.gradle").write_text(gradle_id + "dependencies {\n}\n")
        self.jar = self.root / "fake.jar"

    def make_jar(self, include_main=True, extra=None):
        with zipfile.ZipFile(self.jar, "w") as z:
            z.writestr("META-INF/MANIFEST.MF",
                       "Manifest-Version: 1.0\r\nMIDlet-1: Sample, /icon.png, HG\r\n"
                       "MIDlet-Name: Sample\r\nMIDlet-Version: 15.0\r\n\r\n")
            if include_main:
                z.writestr("HG.class", b"fake")
            z.writestr("005.png", b"fake")
            z.writestr("icon.png", b"fake")
            for name, content in (extra or {}).items():
                z.writestr(name, content)

    def test_prepare(self):
        self.make_jar()
        result = preparer.prepare(self.jar, self.upstream)
        self.assertEqual(result["classes"], 1)
        self.assertEqual(result["resources"], 2)
        self.assertEqual(result["midlet_class"], "HG")
        manifest = (self.upstream /
            "app/src/midlet/resources/MIDLET-META-INF/MANIFEST.MF").read_text()
        self.assertIn("MIDlet-1: Gothic 3 The Beginning, /icon.png, HG", manifest)
        self.assertEqual((self.upstream / "app/src/midlet/resources/005.png").read_bytes(), b"fake")
        with zipfile.ZipFile(self.upstream / "app/libs/gothic3-classes.jar") as z:
            self.assertEqual(z.namelist(), ["HG.class"])
        self.assertIn("org.gothic3.fanport", (self.upstream / "app/build.gradle").read_text())

    def test_unsafe_path(self):
        self.make_jar(extra={"../bad.png": b"bad"})
        with self.assertRaisesRegex(ValueError, "Unsafe ZIP path"):
            preparer.prepare(self.jar, self.upstream)

    def test_missing_class(self):
        self.make_jar(include_main=False)
        with self.assertRaisesRegex(ValueError, "MIDlet class missing"):
            preparer.prepare(self.jar, self.upstream)


if __name__ == "__main__":
    unittest.main()
