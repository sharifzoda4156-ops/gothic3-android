"""Test Android launcher icon resizing with a synthetic source image."""
import importlib.util
import tempfile
import unittest
from pathlib import Path

from PIL import Image

spec = importlib.util.spec_from_file_location(
    "game_icons", Path(__file__).resolve().parents[1] / "tools/generate_game_icons.py"
)
icons = importlib.util.module_from_spec(spec)
spec.loader.exec_module(icons)


class TestLauncherIcons(unittest.TestCase):
    def test_all_density_outputs_and_transparency(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "emblem.png"
            Image.new("RGBA", (44, 44), (200, 30, 17, 255)).save(source)
            output = root / "res"
            paths = icons.generate(source, output)
            self.assertEqual(10, len(paths))
            for density, factor in icons.DENSITIES.items():
                directory = output / ("mipmap-" + density)
                with Image.open(directory / "ic_launcher.png") as png:
                    self.assertEqual((round(48 * factor),) * 2, png.size)
                    self.assertNotEqual(0, png.getpixel((png.width // 2, png.height // 2))[3])
                with Image.open(directory / "ic_launcher_foreground.png") as png:
                    self.assertEqual((round(108 * factor),) * 2, png.size)
                    self.assertEqual(0, png.getpixel((0, 0))[3])
                    self.assertEqual((200, 30, 17, 255), png.getpixel((png.width // 2, png.height // 2)))

    def test_rejects_non_square_source(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            image = root / "bad.png"
            Image.new("RGBA", (20, 30)).save(image)
            with self.assertRaisesRegex(ValueError, "square"):
                icons.generate(image, root / "res")


if __name__ == "__main__":
    unittest.main()
