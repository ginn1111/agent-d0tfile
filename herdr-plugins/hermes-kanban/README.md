# Hermes Kanban for Herdr

Agent maintainers: follow [AGENTS.md](AGENTS.md) for plugin-specific boundaries.

Live, read-only Kanban graph and status lanes inside a native Herdr terminal popup. Built with
[Ratatui](https://ratatui.rs) and [Rataflow](https://github.com/furkankly/rataflow),
the terminal graph stack used by [Zoetrope](https://github.com/furkankly/zoetrope).
Compact graph cards show title, status, and assignee; Enter reveals priority and full details. Recorded parent/child links
become graph edges. Blockers, reported failures, and review requests stand out.

## Build and open

Requires Herdr 0.9.5+, Bash, Python 3.9+, and Rust 1.88+ to build. Cargo downloads
locked dependencies during the first build. Runtime needs only the built binary,
Python, and Bash; no browser or dashboard server is required.

From repository root:

```bash
make hkb-dry-run
make hkb
herdr plugin link "$PWD/herdr-plugins/hermes-kanban"
herdr plugin action invoke open --plugin gin.hermes-kanban
```

Popup uses 90% width and 85% height. `q` closes it; Escape closes an internal
panel first, then the popup. Build again after editing Rust or `reader.py`:
Python source is embedded into the binary. Linking does not run Cargo builds.
GitHub installs use the manifest's build command.

Alternative placements:

```bash
herdr plugin pane open --plugin gin.hermes-kanban --entrypoint board --placement split
herdr plugin pane open --plugin gin.hermes-kanban --entrypoint board --placement tab
```

Optional binding in Herdr config (choose an unused key):

```toml
[[keys.command]]
key = "prefix+shift+b"
type = "plugin_action"
command = "gin.hermes-kanban.open"
description = "Hermes Kanban"
```

Then run `herdr server reload-config`. Remove plugin registration with
`herdr plugin unlink gin.hermes-kanban`.

## Controls

| Key / gesture | Action |
| --- | --- |
| v | Switch task graph / Kanban lanes |
| F | Filters: arrows move, Space toggles, Enter/Esc closes |
| / | Search live; Enter keeps query, Esc restores previous query |
| d | Show/hide done cards (hidden by default) |
| x | Reset all filters, hiding done again |
| Tab / Shift-Tab, arrows | Select card; lanes use left/right for status, up/down for card |
| Enter / click card | Open details |
| j/k or PgUp/PgDn in details | Scroll description, reason, results, recent comments |
| h/j/k/l or drag empty canvas | Pan graph; hjkl navigates lanes |
| + / - or mouse wheel | Zoom |
| o / 0 | Fit graph |
| c | Center selected card |
| n | Next card needing attention, at readable zoom |
| f | Toggle following status changes; navigation pauses follow |
| b | Board picker; arrows/j/k and Enter select |
| r | Refresh now |
| ? | Help |
| Escape | Close internal panel, then popup |
| q / Ctrl-C | Exit |

First view fits the graph and selects a card needing attention when available.
Refresh runs every three seconds while open, preserving selection, positions,
and camera. New cards appear below existing cards. Unknown statuses stay visible.
Done cards are hidden by default; `d` includes them. Archived cards are excluded.
Only links whose endpoints remain visible are drawn.

Filters combine status, assignee (including unassigned), attention-only, and
case-insensitive search across ID/title/status/assignee/body. Multiple values
within status or assignee match any selected value; different filters must all
match. Empty selections mean any value. Selecting done status enables show-done;
other filters still apply. `x` resets everything.

Both layouts share selection and filters across refreshes and board switches.
Filters/layout reset when popup closes; only board selection is saved. Lanes
follow workflow status order, then unknown statuses; empty lanes are omitted.
Narrow popups show fewer columns and scroll to selected lane/card.
Use `--view lanes` to start in lanes; graph remains default.
Edges preserve Hermes parent/child direction; they do not imply temporal order.

Red means blocked or a reported failure; gold means review; cyan spinner means
Hermes reports running. A historical error on a completed card does not count as
current failure. This is a current-state viewer; timeline replay is not provided.

## Board source and selection

Reads local Hermes SQLite using `mode=ro`, `query_only`, and one read transaction
per snapshot, including committed WAL data. Does not import Hermes, run its CLI,
migrate databases, or update Hermes's current-board pointer. `hermes kanban list`
was unsuitable because it calls `recompute_ready`; the dashboard API also needs
authentication and individual task requests for links.

Root selection follows current macOS/Linux Hermes layout:

1. `--root PATH`, otherwise `HERMES_KANBAN_HOME`.
2. Shared root of `HERMES_HOME` (a `profiles/<name>` home resolves to its root).
3. `~/.hermes`.

Default board is `<root>/kanban.db`; named boards are
`<root>/kanban/boards/<slug>/kanban.db` with `board.json` identity metadata.
Archived board tombstones are excluded. `--db PATH` or `HERMES_KANBAN_DB` pins a
single database, shown as "Pinned database".

Last selected board is remembered per canonical source path in
`HERDR_PLUGIN_STATE_DIR/boards.json`. Outside Herdr, use
`${XDG_STATE_HOME:-~/.local/state}/herdr/hermes-kanban/boards.json`.
First launch uses `HERMES_KANBAN_BOARD` or Hermes's current-board pointer.
A missing remembered board stays visibly unavailable until you choose another.

To use a custom root for a Herdr popup, pass it to the pane process:

```bash
herdr plugin pane open --plugin gin.hermes-kanban --entrypoint board \
  --env HERMES_KANBAN_HOME=/absolute/path/to/hermes-root
```

Failures show STALE plus last successful refresh. Old data remains visible for
that board; switching boards clears old cards immediately. A fresh missing DB
shows an error and is never created. Selection-save errors stay visible.
Only the plugin's selection file is written. No background notifications.

The local schema adapter supports current Hermes task/link tables and optional
comments/block events. Unsupported schemas fail visibly; update `reader.py` if
Hermes changes these contracts. Remote hosts and alternate schemas need a future
supported export API; no silent fallback to a different source.

## Verify

```bash
./init.sh
cargo test --locked --manifest-path herdr-plugins/hermes-kanban/Cargo.toml
cargo clippy --locked --manifest-path herdr-plugins/hermes-kanban/Cargo.toml --all-targets -- -D warnings
bash -n herdr-plugins/hermes-kanban/herdr/open.sh herdr-plugins/hermes-kanban/herdr/board.sh
herdr-plugins/hermes-kanban/target/release/hermes-kanban-tui --snapshot
herdr-plugins/hermes-kanban/target/release/hermes-kanban-tui --render
herdr-plugins/hermes-kanban/target/release/hermes-kanban-tui --view lanes --render
```

`--snapshot` prints real JSON and returns nonzero on read failure. `--render`
prints a terminal frame for headless inspection. Neither saves selection.
Python fixture tests cover read-only snapshots, WAL updates, board identity,
missing/schema errors, and root resolution. Rust tests cover view preservation,
stale data, board isolation, rendering, unknown statuses, and selection storage.

Herdr's [popup contract](https://github.com/herdrdev/herdr/blob/v0.9.5/docs/next/website/src/content/docs/plugins.mdx)
uses manifest `placement = "popup"`; the CLI placement flag omits popup. Popup
has no pane ID, receives Escape itself, and closes when the program exits.
