# Session Handoff

## Current Objective

- Goal: feat-008 Cindy Theme Registry.
- Current status: feat-008 done. Next: commit d0t_file `i3/config`; then feat-004 token rotation.
- Branch / commit: `main` (see `git log -1`).

## Current State

- [x] Baseline repaired: obsolete `install-tool-theme` removed (dba46ee).
- [x] `themes/cindy/REGISTRY.md`: Rules, Variants, Roles, Targets (16), worked mappings per tool.
- [x] Palette +8 Colours (`fg_bright`, `shadow`, `card*`, `alert_*`).
- [x] Drift test reads the Targets table; skips missing paths; block scope for herdr live config.
- [x] `GLOSSARY.md` + ADR 0001.
- [x] d0t_file `i3/config`: focused title `#ffffff`→`bg`, comment `#14191D`→`bg` (uncommitted there).

## Verification Evidence

| Check | Command | Result | Notes |
|---|---|---|---|
| Tests + static | `./init.sh` | exit 0, 27 tests OK | |
| Drift test | `python3 -m unittest tests.test_theme_cindy_palette` | 4 OK | red on i3 strays before fix |
| i3 config | `i3 -C -c ~/tools/d0t_file/i3/config` | exit 0 | use running i3's `LD_LIBRARY_PATH` |
| Installer | `make theme-cindy-dry-run` | exit 0 | |

## Blockers / Risks

- Tokens for gindev/ginreview/gintary in pushed history (feat-004).
- Untracked paths left as-is by request (feat-005).
- `~/.config/dunst/dunstrc` not version-controlled (d0t_file `dunstrc` differs).
- picom `dunst-rail.glsl` hard-codes card colours as `vec3(0x..)`; drift test cannot see them.

## Next Session Startup

1. Read `AGENTS.md`.
2. Read `feature_list.json` and `progress.md`.
3. Run `./init.sh`.
