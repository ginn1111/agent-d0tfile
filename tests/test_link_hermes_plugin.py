import os
import pty
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "link-hermes-plugin.sh"
PLUGIN_ROOT = REPO_ROOT / "hermes-plugins" / "english-tutor"


class LinkHermesPluginScriptTests(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp(prefix="hermes-plugin-test."))
        (self.tmpdir / "profiles" / "tester").mkdir(parents=True)

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def _env(self):
        env = os.environ.copy()
        env["HERMES_HOME"] = str(self.tmpdir)
        return env

    def test_list_with_explicit_plugin_name_prints_target(self):
        result = subprocess.run(
            [str(SCRIPT), "list", "tester", "english-tutor"],
            cwd=REPO_ROOT,
            env=self._env(),
            text=True,
            capture_output=True,
            check=True,
        )

        expected = (
            f"{PLUGIN_ROOT} -> "
            f"{self.tmpdir / 'profiles' / 'tester' / 'plugins' / 'english-tutor'}"
        )
        self.assertEqual(result.stdout.strip(), expected)
        self.assertEqual(result.stderr, "")

    def test_list_interactive_picker_selects_profile_and_plugin(self):
        pid, fd = pty.fork()
        if pid == 0:
            os.chdir(REPO_ROOT)
            os.execvpe("bash", ["bash", str(SCRIPT), "list"], self._env())

        output = b""
        try:
            os.write(fd, b"1\n")
            os.write(fd, b"1\n")
            while True:
                try:
                    chunk = os.read(fd, 1024)
                    if not chunk:
                        break
                    output += chunk
                except OSError:
                    break
        finally:
            _, status = os.waitpid(pid, 0)

        text = output.decode("utf-8", "replace")
        self.assertEqual(os.waitstatus_to_exitcode(status), 0, text)
        self.assertIn("Select Hermes profile:", text)
        self.assertIn("Select plugin:", text)
        self.assertIn(str(PLUGIN_ROOT), text)
        self.assertIn(
            str(self.tmpdir / "profiles" / "tester" / "plugins" / "english-tutor"),
            text,
        )


if __name__ == "__main__":
    unittest.main()
