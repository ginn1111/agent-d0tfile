import importlib.util
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


PLUGIN_PATH = Path("hermes-plugins/validated-mistery-loop/__init__.py")


def load_plugin_module():
    spec = importlib.util.spec_from_file_location("validated_mistery_loop", PLUGIN_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class FakePluginContext:
    def __init__(self):
        self.hooks = []
        self.skills = []
        self.commands = []

    def register_hook(self, name, callback):
        self.hooks.append((name, callback))

    def register_skill(self, name, path, description=""):
        self.skills.append({"name": name, "path": Path(path), "description": description})

    def register_command(self, name, handler, description="", args_hint=""):
        self.commands.append({
            "name": name,
            "handler": handler,
            "description": description,
            "args_hint": args_hint,
        })


class ValidatedMisteryLoopPluginTests(unittest.TestCase):
    def setUp(self):
        self.module = load_plugin_module()
        self.tmpdir = tempfile.TemporaryDirectory(prefix="vml-plugin-test.")
        self.root = Path(self.tmpdir.name)
        self.vml_root = self.root / "validated-mastery-loop"
        self.goal_dir = self.vml_root / "goals" / "cli-http-service"
        (self.goal_dir / "sessions").mkdir(parents=True)
        self._write_goal_files()

    def tearDown(self):
        self.tmpdir.cleanup()

    def _write(self, path: Path, content: str):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(textwrap.dedent(content).lstrip(), encoding="utf-8")

    def _write_goal_files(self):
        self._write(
            self.goal_dir / "goal.md",
            """
            # Goal: CLI HTTP Service

            **Capability map:** [[capability-map]]
            **Status:** Draft
            """,
        )
        self._write(
            self.goal_dir / "capability-map.md",
            """
            # Capability Map (VML)

            **Goal:** [[goal]]
            **Map status:** Confirmed

            ## CLI Framework (cobra)
            - **Why required:** commands
            - **Prerequisites:** Go basics
            - **Status:** Practising
            - **Validation state:** Probable
            - **Sources:** cobra docs
            - **Mastery criteria:** build commands
            - **Evidence:**
            - **Gaps:**
            - **Last validated:** 2026-07-25

            ## Structured Logging (slog)
            - **Why required:** logs
            - **Prerequisites:** Go basics
            - **Status:** Unknown
            - **Validation state:** Probable
            - **Sources:** slog docs
            - **Mastery criteria:** json logs
            - **Evidence:**
            - **Gaps:**
            - **Last validated:** 2026-07-25
            """,
        )
        self._write(
            self.goal_dir / "kanban.md",
            """
            # Kanban (VML)

            ## Backlog
            ## Next
            ## In Progress
            - **VML-2 | CLI Framework (cobra)** `card-1`
              - **Objective:** Build root + serve
              - **Acceptance:** `serve --help` shows flags; `--port 9090` changes listen addr
              - **Scope:** cmd/root.go
              - **Evidence:**
            ## Blocked
            ## Review
            ## Done
            """,
        )
        self._write(
            self.goal_dir / "knowledge.md",
            """
            # Knowledge
            ## Principles
            ## Mental models
            ## Important mistakes
            ## Debugging patterns
            ## Architecture decisions
            """,
        )
        self._write(
            self.goal_dir / "sessions" / "_session-template.md",
            """
            # Session: {{capability}}

            Goal: [[goal]]
            Capability: {{capability}}
            Date: {{date}}
            """,
        )

    def test_plugin_yaml_declares_validated_mistery_loop_metadata(self):
        text = Path("hermes-plugins/validated-mistery-loop/plugin.yaml").read_text()
        self.assertIn("name: validated-mistery-loop", text)

    def test_discovery_finds_goal_and_capabilities(self):
        goals = self.module.discover_goals(self.vml_root)
        self.assertEqual([goal.slug for goal in goals], ["cli-http-service"])
        self.assertEqual(goals[0].goal_title, "CLI HTTP Service")
        self.assertEqual(goals[0].capabilities[0].name, "CLI Framework (cobra)")

    def test_check_report_flags_missing_goal_backlink(self):
        (self.goal_dir / "goal.md").write_text("# Goal: Broken\n", encoding="utf-8")
        report = self.module.build_check_report(self.vml_root)
        messages = "\n".join(report["issues"])
        self.assertIn("missing [[capability-map]]", messages)

    def test_check_report_flags_multiple_in_progress_cards(self):
        kanban = (self.goal_dir / "kanban.md").read_text(encoding="utf-8")
        kanban = kanban.replace(
            "## In Progress\n- **VML-2 | CLI Framework (cobra)** `card-1`\n  - **Objective:** Build root + serve\n  - **Acceptance:** `serve --help` shows flags; `--port 9090` changes listen addr\n  - **Scope:** cmd/root.go\n  - **Evidence:**\n",
            "## In Progress\n- **VML-2 | CLI Framework (cobra)** `card-1`\n  - **Objective:** Build root + serve\n  - **Acceptance:** `serve --help` shows flags; `--port 9090` changes listen addr\n  - **Scope:** cmd/root.go\n  - **Evidence:**\n- **VML-3 | Structured Logging (slog)** `card-2`\n  - **Objective:** Build slog\n  - **Acceptance:** json logs\n  - **Scope:** internal/log\n  - **Evidence:**\n",
        )
        (self.goal_dir / "kanban.md").write_text(kanban, encoding="utf-8")
        report = self.module.build_check_report(self.vml_root)
        self.assertTrue(any("multiple In Progress" in item for item in report["issues"]))

    def test_review_report_lists_active_goal_and_capabilities(self):
        report = self.module.build_review_report(self.vml_root)
        self.assertEqual(report["active_goal"], "cli-http-service")
        self.assertEqual(report["in_progress"][0]["capability"], "CLI Framework (cobra)")
        self.assertIn("Practising", report["capability_statuses"])

    def test_start_creates_session_and_moves_capability_to_in_progress(self):
        kanban = (self.goal_dir / "kanban.md").read_text(encoding="utf-8").replace(
            "## In Progress\n- **VML-2 | CLI Framework (cobra)** `card-1`\n  - **Objective:** Build root + serve\n  - **Acceptance:** `serve --help` shows flags; `--port 9090` changes listen addr\n  - **Scope:** cmd/root.go\n  - **Evidence:**\n",
            "## In Progress\n",
        ).replace(
            "## Next\n",
            "## Next\n- **VML-2 | CLI Framework (cobra)** `card-1`\n  - **Objective:** Build root + serve\n  - **Acceptance:** `serve --help` shows flags; `--port 9090` changes listen addr\n  - **Scope:** cmd/root.go\n  - **Evidence:**\n",
        )
        (self.goal_dir / "kanban.md").write_text(kanban, encoding="utf-8")
        result = self.module.start_capability(self.vml_root, "CLI Framework (cobra)")
        self.assertEqual(result["goal"], "cli-http-service")
        self.assertTrue(Path(result["session_path"]).exists())
        kanban_now = (self.goal_dir / "kanban.md").read_text(encoding="utf-8")
        self.assertIn("## In Progress\n- **VML-2 | CLI Framework (cobra)** `card-1`", kanban_now)

    def test_validate_reports_per_acceptance_and_updates_files(self):
        result = self.module.validate_active_goal(
            self.vml_root,
            output_text="serve --help shows flags and port changes to 9090",
            evidence_ref="tests/evidence.txt",
        )
        self.assertEqual([item["passed"] for item in result["checks"]], [True, True])
        kanban_now = (self.goal_dir / "kanban.md").read_text(encoding="utf-8")
        self.assertIn("## Done", kanban_now)
        self.assertIn("tests/evidence.txt", kanban_now)
        capability_map = (self.goal_dir / "capability-map.md").read_text(encoding="utf-8")
        self.assertIn("- **Status:** Demonstrated", capability_map)
        knowledge = (self.goal_dir / "knowledge.md").read_text(encoding="utf-8")
        self.assertIn("[[CLI Framework (cobra)]]", knowledge)

    def test_stress_builds_questions_and_follow_up(self):
        questions = self.module.build_stress_questions(
            capability_name="CLI Framework (cobra)",
            output_text="built cobra CLI with root and serve command",
        )
        self.assertEqual(len(questions), 3)
        strong = self.module.build_follow_up_question(
            capability_name="CLI Framework (cobra)",
            answer_text="I would use persistent flags on root for shared config and local flags for serve-only behavior.",
        )
        weak = self.module.build_follow_up_question(
            capability_name="CLI Framework (cobra)",
            answer_text="not sure",
        )
        self.assertIn("trade-off", strong.lower())
        self.assertIn("what does", weak.lower())

    def test_dispatch_parses_vml_commands(self):
        parsed = self.module.parse_vml_command('vml start "CLI Framework (cobra)"')
        self.assertEqual(parsed["command"], "start")
        self.assertEqual(parsed["argument"], "CLI Framework (cobra)")

    def test_register_bundles_plugin_skills(self):
        ctx = FakePluginContext()
        self.module.register(ctx)
        names = sorted(item["name"] for item in ctx.skills)
        self.assertEqual(names, ["vml-check", "vml-review", "vml-start", "vml-stress", "vml-validate"])
        for item in ctx.skills:
            self.assertTrue(item["path"].exists())
            self.assertEqual(item["path"].name, "SKILL.md")

    def test_register_plugin_commands(self):
        ctx = FakePluginContext()
        self.module.register(ctx)
        names = sorted(item["name"] for item in ctx.commands)
        self.assertEqual(names, ["vml-check", "vml-review", "vml-start", "vml-stress", "vml-validate"])
        hints = {item["name"]: item["args_hint"] for item in ctx.commands}
        self.assertEqual(hints["vml-check"], "")
        self.assertEqual(hints["vml-review"], "")
        self.assertEqual(hints["vml-start"], "<capability>")
        self.assertEqual(hints["vml-validate"], "<output> | <evidence>")
        self.assertEqual(hints["vml-stress"], "[capability]")

    def test_registered_command_handlers_return_text(self):
        ctx = FakePluginContext()
        self.module.register(ctx)
        handlers = {item["name"]: item["handler"] for item in ctx.commands}
        self.assertIn("VML check", handlers["vml-check"](str(self.vml_root)))
        self.assertIn("Active goal", handlers["vml-review"](str(self.vml_root)))
        self.assertIn("Usage: /vml-start <capability>", handlers["vml-start"](""))
        self.assertIn("Usage: /vml-validate <output> | <evidence>", handlers["vml-validate"]("bad"))
        self.assertIn("Stress target", handlers["vml-stress"]("CLI Framework (cobra)"))


if __name__ == "__main__":
    unittest.main()
