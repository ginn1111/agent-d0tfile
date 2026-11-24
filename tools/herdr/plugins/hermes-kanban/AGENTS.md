# Hermes Kanban plugin agent guide

Scope: this directory. Follow repository `AGENTS.md` and `RULES.md` first; they
own startup, feature tracking, and end-of-session rules. Read this plugin's
`README.md` for user behavior and commands before changing code.

## Change path

1. Pick one feature in root `feature_list.json`. Keep unrelated changes outside
   current diff.
2. Locate change: `reader.py` owns board discovery and SQLite snapshots;
   `src/main.rs` owns graph state, navigation, and rendering;
   `herdr-plugin.toml` and `herdr/*.sh` own popup launch and build.
3. Check current Hermes schema or Herdr contract before changing an integration.
   Use fixture databases under a temporary root. Preserve unknown task statuses,
   selected card/camera on refresh, and an explicit STALE error on failed reads.
4. Rebuild with `make hkb` after editing `reader.py` or Rust: Cargo embeds
   `reader.py` in the binary. Linking a plugin does not rebuild it.

## Boundaries

- Read Hermes through SQLite `mode=ro` with WAL visibility. `hermes kanban list`
  recomputes readiness, so keep it out of the viewer. Write only plugin-owned
  board selection under `HERDR_PLUGIN_STATE_DIR`.
- Keep dashboard inside Herdr's native terminal popup. A popup has no pane ID;
  exit the TUI to close it. Restore terminal state on every exit path.
- Keep attention tied to reported blocked, failure, or review state. Historical
  failures on done cards do not signal current attention.

## Verify before done

From repository root, run `./init.sh`, plus the Cargo, shell, and build checks in
`RULES.md` when their files change. For data or UI behavior changes, use an
isolated fixture and confirm `--snapshot` or `--render`; check live Herdr popup
only when user session is available. Record exact results in root
`feature_list.json`, `progress.md`, and `session-handoff.md`.
