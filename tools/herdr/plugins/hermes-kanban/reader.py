"""Read Hermes board snapshots without importing Hermes or running its mutators."""

import argparse
import json
import os
from pathlib import Path
import re
import signal
import sqlite3
import time


def root_path(explicit=None):
    if explicit or os.environ.get("HERMES_KANBAN_HOME"):
        return Path(explicit or os.environ["HERMES_KANBAN_HOME"]).expanduser().resolve()
    native = Path.home() / ".hermes"
    home = Path(os.path.expandvars(os.environ.get("HERMES_HOME") or str(native))).expanduser()
    if home.resolve().is_relative_to(native.resolve()):
        return native.resolve()
    return (home.parent.parent if home.parent.name == "profiles" else home).resolve()


def catalog(root, pinned=None):
    if pinned:
        return [{"slug": "pinned", "name": "Pinned database", "path": str(pinned)}]
    boards = [{"slug": "default", "name": "Default", "path": str(root / "kanban.db")}]
    directory = root / "kanban" / "boards"
    if directory.is_dir():
        for child in sorted(directory.iterdir()):
            if not re.fullmatch(r"[a-z0-9][a-z0-9_-]*", child.name):
                continue
            metadata = child / "board.json"
            if not metadata.is_file():
                continue
            meta = json.loads(metadata.read_text(encoding="utf-8-sig"))
            if not isinstance(meta, dict):
                raise ValueError("Invalid board metadata: " + str(metadata))
            if child.name == "default":
                boards[0]["name"] = str(meta.get("name") or "Default")
            elif not meta.get("archived"):
                boards.append({"slug": child.name, "name": str(meta.get("name") or child.name),
                               "path": str(child / "kanban.db")})
    return boards


def read_board(path):
    # ponytail: local Hermes SQLite schema only; use a read-only export API when available.
    conn = sqlite3.connect(Path(path).resolve().as_uri() + "?mode=ro", uri=True, timeout=1)
    try:
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA query_only = ON")
        deadline = time.monotonic() + 4
        conn.set_progress_handler(lambda: int(time.monotonic() > deadline), 10000)
        conn.execute("BEGIN")
        columns = {r[1] for r in conn.execute("PRAGMA table_info(tasks)")}
        if not {"id", "title", "status"}.issubset(columns):
            raise ValueError("Unsupported Hermes tasks schema in " + str(path))
        fields = ["id", "title", "status", "assignee", "body", "result", "block_kind",
                  "last_failure_error", "consecutive_failures", "priority"]
        selected = [f for f in fields if f in columns]
        tasks = [dict(r) for r in conn.execute(
            "SELECT " + ", ".join(selected) + " FROM tasks WHERE status != 'archived' ORDER BY id")]
        tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if "task_links" not in tables:
            raise ValueError("Unsupported Hermes schema: task_links table missing")
        links = [list(r) for r in conn.execute("SELECT parent_id, child_id FROM task_links ORDER BY 1, 2")]
        by_id = {t["id"]: t for t in tasks}
        if "task_events" in tables:
            for row in conn.execute("""
                SELECT task_id, payload FROM task_events WHERE id IN (
                    SELECT MAX(id) FROM task_events WHERE kind = 'blocked' GROUP BY task_id
                )
            """):
                if row["task_id"] in by_id:
                    try:
                        payload = json.loads(row["payload"] or "{}")
                        if isinstance(payload, dict):
                            by_id[row["task_id"]]["block_reason"] = str(payload.get("reason") or "")
                    except (TypeError, ValueError):
                        pass
        if "task_comments" in tables:
            for row in conn.execute("""
                SELECT task_id, author, body FROM (
                    SELECT task_id, author, body, id,
                        ROW_NUMBER() OVER (PARTITION BY task_id ORDER BY id DESC) AS n
                    FROM task_comments
                ) WHERE n <= 3 ORDER BY id
            """):
                if row["task_id"] in by_id:
                    by_id[row["task_id"]].setdefault("comments", []).append(
                        str(row["author"]) + ": " + str(row["body"]))
        for task in tasks:
            for field in fields:
                if field in ("consecutive_failures", "priority"):
                    task[field] = int(task.get(field) or 0)
                else:
                    task[field] = str(task.get(field) or "")
            task.setdefault("comments", [])
            task.setdefault("block_reason", "")
        return tasks, links
    finally:
        conn.close()


def snapshot(root, board="", pinned=None):
    root = Path(root).resolve()
    pinned = Path(pinned).expanduser().resolve() if pinned else None
    boards = catalog(root, pinned)
    current_path = root / "kanban" / "current"
    current = os.environ.get("HERMES_KANBAN_BOARD", "")
    if not current and current_path.is_file():
        current = current_path.read_text(encoding="utf-8-sig").strip()
    slugs = {b["slug"] for b in boards}
    selected = board or ("pinned" if pinned else current if current in slugs else "default")
    result = {"scope": str(pinned or root), "board": selected, "boards": boards,
              "tasks": [], "links": [], "error": None}
    try:
        if selected not in slugs:
            raise ValueError("Board unavailable: " + selected + ". Press b to choose another board.")
        path = next(b["path"] for b in boards if b["slug"] == selected)
        result["tasks"], result["links"] = read_board(path)
    except (OSError, sqlite3.Error, ValueError) as exc:
        result["error"] = str(exc)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", help="Hermes shared Kanban root")
    parser.add_argument("--board", default="", help="Board slug; does not change Hermes current board")
    parser.add_argument("--db", help="Read one explicitly selected database")
    args = parser.parse_args()
    signal.alarm(8)
    try:
        print(json.dumps(snapshot(root_path(args.root), args.board,
                                  args.db or os.environ.get("HERMES_KANBAN_DB"))))
    except (OSError, sqlite3.Error, ValueError) as exc:
        parser.exit(1, str(exc) + "\n")
