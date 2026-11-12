# Plan: feat-006 Live Hermes Kanban TUI (Herdr popup)

## Goal

Replace placeholder popup in `herdr-plugins/hermes-kanban/` with a read-only Ratatui + Rataflow TUI that shows one Hermes Kanban board as a dependency graph. It highlights cards that need attention, remembers the chosen board, has a details panel, and shows refresh status so stale data is visible.

## Current context (verified 2026-10-28)

- `feature_list.json` has `feat-006` `in-progress`. Its dependency, feat-005, is done.
- `herdr-plugins/hermes-kanban/` is untracked. It contains:
  - `herdr-plugin.toml`: popup 90%x85%, `command = ["bash", "herdr/board.sh"]`.
  - `herdr/board.sh`: placeholder text. `herdr/open.sh` is the launcher (keep as is).
  - `Cargo.toml`: crate `hermes-kanban-tui`, edition 2024, deps `ratatui 0.30` (crossterm feature), `rataflow 0.1.0`, `crossterm 0.29`, `serde`, `serde_json`. `Cargo.lock` exists. Crates are already in `~/.cargo/registry`.
  - `src/main.rs`: `fn main() {}` stub.
  - `reader.py`: stdlib-only snapshot reader. It reads Hermes SQLite read-only (`mode=ro`) and prints JSON `{scope, board, boards[{slug,name,path}], tasks[...], links[[parent,child]], error}`.
- Toolchain: `cargo 1.98.1`, system `python3` 3.9.6, SQLite 3.51.0.
- **Bug found:** `python3 reader.py --board vmas` returns `error: "unable to open database file"`. Per-board DBs (`~/.hermes/kanban/boards/<slug>/kanban.db`) are in WAL mode with an empty `-wal` and no `-shm` file, so a `mode=ro` connection cannot open them. `?mode=ro&immutable=1` opens them (7 tasks). The default board (`~/.hermes/kanban.db`, which has `-shm`) works: 147 tasks, 31 links.
- Supported API check: `hermes kanban list --json` takes about 2.4 s and returns no links. `show --json` gives `parents`/`children` per task, so building the graph would need N calls (too slow for refresh). Decision: keep the SQLite reader and treat the schema coupling as a known risk (`ponytail:` comment already in `reader.py`).
- Rataflow API facts (from `~/.cargo/registry/src/*/rataflow-0.1.0`):
  - Core calls: `Flow::with_graph(nodes, edges) -> Result<Flow, Error>`, `Node::new(id, (x,y), (w,h), TextContent)`, `Edge::new(id, src, tgt)`, and `flow.apply_layout(Sugiyama::vertical())`.
  - Selection and view: `select_node`, `first_selected_node_id`, `center_on_selected`, `request_fit_view`.
  - Input: `handle_key_event(impl Into<KeyEvent>)` (crossterm `From` impls exist), plus `default_controls_key_binding` with `apply_controls_action`.
  - Rendering: `impl Widget for &mut Flow`.
  - **`with_locked(true)` blocks selection navigation too**, so do not lock the flow. Make nodes non-draggable/deletable/connectable instead, and filter mutating keys yourself (`Delete`, `Backspace`, `m`, `i`).
  - `with_graph` errors on edges to unknown nodes. Drop links to archived or missing tasks.
