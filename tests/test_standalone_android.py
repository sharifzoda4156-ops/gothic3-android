"""Regression checks: Gothic game features must remain wired into normal builds."""
import importlib.util
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("verify_standalone", ROOT / "tools/verify_standalone_apk.py")
verifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verifier)


class GothicIntegrationTests(unittest.TestCase):
    def test_standalone_activity_mounts_our_controls(self):
        activity = (ROOT / "app/src/main/java/javax/microedition/shell/MicroActivity.java").read_text()
        self.assertIn("installGothicControls();", activity)
        self.assertIn("new GothicControlsView(this)", activity)
        self.assertIn("gothicControls.cancelInputs();", activity)
        self.assertIn("ContextHolder.setVk(null);", activity)

    def test_preset_exists_without_overwriting_hd3x(self):
        loader = (ROOT / "app/src/main/java/javax/microedition/shell/MicroLoader.java").read_text()
        defaults = (ROOT / "app/src/main/java/ru/playsoftware/j2meloader/config/GothicProfileDefaults.java").read_text()
        self.assertIn("GothicProfileDefaults.ensure(context, config)", loader)
        self.assertIn("screenWidth = 720; screenHeight = 960", loader)
        self.assertIn("profile.screenWidth = 480;", defaults)
        self.assertIn("profile.screenHeight = 640;", defaults)
        self.assertIn("profile.showKeyboard = false;", defaults)

    def test_top_row_and_midp_bindings(self):
        controls = (ROOT / "app/src/main/java/javax/microedition/shell/gothic/GothicControlsView.java").read_text()
        self.assertIn("final int[] topRow = {BACK, PAUSE, MENU};", controls)
        self.assertIn("KEY_CODES = {'5', '*', '#', -6, -7, '0'}", controls)

    def test_builds_use_checked_out_game_not_unmodified_emulator(self):
        shell = (ROOT / "tools/build_local.sh").read_text()
        windows = (ROOT / "tools/build_local.ps1").read_text()
        self.assertNotIn("git clone https://github.com/nikita36078/J2ME-Loader", shell)
        self.assertNotIn("git clone https://github.com/nikita36078/J2ME-Loader", windows)
        self.assertIn(":app:assembleMidletDebug", shell)
        self.assertIn(":app:assembleMidletDebug", windows)

    def test_launcher_name_exact(self):
        manifest = (ROOT / "app/src/midlet/resources/MIDLET-META-INF/MANIFEST.MF").read_text()
        self.assertIn("MIDlet-Name: Gothic 3: The Beginning", manifest)

    def test_apk_verifier_detects_missing_controls(self):
        with tempfile.TemporaryDirectory() as folder:
            apk = Path(folder) / "fake.apk"
            with ZipFile(apk, "w") as z:
                z.writestr("classes.dex", b"".join(verifier.REQUIRED_CLASSES))
            verifier.verify(apk)
            with ZipFile(apk, "w") as z:
                z.writestr("classes.dex", b"LGothicResolution;")
            with self.assertRaisesRegex(ValueError, "missing Gothic game features"):
                verifier.verify(apk)


if __name__ == "__main__":
    unittest.main()
