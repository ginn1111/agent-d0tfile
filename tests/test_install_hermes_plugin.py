import importlib.util
import os
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "install_hermes_plugin.py"
_SPEC = importlib.util.spec_from_file_location("install_hermes_plugin", SCRIPT)
assert _SPEC is not None and _SPEC.loader is not None
cli = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = cli
_SPEC.loader.exec_module(cli)


class InstallHermesPluginTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=os.getenv("TMPDIR"))
        self.root = Path(self.tmp.name)
        self.plugins_root = self.root / "repo" / "hermes" / "plugins"
        self.hermes_root = self.root / "hermes-home"
        self.hermes_root.mkdir(parents=True)
        (self.hermes_root / "profiles" / "ginb").mkdir(parents=True)
        (self.hermes_root / "profiles" / "cindy").mkdir(parents=True)

        # Model provider plugin
        mp = self.plugins_root / "model-providers" / "gin1111"
        mp.mkdir(parents=True)
        (mp / "plugin.yaml").write_text("name: gin1111\nkind: model-provider\n", encoding="utf-8")
        (mp / "__init__.py").write_text("# gin1111\n", encoding="utf-8")

        # Regular plugin
        reg = self.plugins_root / "english-tutor"
        reg.mkdir(parents=True)
        (reg / "plugin.yaml").write_text("name: english-tutor\n", encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def test_discover_plugins_finds_model_providers_and_regular_plugins(self):
        plugins = cli.discover_plugins(self.plugins_root)
        by_name = {p.name: p for p in plugins}
        self.assertEqual(set(by_name.keys()), {"gin1111", "english-tutor"})
        self.assertEqual(by_name["gin1111"].kind, "model-provider")
        self.assertEqual(by_name["gin1111"].target_relpath, Path("plugins/model-providers/gin1111"))
        self.assertEqual(by_name["english-tutor"].target_relpath, Path("plugins/english-tutor"))

    def test_install_symlinks_model_provider_into_profile_and_is_idempotent(self):
        rc = cli.main([
            "--hermes-root", str(self.hermes_root),
            "--plugins-root", str(self.plugins_root),
            "install", "gin1111", "--profile", "ginb",
        ])
        self.assertEqual(rc, 0)
        dest = self.hermes_root / "profiles" / "ginb" / "plugins" / "model-providers" / "gin1111"
        self.assertTrue(dest.is_symlink())
        self.assertEqual(dest.resolve(), (self.plugins_root / "model-providers" / "gin1111").resolve())

        # Re-running is idempotent
        rc2 = cli.main([
            "--hermes-root", str(self.hermes_root),
            "--plugins-root", str(self.plugins_root),
            "install", "gin1111", "--profile", "ginb",
        ])
        self.assertEqual(rc2, 0)

    def test_install_refuses_existing_dir_without_force_and_overwrites_with_force(self):
        dest = self.hermes_root / "profiles" / "ginb" / "plugins" / "model-providers" / "gin1111"
        dest.mkdir(parents=True)
        (dest / "old.txt").write_text("old", encoding="utf-8")

        with self.assertRaises(SystemExit):
            cli.main([
                "--hermes-root", str(self.hermes_root),
                "--plugins-root", str(self.plugins_root),
                "install", "gin1111", "--profile", "ginb",
            ])

        rc = cli.main([
            "--hermes-root", str(self.hermes_root),
            "--plugins-root", str(self.plugins_root),
            "install", "gin1111", "--profile", "ginb", "--force",
        ])
        self.assertEqual(rc, 0)
        self.assertTrue(dest.is_symlink())

    def test_copy_and_uninstall(self):
        rc = cli.main([
            "--hermes-root", str(self.hermes_root),
            "--plugins-root", str(self.plugins_root),
            "install", "english-tutor", "--profile", "cindy", "--copy",
        ])
        self.assertEqual(rc, 0)
        dest = self.hermes_root / "profiles" / "cindy" / "plugins" / "english-tutor"
        self.assertTrue(dest.is_dir())
        self.assertFalse(dest.is_symlink())

        rc2 = cli.main([
            "--hermes-root", str(self.hermes_root),
            "--plugins-root", str(self.plugins_root),
            "uninstall", "english-tutor", "--profile", "cindy",
        ])
        self.assertEqual(rc2, 0)
        self.assertFalse(dest.exists())

    def test_profile_all_installs_and_uninstalls_every_profile(self):
        rc = cli.main([
            "--hermes-root", str(self.hermes_root),
            "--plugins-root", str(self.plugins_root),
            "install", "gin1111", "--profile", "all",
        ])
        self.assertEqual(rc, 0)
        for pdir in (
            self.hermes_root,
            self.hermes_root / "profiles" / "cindy",
            self.hermes_root / "profiles" / "ginb",
        ):
            self.assertTrue((pdir / "plugins" / "model-providers" / "gin1111").is_symlink())

        rc2 = cli.main([
            "--hermes-root", str(self.hermes_root),
            "--plugins-root", str(self.plugins_root),
            "uninstall", "gin1111", "--profile", "all",
        ])
        self.assertEqual(rc2, 0)
        for pdir in (
            self.hermes_root,
            self.hermes_root / "profiles" / "cindy",
            self.hermes_root / "profiles" / "ginb",
        ):
            self.assertFalse((pdir / "plugins" / "model-providers" / "gin1111").exists())


if __name__ == "__main__":
    unittest.main()
