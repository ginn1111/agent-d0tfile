import re
import unittest
from pathlib import Path

THEME = Path("themes/cindy")
HEX = re.compile(r"#[0-9a-fA-F]{6}\b")


class ThemeCindyPaletteTest(unittest.TestCase):
    def test_theme_files_use_only_palette_colors(self):
        palette = {h.lower() for h in HEX.findall((THEME / "black-ruby.palette").read_text())}
        files = [
            p for p in THEME.rglob("*")
            if p.is_file() and "sketches" not in p.parts and p.name != "black-ruby.palette"
        ]
        self.assertTrue(files, "no theme files found")
        for p in files:
            stray = {h.lower() for h in HEX.findall(p.read_text())} - palette
            self.assertFalse(stray, f"{p}: colors not in palette: {sorted(stray)}")


if __name__ == "__main__":
    unittest.main()
