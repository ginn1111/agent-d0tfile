import os
import pty
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "install-tool-theme.sh"
THEME = REPO_ROOT / "agent-tool-themes" / "cindy"

HERDR = """[theme]
name = "solarized"

[theme.custom]
accent = "#268bd3"

[terminal]
shell_mode = "auto"
"""


class InstallToolThemeTests(unittest.TestCase):
    def setUp(self):
        self.cfg = Path(tempfile.mkdtemp(prefix="tool-theme-test."))
        (self.cfg / "herdr").mkdir()
        (self.cfg / "herdr" / "config.toml").write_text(HERDR)
        (self.cfg / "starship.toml").write_text("old\n")

    def tearDown(self):
        shutil.rmtree(self.cfg)

    def _run(self, *args):
        env = os.environ.copy()
        env["TOOL_THEME_CONFIG_HOME"] = str(self.cfg)
        env.pop("TOOL_THEME", None)
        return subprocess.run(
            ["bash", str(SCRIPT), *args], cwd=REPO_ROOT, env=env,
            text=True, capture_output=True, check=True,
        )

    def test_list_writes_nothing(self):
        out = self._run("list", "cindy").stdout
        self.assertIn(f"link    {THEME / 'starship.toml'} -> {self.cfg / 'starship.toml'}", out)
        self.assertEqual((self.cfg / "starship.toml").read_text(), "old\n")
        self.assertFalse((self.cfg / "yazi").exists())

    def test_install_links_merges_and_is_idempotent(self):
        out = self._run("install", "cindy").stdout
        self.assertIn("linked=4 merged=1 unchanged=0", out)
        self.assertEqual(os.readlink(self.cfg / "starship.toml"), str(THEME / "starship.toml"))
        self.assertEqual(len(list(self.cfg.glob("starship.toml.bak-tooltheme-*"))), 1)

        herdr = (self.cfg / "herdr" / "config.toml").read_text()
        self.assertIn('accent = "#db302d"', herdr)
        self.assertNotIn("#268bd3\"\n\n[terminal]", herdr)
        self.assertEqual(herdr.splitlines().count("[theme.custom]"), 1)
        self.assertEqual(herdr.splitlines().count("[theme]"), 1)
        self.assertIn('[terminal]\nshell_mode = "auto"', herdr)

        out = self._run("install", "cindy").stdout
        self.assertIn("linked=0 merged=0 unchanged=5", out)

    def test_theme_hexes_come_from_palette(self):
        import re
        palette = set(re.findall(r"#[0-9a-f]{6}", (THEME / "solarized-osaka.palette").read_text().lower()))
        for f in THEME.rglob("*"):
            if f.is_file() and f.suffix in {".toml", ".lua"}:
                used = set(re.findall(r"#[0-9a-f]{6}", f.read_text().lower()))
                self.assertEqual(used - palette, set(), f.name)

    def test_interactive_picker(self):
        pid, fd = pty.fork()
        if pid == 0:
            env = os.environ.copy()
            env["TOOL_THEME_CONFIG_HOME"] = str(self.cfg)
            env.pop("TOOL_THEME", None)
            os.chdir(REPO_ROOT)
            os.execvpe("bash", ["bash", str(SCRIPT), "list"], env)
        os.write(fd, b"1\n")
        output = b""
        while True:
            try:
                chunk = os.read(fd, 1024)
            except OSError:
                break
            if not chunk:
                break
            output += chunk
        os.waitpid(pid, 0)
        text = output.decode()
        self.assertIn("Select tool theme:", text)
        self.assertIn("1) cindy", text)
        self.assertIn("starship.toml", text)


if __name__ == "__main__":
    unittest.main()