- Herdr popup contract: no pane ID, Escape is delivered to the app, popup closes when the process exits. Plugin state dir is `HERDR_PLUGIN_STATE_DIR` (may be unset; then don't persist).
- Repo rules: `./init.sh` must pass. No Hermes profile mutation. Do not commit unless gin approves (dirty tree, feat-003, main/develop split). In the steps below, "commit" means *stage selectively only if approved*.

## Approach

Rust binary polls `python3 reader.py --board <slug>` in a background thread every 5 s while the popup is open. It parses the JSON into `Snapshot` and rebuilds the Rataflow graph only when the data changes, keeping the selected card. Attention means `blocked`, `review`, a non-empty `last_failure_error`, or `consecutive_failures > 0`. These cards get colored borders and receive first focus. A status bar shows board, read mode, counts, last good refresh age, and the latest error.

## Tasks

### T1: Reader fallback for WAL boards without `-shm` (TDD, Python)

1. Create `tests/test_hermes_kanban_reader.py`:

```python
import importlib.util
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location(
    "hk_reader", REPO / "herdr-plugins" / "hermes-kanban" / "reader.py")
reader = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(reader)


def make_board(root, slug, wal):
    d = root / "kanban" / "boards" / slug
    d.mkdir(parents=True)
    (d / "board.json").write_text(json.dumps({"slug": slug, "name": slug.title()}))
    db = d / "kanban.db"
    c = sqlite3.connect(db)
    c.executescript(("PRAGMA journal_mode=WAL;" if wal else "") + """
        CREATE TABLE tasks(id TEXT PRIMARY KEY, title TEXT, status TEXT, assignee TEXT);
        CREATE TABLE task_links(parent_id TEXT, child_id TEXT);
        INSERT INTO tasks VALUES ('t1','One','blocked','a'), ('t2','Two','todo',NULL),
                                 ('t3','Old','archived',NULL);
        INSERT INTO task_links VALUES ('t1','t2');
    """)
    c.close()
    return db


class ReaderTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_live_read_skips_archived(self):
        make_board(self.root, "x", wal=False)
        s = reader.snapshot(self.root, "x")
        self.assertIsNone(s["error"])
        self.assertEqual([t["id"] for t in s["tasks"]], ["t1", "t2"])
        self.assertEqual(s["links"], [["t1", "t2"]])
        self.assertEqual(s["consistency"], "live")

    def test_wal_without_shm_falls_back_to_immutable(self):
        db = make_board(self.root, "x", wal=True)
        Path(str(db) + "-wal").write_bytes(b"")  # mirrors real per-board state
        s = reader.snapshot(self.root, "x")
        self.assertIsNone(s["error"])
        self.assertEqual(s["consistency"], "immutable")
        self.assertEqual(len(s["tasks"]), 2)

    def test_pending_wal_is_not_read_immutably(self):
        db = make_board(self.root, "x", wal=True)
        Path(str(db) + "-wal").write_bytes(b"pending")
        s = reader.snapshot(self.root, "x")
        self.assertIsNotNone(s["error"])


if __name__ == "__main__":
    unittest.main()
```

2. Run `python3 -m unittest tests.test_hermes_kanban_reader -v`. Expected RED: a `KeyError: 'consistency'` failure in test 1, and test 2 fails with error `unable to open database file`.
   - If test 2 errors with something else, or opens live, the fixture does not reproduce the real state. Stop and compare `ls -la ~/.hermes/kanban/boards/vmas/` against the temp dir before changing anything.
3. Edit `herdr-plugins/hermes-kanban/reader.py`:
   - Add this function above `read_board`:

```python
def connect(path):
    uri = Path(path).resolve().as_uri()
    conn = None
    try:
        conn = sqlite3.connect(uri + "?mode=ro", uri=True, timeout=1)
        conn.execute("SELECT count(*) FROM sqlite_master").fetchone()
        return conn, "live"
    except sqlite3.OperationalError:
        if conn is not None:
            conn.close()
        wal = Path(str(path) + "-wal")
        if wal.exists() and wal.stat().st_size:
            raise
        # ponytail: empty WAL + no -shm means no pending writes; immutable skips locks.
        # Upgrade when Hermes exposes a JSON export that includes links.
        return sqlite3.connect(uri + "?mode=ro&immutable=1", uri=True, timeout=1), "immutable"
```

   - In `read_board`, replace the `conn = sqlite3.connect(...)` line with `conn, mode = connect(path)`, and change `return tasks, links` to `return tasks, links, mode`.
   - In `snapshot`, add `"consistency": ""` to the `result` dict, and change the read line to `result["tasks"], result["links"], result["consistency"] = read_board(path)`.
4. Run `python3 -m unittest tests.test_hermes_kanban_reader -v`. Expected: `Ran 3 tests ... OK`.
5. Real check: `python3 herdr-plugins/hermes-kanban/reader.py --board vmas | python3 -c "import json,sys;d=json.load(sys.stdin);print(d['error'],d['consistency'],len(d['tasks']))"`. Expected: `None immutable 7`, or a similar count. Do not write to any DB.
6. Commit (if approved): `tests/test_hermes_kanban_reader.py`, `herdr-plugins/hermes-kanban/reader.py`.

### T2: Cargo cleanup and ignore build output

1. In `herdr-plugins/hermes-kanban/Cargo.toml`, delete the line `crossterm = "0.29"`. Use `ratatui::crossterm` instead, which is the same crossterm the rataflow `From` impls target.
2. Append `herdr-plugins/hermes-kanban/target/` to `.gitignore`.
3. Run `cargo build --manifest-path herdr-plugins/hermes-kanban/Cargo.toml`. Expected: builds (stub `main`). `Cargo.lock` updates.

### T3: Pure model logic + tests (TDD, Rust)

1. Replace `herdr-plugins/hermes-kanban/src/main.rs` with the model part only, plus a `fn main() {}` placeholder for now:

```rust
use std::collections::HashSet;

use ratatui::style::{Color, Style};
use ratatui::text::Text;
use rataflow::{Edge, Flow, Node, StepEdge, Sugiyama, TextContent};
use serde::Deserialize;

#[derive(Deserialize, Clone, PartialEq, Default, Debug)]
struct Task {
    id: String,
    title: String,
    status: String,
    #[serde(default)] assignee: String,
    #[serde(default)] body: String,
    #[serde(default)] result: String,
    #[serde(default)] block_kind: String,
    #[serde(default)] last_failure_error: String,
    #[serde(default)] consecutive_failures: i64,
    #[serde(default)] comments: Vec<String>,
}

#[derive(Deserialize, Clone, PartialEq, Debug)]
struct BoardRef { slug: String, name: String }

#[derive(Deserialize, Clone, PartialEq, Debug)]
struct Snapshot {
    board: String,
    boards: Vec<BoardRef>,
    tasks: Vec<Task>,
    links: Vec<(String, String)>,
    error: Option<String>,
    #[serde(default)] consistency: String,
}

fn attention(t: &Task) -> bool {
    matches!(t.status.as_str(), "blocked" | "review")
        || !t.last_failure_error.is_empty()
        || t.consecutive_failures > 0
}

fn color(t: &Task) -> Color {
    match t.status.as_str() {
        "blocked" => Color::Red,
        "review" => Color::Yellow,
        _ if attention(t) => Color::Magenta,
        "running" => Color::Green,
        "done" => Color::DarkGray,
        _ => Color::Gray, // unknown statuses kept as-is
    }
}

fn trunc(s: &str, n: usize) -> String {
    if s.chars().count() <= n { s.to_string() } else { s.chars().take(n - 1).collect::<String>() + "…" }
}

fn graph_links(s: &Snapshot) -> Vec<(String, String)> {
    let ids: HashSet<&str> = s.tasks.iter().map(|t| t.id.as_str()).collect();
    s.links.iter().filter(|(p, c)| ids.contains(p.as_str()) && ids.contains(c.as_str())).cloned().collect()
}

fn initial_focus(s: &Snapshot, prev: Option<&str>) -> Option<String> {
    prev.filter(|p| s.tasks.iter().any(|t| t.id == *p)).map(str::to_string)
        .or_else(|| s.tasks.iter().find(|t| attention(t)).map(|t| t.id.clone()))
        .or_else(|| s.tasks.first().map(|t| t.id.clone()))
}

fn build_flow(s: &Snapshot) -> Result<Flow, rataflow::Error> {
    let nodes = s.tasks.iter().map(|t| {
        let who = if t.assignee.is_empty() { "unassigned" } else { &t.assignee };
        let lines = [trunc(&t.title, 32), format!("{} · {}", t.status, trunc(who, 16))];
        let w = lines.iter().map(|l| l.chars().count()).chain([t.id.len() + 2]).max().unwrap_or(0) + 2;
        let content = TextContent::new(Text::from(lines.join("\n")))
            .with_title(t.id.clone())
            .with_border_style(Style::default().fg(color(t)));
        Node::new(t.id.clone(), (0.0, 0.0), (w as f64, 4.0), content)
            .with_draggable(false).with_deletable(false).with_connectable(false)
    }).collect();
    let edges: Vec<Edge<StepEdge>> = graph_links(s).into_iter()
        .map(|(p, c)| Edge::new(format!("{p}->{c}"), p, c).with_deletable(false))
        .collect();
    let mut flow = Flow::with_graph(nodes, edges)?;
    flow.apply_layout(Sugiyama::vertical());
    Ok(flow)
}

fn main() {}

#[cfg(test)]
mod tests {
    use super::*;

    fn t(id: &str, status: &str) -> Task {
        Task { id: id.into(), title: id.into(), status: status.into(), ..Default::default() }
    }

    fn snap(tasks: Vec<Task>, links: &[(&str, &str)]) -> Snapshot {
        Snapshot {
            board: "x".into(), boards: vec![], tasks, error: None, consistency: "live".into(),
            links: links.iter().map(|(a, b)| (a.to_string(), b.to_string())).collect(),
        }
    }

    #[test]
    fn attention_rules() {
        assert!(attention(&t("a", "blocked")));
        assert!(attention(&t("a", "review")));
        assert!(!attention(&t("a", "done")));
        let mut f = t("a", "ready");
        f.last_failure_error = "boom".into();
        assert!(attention(&f));
    }

    #[test]
    fn dangling_links_dropped_and_isolated_nodes_layout() {
        let s = snap(vec![t("a", "ready"), t("b", "todo"), t("c", "weird")], &[("a", "b"), ("a", "gone")]);
        assert_eq!(graph_links(&s), vec![("a".to_string(), "b".to_string())]);
        assert!(build_flow(&s).is_ok());
    }

    #[test]
    fn focus_keeps_previous_else_attention_first() {
        let s = snap(vec![t("a", "ready"), t("b", "blocked")], &[]);
        assert_eq!(initial_focus(&s, Some("a")).as_deref(), Some("a"));
        assert_eq!(initial_focus(&s, Some("gone")).as_deref(), Some("b"));
        assert_eq!(initial_focus(&s, None).as_deref(), Some("b"));
    }

    #[test]
    fn parses_reader_json() {
        let j = r#"{"scope":"/r","board":"x","boards":[{"slug":"x","name":"X","path":"/p"}],
            "tasks":[{"id":"t1","title":"One","status":"blocked","assignee":"","body":"","result":"",
            "block_kind":"needs_input","last_failure_error":"","consecutive_failures":0,"priority":0,
            "started_at":0,"comments":["a: hi"]}],"links":[["t1","t2"]],"error":null,"consistency":"live"}"#;
        let s: Snapshot = serde_json::from_str(j).unwrap();
        assert_eq!(s.tasks[0].block_kind, "needs_input");
        assert_eq!(s.links[0].1, "t2");
    }
}
```

   - RED first: write the `#[cfg(test)]` module with the functions as `todo!()` bodies, then run `cargo test --manifest-path herdr-plugins/hermes-kanban/Cargo.toml`. Expected: 4 tests fail or panic with `not yet implemented`.
   - Then fill in the bodies as above and run again. Expected: `test result: ok. 4 passed`.
   - Dead-code warnings for unused fields are fine until T4.
2. Commit (if approved): `Cargo.toml`, `Cargo.lock`, `src/main.rs`, `.gitignore`.

### T4: App loop, rendering, keys

Replace `fn main() {}` in `src/main.rs` with the code below, and extend the `use` lines at the top.

```rust
use std::{env, fs, path::PathBuf, process::Command, sync::mpsc, thread, time::{Duration, Instant}};
use ratatui::crossterm::event::{self, Event, KeyCode, KeyEventKind};
use ratatui::layout::{Constraint, Layout, Rect};
use ratatui::style::Modifier;
use ratatui::widgets::{Block, Borders, Clear, List, ListItem, ListState, Paragraph, Wrap};
use ratatui::Frame;
use rataflow::default_controls_key_binding;

const REFRESH: Duration = Duration::from_secs(5);
type Fetch = Result<Snapshot, String>;

#[derive(Default)]
struct App {
    board: String,
    snap: Option<Snapshot>,
    boards: Vec<BoardRef>,
    flow: Option<Flow>,
    last_ok: Option<Instant>,
    err: Option<String>,
    details: bool,
    help: bool,
    picker: Option<ListState>,
    inflight: bool,
}

fn spawn_fetch(reader: &str, board: &str, tx: mpsc::Sender<Fetch>) {
    let (reader, board) = (reader.to_string(), board.to_string());
    thread::spawn(move || {
        let mut cmd = Command::new("python3");
        cmd.arg(&reader);
        if !board.is_empty() { cmd.args(["--board", &board]); }
        let res = cmd.output().map_err(|e| e.to_string()).and_then(|o| {
            if o.status.success() { serde_json::from_slice(&o.stdout).map_err(|e| e.to_string()) }
            else { Err(String::from_utf8_lossy(&o.stderr).trim().to_string()) }
        });
        let _ = tx.send(res);
    });
}

impl App {
    fn selected(&self) -> Option<&Task> {
        let id = self.flow.as_ref()?.first_selected_node_id()?;
        self.snap.as_ref()?.tasks.iter().find(|t| t.id == id)
    }

    fn apply(&mut self, res: Fetch) {
        self.inflight = false;
        let s = match res { Ok(s) => s, Err(e) => { self.err = Some(e); return; } };
        if !self.board.is_empty() && s.board != self.board { return; } // stale result from old board
        self.board = s.board.clone();
        self.boards = s.boards.clone();
        if let Some(e) = &s.error { self.err = Some(e.clone()); return; }
        self.err = None;
        self.last_ok = Some(Instant::now());
        if self.snap.as_ref() == Some(&s) { return; }
        let prev = self.flow.as_ref().and_then(|f| f.first_selected_node_id());
        match build_flow(&s) {
            Ok(mut f) => {
                if let Some(id) = initial_focus(&s, prev.as_deref()) { f.select_node(&id); }
                // ponytail: rebuild resets viewport; diff-patch nodes if this annoys.
                f.request_fit_view();
                self.flow = Some(f);
                self.snap = Some(s);
            }
            Err(e) => self.err = Some(format!("graph: {e}")),
        }
    }
}

fn draw(f: &mut Frame, app: &mut App) {
    let [main, status] = Layout::vertical([Constraint::Min(1), Constraint::Length(1)]).areas(f.area());
    let [graph, side] = if app.details {
        Layout::horizontal([Constraint::Percentage(65), Constraint::Percentage(35)]).areas(main)
    } else { [main, Rect::default()] };
    match app.flow.as_mut() {
        Some(flow) => f.render_widget(flow, graph),
        None => f.render_widget(Paragraph::new(if app.err.is_some() { "No data." } else { "Loading…" }), graph),
    }
    if app.details {
        let text = match app.selected() {
            Some(t) => {
                let mut l = vec![
                    format!("{}  {}", t.id, t.title), format!("status: {}", t.status),
                    format!("assignee: {}", t.assignee), format!("block: {}", t.block_kind),
                    format!("failure: {} (x{})", t.last_failure_error, t.consecutive_failures),
                    format!("result: {}", t.result), String::new(),
                ];
                l.extend(t.comments.iter().cloned());
                l.push(String::new());
                l.extend(t.body.lines().take(20).map(str::to_string));
                l.join("\n")
            }
            None => "No card selected.".into(),
        };
        f.render_widget(Paragraph::new(text).wrap(Wrap { trim: false })
            .block(Block::default().borders(Borders::ALL).title("Details")), side);
    }
    let (n, att) = app.snap.as_ref().map_or((0, 0), |s| (s.tasks.len(), s.tasks.iter().filter(|t| attention(t)).count()));
    let mode = app.snap.as_ref().map_or("", |s| s.consistency.as_str());
    let age = app.last_ok.map_or("never".into(), |t| format!("{}s ago", t.elapsed().as_secs()));
    let mut line = format!(" {} [{mode}] {n} cards, {att} need attention | ok {age} | ? help ", app.board);
    let mut style = Style::default();
    if let Some(e) = &app.err { line += &format!("| STALE: {e}"); style = style.fg(Color::Red); }
    f.render_widget(Paragraph::new(line).style(style), status);
    if app.help {
        let area = centered(f.area(), 50, 12);
        f.render_widget(Clear, area);
        f.render_widget(Paragraph::new(
            "arrows/Tab select   hjkl pan   +/- zoom   0 reset   f fit\nc center   Enter details   b boards   r refresh\nEsc close panel / exit   q exit")
            .block(Block::default().borders(Borders::ALL).title("Help")), area);
    }
    if let Some(state) = app.picker.as_mut() {
        let area = centered(f.area(), 40, app.boards.len() as u16 + 2);
        let items: Vec<ListItem> = app.boards.iter().map(|b| ListItem::new(format!("{} ({})", b.name, b.slug))).collect();
        f.render_widget(Clear, area);
        f.render_stateful_widget(List::new(items).highlight_style(Style::default().add_modifier(Modifier::REVERSED))
            .block(Block::default().borders(Borders::ALL).title("Boards")), area, state);
    }
}

fn centered(r: Rect, w: u16, h: u16) -> Rect {
    let (w, h) = (w.min(r.width), h.min(r.height));
    Rect::new(r.x + (r.width - w) / 2, r.y + (r.height - h) / 2, w, h)
}

fn main() -> std::io::Result<()> {
    let reader = env::var("HERMES_KANBAN_READER").unwrap_or_else(|_| "reader.py".into());
    let state = env::var_os("HERDR_PLUGIN_STATE_DIR").map(|d| PathBuf::from(d).join("board"));
    let mut app = App::default();
    app.board = state.as_ref().and_then(|p| fs::read_to_string(p).ok()).map(|s| s.trim().to_string()).unwrap_or_default();
    let (tx, rx) = mpsc::channel();
    let mut next = Instant::now();
    let mut term = ratatui::init();
    let res = (|| -> std::io::Result<()> {
        loop {
            if !app.inflight && Instant::now() >= next {
                app.inflight = true;
                next = Instant::now() + REFRESH;
                spawn_fetch(&reader, &app.board, tx.clone());
            }
            while let Ok(r) = rx.try_recv() { app.apply(r); }
            term.draw(|f| draw(f, &mut app))?;
            if !event::poll(Duration::from_millis(100))? { continue; }
            let Event::Key(key) = event::read()? else { continue };
            if key.kind != KeyEventKind::Press { continue; }
            if let Some(ls) = app.picker.as_mut() {
                let n = app.boards.len();
                match key.code {
                    KeyCode::Up => ls.select(Some(ls.selected().unwrap_or(0).saturating_sub(1))),
                    KeyCode::Down => ls.select(Some((ls.selected().unwrap_or(0) + 1).min(n.saturating_sub(1)))),
                    KeyCode::Enter => {
                        if let Some(b) = ls.selected().and_then(|i| app.boards.get(i)) {
                            app.board = b.slug.clone();
                            if let Some(p) = &state {
                                if let Some(d) = p.parent() { let _ = fs::create_dir_all(d); }
                                let _ = fs::write(p, &app.board);
                            }
                            app.flow = None; app.snap = None; app.last_ok = None; app.err = None;
                            next = Instant::now(); // in-flight old-board result is discarded by apply()
                        }
                        app.picker = None;
                    }
                    KeyCode::Esc | KeyCode::Char('b') => app.picker = None,
                    _ => {}
                }
                continue;
            }
            match key.code {
                KeyCode::Char('q') => break,
                KeyCode::Esc if app.help => app.help = false,
                KeyCode::Esc if app.details => app.details = false,
                KeyCode::Esc => break,
                KeyCode::Char('?') => app.help = !app.help,
                KeyCode::Enter => app.details = !app.details,
                KeyCode::Char('r') => next = Instant::now(),
                KeyCode::Char('b') if !app.boards.is_empty() => {
                    let i = app.boards.iter().position(|b| b.slug == app.board).unwrap_or(0);
                    app.picker = Some(ListState::default().with_selected(Some(i)));
                }
                // read-only: drop delete, multi-select, lock toggle
                KeyCode::Delete | KeyCode::Backspace | KeyCode::Char('m') | KeyCode::Char('i') => {}
                _ => if let Some(flow) = app.flow.as_mut() {
                    let rk: rataflow::KeyEvent = key.into();
                    match default_controls_key_binding(&rk) {
                        Some(a) => { flow.apply_controls_action(a); }
                        None => { flow.handle_key_event(rk); }
                    }
                },
            }
        }
        Ok(())
    })();
    ratatui::restore();
    res
}
```

Notes for the implementer:
- `Style`/`Color` are already imported from T3. Do not add a second import.
- If `ratatui::init` is not found, enable the feature in `Cargo.toml` (it is gated on `crossterm`, which is already on). Don't hand-roll terminal setup.
- If `key.into()` mismatches crossterm versions, `cargo tree -i crossterm` must show a single version. T2 removed the direct dependency for this reason.
- If `with_selected` on `ListState` is missing, use `let mut s = ListState::default(); s.select(Some(i));`.

Verify:
1. Run `cargo test --manifest-path herdr-plugins/hermes-kanban/Cargo.toml`. Expected: 4 passed.
2. Run `cargo build --release --manifest-path herdr-plugins/hermes-kanban/Cargo.toml`. Expected: no errors, no warnings about unused `Task` fields.
3. Manual run in a normal terminal:
   ```bash
   HERMES_KANBAN_READER=$PWD/herdr-plugins/hermes-kanban/reader.py \
     HERDR_PLUGIN_STATE_DIR=$TMPDIR/hk-state \
     herdr-plugins/hermes-kanban/target/release/hermes-kanban-tui
   ```
   Expected:
   - Default board graph appears, and a red-bordered `blocked` card is selected.
   - Status bar reads `default [live] 147 cards, N need attention | ok 0s ago`.
   - `b` shows 7 boards. Selecting `vmas` shows `[immutable] 7 cards`, and `cat $TMPDIR/hk-state/board` prints `vmas`.
   - Enter shows details. Esc closes details, then a second Esc exits and the terminal is restored.
   - Deleting `HERMES_KANBAN_READER` path (point it at `/nope.py`) shows `STALE: ...` in red without crashing.

Commit (if approved): `src/main.rs`, `Cargo.lock`.

### T5: Wire popup launcher

1. Replace `herdr-plugins/hermes-kanban/herdr/board.sh` with:

```bash
#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"
bin="$root/target/release/hermes-kanban-tui"
if [[ ! -x "$bin" ]]; then
  echo "Hermes Kanban TUI not built. Run:"
  echo "  cargo build --release --manifest-path $root/Cargo.toml"
  echo "Press Enter to close."
  if [[ -t 0 ]]; then read -r _ || true; fi
  exit 0
fi
export HERMES_KANBAN_READER="$root/reader.py"
exec "$bin"
```

2. In `herdr-plugin.toml`, set `description = "Read-only Hermes Kanban dependency graph in a Herdr popup."` and the action `title = "Hermes Kanban: open board"`.
3. Verify:
   - `bash -n herdr-plugins/hermes-kanban/herdr/board.sh herdr-plugins/hermes-kanban/herdr/open.sh` exits 0.
   - `mv target` is not needed. Run `HOME=$HOME bash herdr-plugins/hermes-kanban/herdr/board.sh </dev/null` with the binary present in a real tty: the TUI opens.
   - Manifest check: `python3 -c "import tomllib"` is not available on 3.9, so reuse the feat-005 evidence and only check by eye that `grep -n description herdr-plugins/hermes-kanban/herdr-plugin.toml` shows the new text.
4. Live Herdr check (gin runs, since it registers a local plugin; no Hermes profile change):
   ```bash
   herdr plugin link "$PWD/herdr-plugins/hermes-kanban"
   herdr plugin action invoke open --plugin gin.hermes-kanban
   ```
   Expected: popup shows the graph and Esc twice closes it.

### T6: Harness wiring + docs

1. In `init.sh`, add after the unittest line:

```bash
if command -v cargo >/dev/null; then
  echo "=== Tests: hermes-kanban TUI ==="
  cargo test --quiet --manifest-path herdr-plugins/hermes-kanban/Cargo.toml
fi
```

2. Run `./init.sh`. Expected: exit 0, `Ran 17 tests` (14 + 3) OK, cargo `4 passed`.
3. In `herdr-plugins/hermes-kanban/README.md`:
   - Replace the "placeholder" wording with build steps (`cargo build --release ...`), the key table from the help overlay, the attention rules, the `live`/`immutable` read modes, and the stale indicator.
   - Requirements become Herdr 0.9.5+, Bash, python3 (stdlib), Rust 1.88+ to build.
   - Move "Proposed TUI design" items that are now shipped into "Behavior". Keep deferred items (mutation, replay, follow-activity animation, mouse) listed as deferred.
4. Update the root `README.md` plugin line to match.
5. Update `feature_list.json` feat-006: `status: done`, with `evidence` holding the exact commands and results from T1–T6.
6. Add a dated feat-006 section to `progress.md`. Rewrite `session-handoff.md` "Latest Update" (live Herdr popup check result, or "pending gin").

## Validation summary

| Check | Command | Expected |
|---|---|---|
| Python reader | `python3 -m unittest tests.test_hermes_kanban_reader -v` | 3 OK |
| Rust model | `cargo test --manifest-path herdr-plugins/hermes-kanban/Cargo.toml` | 4 passed |
| Harness | `./init.sh` | exit 0 |
| Real boards | reader on `default` and `vmas` | `live 147`, `immutable 7` |
| Shell | `bash -n herdr-plugins/hermes-kanban/herdr/*.sh` | exit 0 |
| Diff hygiene | `git diff --check` | exit 0 |

## Risks / tradeoffs / open questions

- **SQLite schema coupling.** The reader depends on the `tasks`/`task_links`/`task_comments` columns. Missing optional columns degrade gracefully; missing core columns show an error. Upgrade to a Hermes JSON export that includes links if one is added.
- **Immutable fallback** only runs when the WAL is empty or missing. If a writer opens the DB mid-read, the snapshot may be slightly stale, and the next 5 s refresh corrects it. The read mode is shown in the status bar so it is never hidden.
- **Viewport reset on data change** (fit view on rebuild). Selection is preserved. Accept for now (`ponytail:` comment).
- **Large boards**: default board has 147 cards including `done`. A layout this size could get crowded. Open question for gin: hide `done` by default with a toggle? Not built (YAGNI until seen in the popup).
- **Deferred:** mouse input, follow-activity (`f` is used for fit view, matching rataflow defaults), replay, mutation, notifications.
- **Commits:** the repo has a dirty tree and a main/develop policy. Stage only the listed paths, and only with gin's approval.
