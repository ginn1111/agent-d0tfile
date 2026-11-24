import importlib.util
import json
import os
import sys
import tempfile
import threading
import types
import unittest
import warnings
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

PLUGIN = Path(__file__).resolve().parents[1] / "hermes" / "plugins" / "model-providers" / "gin1111"


class Gin1111ProviderTests(unittest.TestCase):
    def test_registers_openai_compatible_profile_with_coding_fallback(self):
        registered = []
        providers = types.ModuleType("providers")
        base = types.ModuleType("providers.base")
        setattr(base, "ProviderProfile", lambda **kwargs: kwargs)
        setattr(providers, "register_provider", registered.append)

        with patch.dict(sys.modules, {"providers": providers, "providers.base": base}):
            spec = importlib.util.spec_from_file_location("gin1111_test", PLUGIN / "__init__.py")
            if spec is None or spec.loader is None:
                self.fail("gin1111 provider module is missing or cannot be loaded")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

        self.assertEqual(len(registered), 1)
        self.assertEqual(registered[0]["name"], "gin1111")
        self.assertEqual(registered[0]["api_mode"], "chat_completions")
        self.assertEqual(registered[0]["auth_type"], "api_key")
        self.assertEqual(registered[0]["base_url"], "http://localhost:20128/v1")
        self.assertEqual(registered[0]["env_vars"], ("GIN1111_API_KEY", "GIN1111_BASE_URL"))
        self.assertEqual(registered[0]["fallback_models"], ("coding",))

    def test_manifest_identifies_a_model_provider(self):
        manifest = (PLUGIN / "plugin.yaml").read_text()
        self.assertIn("name: gin1111\n", manifest)
        self.assertIn("kind: model-provider\n", manifest)

    @unittest.skipUnless(os.getenv("HERMES_AGENT_SOURCE"), "set HERMES_AGENT_SOURCE for runtime integration")
    def test_real_picker_merges_authenticated_catalog_and_falls_back(self):
        class Catalog(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path != "/v1/models" or self.headers.get("Authorization") != "Bearer test-key":
                    self.send_error(401)
                    return
                payload = json.dumps({"data": [{"id": "fast"}, {"id": "coding"}]}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(payload)

            def log_message(self, format, *args):
                pass

        server = ThreadingHTTPServer(("127.0.0.1", 0), Catalog)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with tempfile.TemporaryDirectory(dir=os.getenv("TMPDIR")) as home:
                target = Path(home) / "plugins/model-providers/gin1111"
                target.parent.mkdir(parents=True)
                target.symlink_to(PLUGIN, target_is_directory=True)
                env = {"HERMES_HOME": home, "GIN1111_API_KEY": "test-key",
                       "GIN1111_BASE_URL": f"http://127.0.0.1:{server.server_port}/v1"}
                with patch.dict(os.environ, env), patch.object(sys, "path", [os.environ["HERMES_AGENT_SOURCE"], *sys.path]):
                    from providers import get_provider_profile
                    from hermes_cli.models import _profile_live_catalog, list_available_providers
                    from hermes_cli.runtime_provider import resolve_runtime_provider

                    profile = get_provider_profile("gin1111")
                    if profile is None:
                        self.fail("gin1111 was not discovered")
                    self.assertEqual(profile.name, "gin1111")
                    self.assertTrue(any(p["id"] == "gin1111" for p in list_available_providers()))
                    runtime = resolve_runtime_provider(requested="gin1111", target_model="coding")
                    self.assertEqual(runtime["api_mode"], "chat_completions")
                    self.assertEqual(runtime["api_key"], "test-key")
                    self.assertEqual(runtime["base_url"], env["GIN1111_BASE_URL"])
                    self.assertEqual(_profile_live_catalog("gin1111"), ["coding", "fast"])
                    with patch.dict(os.environ, {"GIN1111_API_KEY": "bad-key"}):
                        # Upstream Hermes leaves urllib's 401 response for GC; suppress its warning.
                        with warnings.catch_warnings():
                            warnings.simplefilter("ignore", ResourceWarning)
                            self.assertEqual(_profile_live_catalog("gin1111"), ["coding"])
                    with patch.dict(os.environ, {"GIN1111_API_KEY": ""}):
                        self.assertEqual(_profile_live_catalog("gin1111"), ["coding"])
        finally:
            server.shutdown()
            server.server_close()
            thread.join()


if __name__ == "__main__":
    unittest.main()
