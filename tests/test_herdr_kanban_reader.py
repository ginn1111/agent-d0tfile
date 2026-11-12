"""Read-only contract against isolated, live SQLite boards."""

import hashlib
from contextlib import closing
import importlib.util
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[1] / "herdr-plugins/hermes-kanban/reader.py"
spec = importlib.util.spec_from_file_location("kanban_reader", SOURCE)
reader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reader)


def make_db(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(path)) as conn:
        conn.executescript("""
            CREATE TABLE tasks (id TEXT PRIMARY KEY, title TEXT, status TEXT,
                                body TEXT, consecutive_failures INTEGER, priority INTEGER);
            CREATE TABLE task_links (parent_id TEXT, child_id TEXT);
            CREATE TABLE task_events (id INTEGER, task_id TEXT, kind TEXT, payload TEXT);
            CREATE TABLE task_comments (id INTEGER, task_id TEXT, author TEXT, body TEXT);
            INSERT INTO tasks VALUES ('t_a', 'Blocked card', 'blocked', 'Details', 2, 1);
            INSERT INTO tasks VALUES ('t_b', 'Unknown state', 'custom-state', NULL, NULL, 0);
            INSERT INTO tasks VALUES ('t_c', 'History', 'archived', NULL, 0, 0);
            INSERT INTO task_links VALUES ('t_a', 't_b');
            INSERT INTO task_events VALUES (1, 't_a', 'blocked', '{"reason":"Needs approval"}');
            INSERT INTO task_comments VALUES (1, 't_a', 'reviewer', 'Check credentials');
        """)


class ReaderTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="herdr-kanban-test-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.db = self.root / "kanban.db"
        make_db(self.db)
        self.env = patch.dict(os.environ, {"HERMES_KANBAN_BOARD": ""})
        self.env.start()
        self.addCleanup(self.env.stop)

    def test_snapshot_preserves_database_and_unknown_states(self):
        before = hashlib.sha256(self.db.read_bytes()).digest()
        data = reader.snapshot(self.root)
        self.assertIsNone(data["error"])
        self.assertEqual([t["status"] for t in data["tasks"]], ["blocked", "custom-state"])
        self.assertEqual(data["tasks"][0]["block_reason"], "Needs approval")
        self.assertEqual(data["tasks"][0]["comments"], ["reviewer: Check credentials"])
        self.assertEqual(data["links"], [["t_a", "t_b"]])
        self.assertEqual(hashlib.sha256(self.db.read_bytes()).digest(), before)

    def test_live_wal_updates_are_visible(self):
        conn = sqlite3.connect(self.db)
        self.addCleanup(conn.close)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("UPDATE tasks SET status='review' WHERE id='t_a'")
        conn.commit()
        self.assertEqual(reader.snapshot(self.root)["tasks"][0]["status"], "review")
        conn.execute("UPDATE tasks SET status='done' WHERE id='t_a'")
        conn.commit()
        self.assertEqual(reader.snapshot(self.root)["tasks"][0]["status"], "done")

    def test_selection_and_archived_boards(self):
        for slug, archived in [("work", False), ("old", True)]:
            directory = self.root / "kanban/boards" / slug
            make_db(directory / "kanban.db")
            (directory / "board.json").write_text(json.dumps({"name": slug, "archived": archived}))
        current = self.root / "kanban/current"
        current.write_text("work")
        data = reader.snapshot(self.root, "default")
        self.assertEqual(data["board"], "default")
        self.assertEqual([b["slug"] for b in data["boards"]], ["default", "work"])
        self.assertEqual(current.read_text(), "work")
        self.assertEqual(reader.snapshot(self.root)["board"], "work")
        self.assertIsNotNone(reader.snapshot(self.root, "../work")["error"])

    def test_missing_or_incompatible_db_does_not_create_or_migrate(self):
        absent = self.root / "missing.db"
        self.assertIsNotNone(reader.snapshot(self.root, pinned=absent)["error"])
        self.assertFalse(absent.exists())
        broken = self.root / "broken.db"
        with closing(sqlite3.connect(broken)) as conn:
            conn.execute("CREATE TABLE tasks (id TEXT)")
        self.assertIn("Unsupported", reader.snapshot(self.root, pinned=broken)["error"])

    def test_pinned_database_and_custom_profile_root(self):
        custom = self.root / "other.db"
        make_db(custom)
        data = reader.snapshot(self.root, pinned=custom)
        self.assertEqual([b["slug"] for b in data["boards"]], ["pinned"])
        self.assertEqual(data["scope"], str(custom))
        with patch.dict(os.environ, {"HERMES_KANBAN_HOME": "", "HERMES_HOME": str(self.root / "profiles/test")}):
            self.assertEqual(reader.root_path(), self.root)


if __name__ == "__main__":
    unittest.main()
