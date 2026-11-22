# Session Progress Log

## Current State

**Last Updated:** 2026-11-22
**Active Feature:** none (feat-009 done; Gin's visual OK 2026-11-22)

## Status

### What's Done
- [x] feat-001 Agent harness.
- [x] feat-002 Validated-mistery-loop plugin.
- [x] feat-003 Reconcile working tree: tracked cleanup committed.
- [x] feat-007 Cindy Black & Ruby theme: files, installer, make targets, real install, herdr focus colors.
- [x] Shape: slight rounding (Gin, 2026-11-22). picom/xborders/polybar/dunst 6px, rofi launcher 6/4px, nvim `winborder=rounded`, lazygit `border: rounded`; rule 9 in REGISTRY. kitty skipped (RULES.md). herdr/yazi have no rounded option.
- [x] feat-009 Warm Dusk rollout: `warm-dusk.palette` active (Black & Ruby kept inactive in `black-ruby.palette` + tag `theme-black-ruby`); all 18 Targets rewritten; nvim bearded -> `mini.base16` (`nvim/colorscheme.lua`); comfort contrast test; installer keeps `[palettes.cindy]` starship + retires dangling links. Plan: `.hermes/plans/2026-11-22_111452-warm-dusk-rollout.md`.
- [x] feat-008 Cindy Theme Registry: `themes/cindy/REGISTRY.md` (Roles, Variants, Targets, worked mappings), palette +8 Colours, drift test over all listed Targets, `GLOSSARY.md`, ADR 0001; i3 Stray Colours fixed in d0t_file.

### What's In Progress
- [ ] none

### What's Next
0. feat-011 (switch back to Black & Ruby on demand) and feat-010 (rename `black-ruby` identifiers).
1. feat-004 Rotate leaked Hermes API tokens (was in `hermes/.make/hermes-profiles.mk`, pushed).
2. feat-005 Triage untracked files.
3. feat-006 Restore or drop `RULES.md` reference in `AGENTS.md`.

## Blockers / Risks
- [ ] Tokens in git history on origin/main; untracking does not remove them. Rotate.
- [ ] `~/.config/dunst/dunstrc` is a real file, not the d0t_file `dunstrc` (different content): not version-controlled.

## Decisions Made
- **Removed orphaned Make targets**: `hermes-profiles-config` + `hermes-health*` (needed deleted `hermes_profile_map.py`), `lmp*` + `scripts/link-model-providers.sh` (needed deleted `hermes-plugins/model-providers`).
- **`hermes/Makefile` uses `-include .env`**: `make help` no longer fails without `.env`.
- **`init.sh` drops `-t .`**: `tests/` has no `__init__.py`; discovery failed with "Start directory is not importable".
- **`.make/` gitignored**: generated cache holds tokens.
- **Installer ignores `HERMES_HOME`**: profile sessions set it to a profile dir; target fixed at `~/.hermes/profiles/cindy`.
- **ginb skin**: `black-ruby-ginb` = cindy base, turquoise `#38c7bd` accent, teal-tinted pane `#0e1314`/bars `#0f1a1a`, ▸ branding, ruby G on banner.
- **herdr focus**: `active_row_bg=#1a0f14`, `selection_bg=#3a1a26`; `accent` keeps pane border ruby.
- **Theme Registry is reference-only + drift test** (ADR 0001). Variants re-point Roles, never hex. Text on filled colour = `bg`. Tints/full transparency allowed; comments count. Drift test resolves `~` via login home (pwd), not `$HOME` (profile sessions override it).
- **Warm Dusk replaces Black & Ruby** (Gin, 2026-11-22): rollout by name-keyed hex rewrite (throwaway script, not committed: ADR 0001). `black-ruby.palette` stays for a later switch; drift test ignores `*.palette` files as Targets.
- **i3 reload does not restart xborders/picom with new env**: restart them via `i3-msg 'exec …'` so they inherit i3's `LD_LIBRARY_PATH` (picom needs `libev.so.4` from `~/.local/lib`).
- **Dropped `install-tool-theme.sh`** + test + README section: `agent-tool-themes/` gone, `itt` target already removed; was failing baseline.

## Files Modified This Session
- feat-008: `themes/cindy/REGISTRY.md` (new), `themes/cindy/black-ruby.palette`, `tests/test_theme_cindy_palette.py`, `GLOSSARY.md` (new), `docs/adr/0001-theme-registry-reference-not-generator.md` (new), `README.md`, `RULES.md`, `feature_list.json`
- d0t_file: `i3/config`
- Baseline fix (dba46ee): removed `scripts/install-tool-theme.sh`, `tests/test_install_tool_theme.py`; `Makefile`, `README.md`

## Evidence of Completion
- [x] `./init.sh` exit 0, 27 tests OK
- [x] `python3 -m unittest tests.test_theme_cindy_palette` OK (4 tests); red on i3 `#14191d`/`#ffffff` before fix
- [x] `i3 -C -c ~/tools/d0t_file/i3/config` exit 0 (needs running i3's `LD_LIBRARY_PATH`)
- [x] `make theme-cindy-dry-run` exit 0

## Notes for Next Session
Run `./init.sh` first. Under a profile session, set `HERMES_HOME=~/.hermes` for link dry-runs. Theming a new tool: read `themes/cindy/REGISTRY.md`.
