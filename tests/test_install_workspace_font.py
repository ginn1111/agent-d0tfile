import io
import os
import subprocess
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "scripts" / "install_workspace_font.py"
FAMILY = "Terminess Nerd Font"

LINUX = {
    ".config/i3/config": "set $mod Mod4\nfont pango:Roboto Condensed, 10\n",
    ".config/polybar/config.ini": "[bar/top]\nfont-0 = EnvyCodeR Nerd Font:size=11;3\n"
                                  "font-1 = EnvyCodeR Nerd Font:style=Bold:size=11;3\n"
                                  "font-2 = IoskeleyMono Nerd Font Mono:size=11;3\n",
    ".config/rofi/launchers/shared/fonts.rasi": '* {\n    font: "JetBrains Mono Nerd Font Bold Italic 12";\n}\n',
    ".config/rofi/powermenu/style.rasi": '@import "shared/fonts.rasi"\n    element-font: "feather 48";\n',
    ".config/dunst/dunstrc": "[global]\n    font = IoskeleyMono Nerd Font 8.5     # body\n",
    ".config/kitty/kitty.conf": 'font_family      family="IoskeleyMono Nerd Font"\n',
}
MACOS = {
    ".config/sketchybar/sketchybarrc": 'FONT="SF Pro"\nsketchybar --default icon.font="Hack Nerd Font:Semibold:14.0" \\\n'
                                       '  label.font="$FONT:Semibold:12.0"\n',
    ".config/sketchybar/items/spaces.sh": 'icon.font="$FONT:Black:12.0" label.font="sketchybar-app-font:Regular:12.0"\n',
    ".config/sketchybar/items/front_app.sh": 'label.font="$FONT:Regular:10.0"\n',
    ".config/kitty/kitty.conf": 'font_family      family="IoskeleyMono Nerd Font"\n',
}


def snapshot(home):
    return {str(p.relative_to(home)): p.read_bytes() for p in sorted(home.rglob("*")) if p.is_file()}


def fake_archive(path):
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:xz") as tar:
        for name in ["TerminessNerdFont-Regular.ttf", "TerminessNerdFont-Bold.ttf", "LICENSE.txt", "README.md"]:
            info = tarfile.TarInfo(name)
            info.size = len(name)
            tar.addfile(info, io.BytesIO(name.encode()))
    path.write_bytes(buf.getvalue())


class Base(unittest.TestCase):
    PLATFORM, FIXTURES = None, {}

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name) / "home"
        for rel, text in self.FIXTURES.items():
            p = self.home / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text)
        self.archive = Path(self.tmp.name) / "Terminus.tar.xz"
        fake_archive(self.archive)
        self.original = snapshot(self.home)

    def tearDown(self):
        self.tmp.cleanup()

    def run_script(self, *args):
        env = {**os.environ, "HOME": str(self.home), "WORKSPACE_FONT_PLATFORM": self.PLATFORM,
               "WORKSPACE_FONT_ARCHIVE": str(self.archive), "PATH": "/nonexistent"}  # no fc-cache side effects
        r = subprocess.run([sys.executable, str(SCRIPT), *args], env=env, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return r.stdout

    def read(self, rel):
        return (self.home / rel).read_text()

    def check_common(self):
        self.assertEqual(self.read(".config/kitty/kitty.conf"), self.FIXTURES[".config/kitty/kitty.conf"])
        after = snapshot(self.home)
        out = self.run_script()
        self.assertEqual(snapshot(self.home), after, "second run must be a no-op")
        self.assertTrue(all(line.startswith(("ok ", "reload:")) for line in out.splitlines()), out)
        self.run_script("--restore")
        self.assertEqual(snapshot(self.home), self.original)

    def test_dry_run_writes_nothing(self):
        out = self.run_script("--dry-run")
        self.assertIn("would install", out)
        self.assertIn("would edit", out)
        self.assertEqual(snapshot(self.home), self.original)


class LinuxTest(Base):
    PLATFORM, FIXTURES = "linux", LINUX

    def test_install_rewrites_targets_skips_kitty_and_restores(self):
        self.run_script()
        fonts = self.home / ".local/share/fonts/terminess"
        self.assertTrue((fonts / "TerminessNerdFont-Bold.ttf").exists())
        self.assertFalse((fonts / "README.md").exists())
        self.assertIn(f"font pango:{FAMILY} 10\n", self.read(".config/i3/config"))
        bar = self.read(".config/polybar/config.ini")
        self.assertIn(f"font-0 = {FAMILY}:size=11;3", bar)
        self.assertIn(f"font-1 = {FAMILY}:style=Bold:size=11;3", bar)
        self.assertIn("font-2 = IoskeleyMono Nerd Font Mono", bar, "glyph fallback slot stays")
        self.assertIn(f'"{FAMILY} Bold Italic 12"', self.read(".config/rofi/launchers/shared/fonts.rasi"))
        self.assertIn('"feather 48"', self.read(".config/rofi/powermenu/style.rasi"), "icon font stays")
        self.assertIn(f"font = {FAMILY} 8.5     # body", self.read(".config/dunst/dunstrc"))
        self.check_common()


class MacosTest(Base):
    PLATFORM, FIXTURES = "macos", MACOS

    def test_install_rewrites_targets_skips_kitty_and_restores(self):
        self.run_script()
        self.assertTrue((self.home / "Library/Fonts/TerminessNerdFont-Regular.ttf").exists())
        self.assertTrue((self.home / "Library/Fonts/Terminess-LICENSE.txt").exists())
        rc = self.read(".config/sketchybar/sketchybarrc")
        self.assertIn('FONT="SF Pro"', rc, "SF Symbols icons need SF Pro")
        self.assertIn('icon.font="Hack Nerd Font:Semibold:14.0"', rc, "icon fonts stay")
        self.assertIn(f'label.font="{FAMILY}:Bold:12.0"', rc)
        spaces = self.read(".config/sketchybar/items/spaces.sh")
        self.assertIn('icon.font="$FONT:Black:12.0"', spaces)
        self.assertIn('"sketchybar-app-font:Regular:12.0"', spaces, "icon font stays")
        self.assertIn(f'label.font="{FAMILY}:Regular:10.0"', self.read(".config/sketchybar/items/front_app.sh"))
        self.check_common()


del Base

if __name__ == "__main__":
    unittest.main()
