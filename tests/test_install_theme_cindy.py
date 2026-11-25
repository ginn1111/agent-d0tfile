import os
import subprocess
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "scripts" / "install_theme_cindy.py"
THEME = REPO / "themes" / "cindy"

FIXTURES = {
    ".config/kitty/kitty.conf": "font_size 12\n# include gruvbox.conf\ninclude solarized_osaka_dark.conf\n",
    ".config/yazi/theme.toml": '[app]\noverall = { fg = "#9eabac" }\n',
    ".config/lazygit/config.yml": "",
    ".config/nvim/lua/plugins/solarized.lua": "return {}\n",
    ".config/nvim/lua/plugins/lualine.lua": "return {}\n",
    ".config/herdr/config.toml": 'name = "solarized"\n\n[theme.custom]\naccent = "#268bd3"\n\n[terminal]\nshell_mode = "auto"\n',
    "dotfiles/starship.toml": 'palette = "solarized"\n\n[palettes.solarized]\ngreen = "#859900"\n\n[character]\nsuccess_symbol = "[>](green)"\n',
    ".hermes/profiles/cindy/config.yaml": "display:\n  skin: solarized-osaka-cindy\n  language: en\n",
    ".hermes/profiles/cindy/skins/solarized-osaka-cindy.yaml": "name: x\n",
    ".hermes/profiles/ginb/config.yaml": "display:\n  skin: solarized-osaka-ginb\n",
    ".hermes/profiles/ginb/skins/solarized-osaka-ginb.yaml": "name: y\n",
}

LINKS = {
    ".config/kitty/black_ruby.conf": "kitty.conf",
    ".config/yazi/theme.toml": "yazi-theme.toml",
    ".config/lazygit/config.yml": "lazygit.yml",
    ".config/nvim/lua/plugins/colorscheme.lua": "nvim/colorscheme.lua",
    ".config/nvim/lua/plugins/lualine.lua": "nvim/lualine.lua",
    ".hermes/profiles/cindy/skins/vscode-cindy.yaml": "hermes-skin.yaml",
    ".hermes/profiles/ginb/skins/vscode-ginb.yaml": "hermes-skin-ginb.yaml",
}


def snapshot(home):
    out = {}
    for p in sorted(home.rglob("*")):
        rel = str(p.relative_to(home))
        if p.is_symlink():
            out[rel] = ("link", os.readlink(p))
        elif p.is_file():
            out[rel] = ("file", p.read_bytes())
        else:
            out[rel] = ("dir", None)
    return out


class InstallThemeCindyTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name)
        for rel, text in FIXTURES.items():
            p = self.home / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text)
        # Real setup: ~/.config/starship.toml is a symlink into another repo.
        (self.home / ".config/starship.toml").symlink_to(self.home / "dotfiles/starship.toml")
        self.original = snapshot(self.home)

    def tearDown(self):
        self.tmp.cleanup()

    def run_script(self, *args):
        # Profile sessions export HERMES_HOME=<root>/profiles/<name>; the script must not nest under it.
        env = {**os.environ, "HOME": str(self.home), "HERMES_HOME": str(self.home / ".hermes/profiles/cindy")}
        r = subprocess.run([sys.executable, str(SCRIPT), *args], env=env, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return r.stdout

    def test_dry_run_writes_nothing(self):
        out = self.run_script("--dry-run")
        self.assertIn("would link", out)
        self.assertIn("would edit", out)
        self.assertEqual(snapshot(self.home), self.original)

    def test_install_links_edits_and_backs_up(self):
        self.run_script()
        for rel, src in LINKS.items():
            self.assertEqual((self.home / rel).resolve(), (THEME / src).resolve(), rel)
        plugins = self.home / ".config/nvim/lua/plugins"
        self.assertFalse((plugins / "solarized.lua").exists())
        self.assertEqual(len(list(plugins.glob("solarized.lua.pre-cindy.*"))), 1)
        kitty = (self.home / ".config/kitty/kitty.conf").read_text()
        self.assertIn("# include solarized_osaka_dark.conf", kitty)
        self.assertIn("\ninclude black_ruby.conf\n", kitty)
        herdr = tomllib.loads((self.home / ".config/herdr/config.toml").read_text())
        self.assertEqual(herdr["theme"]["custom"]["accent"], "#0078d4")
        self.assertEqual(herdr["terminal"]["shell_mode"], "auto")
        star_link = self.home / ".config/starship.toml"
        self.assertTrue(star_link.is_symlink(), "edit must write through the symlink")
        star = tomllib.loads(star_link.read_text())
        self.assertEqual(star["palette"], "black_ruby")
        self.assertEqual(set(star["palettes"]), {"black_ruby"})
        self.assertIn("  skin: vscode-cindy\n", (self.home / ".hermes/profiles/cindy/config.yaml").read_text())
        self.assertIn("  skin: vscode-ginb\n", (self.home / ".hermes/profiles/ginb/config.yaml").read_text())

    def test_install_leaves_cindy_starship_palette_alone(self):
        live = 'palette = "cindy"\n\n[palettes.cindy]\nfg = "#d6cbb8"\n'
        (self.home / "dotfiles/starship.toml").write_text(live)
        self.run_script()
        self.assertEqual((self.home / "dotfiles/starship.toml").read_text(), live)

    def test_install_retires_dangling_bearded_link(self):
        plugins = self.home / ".config/nvim/lua/plugins"
        (plugins / "bearded.lua").symlink_to(self.home / "gone/bearded.lua")
        self.run_script()
        self.assertFalse((plugins / "bearded.lua").is_symlink())
        self.assertEqual(len(list(plugins.glob("bearded.lua.pre-cindy.*"))), 1)

    def test_second_run_is_noop(self):
        self.run_script()
        after = snapshot(self.home)
        out = self.run_script()
        self.assertEqual(snapshot(self.home), after)
        self.assertTrue(all(line.startswith("ok ") for line in out.splitlines()), out)

    def test_restore_returns_original(self):
        self.run_script()
        installed = snapshot(self.home)
        self.run_script("--restore", "--dry-run")
        self.assertEqual(snapshot(self.home), installed)
        self.run_script("--restore")
        self.assertEqual(snapshot(self.home), self.original)


if __name__ == "__main__":
    unittest.main()
