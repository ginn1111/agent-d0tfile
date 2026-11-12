---
status: completed
scope: plan Task 13: real install (gated on Gin approval of dry-run output)
owner: cindy
---

# THM-4 — Cindy Black & Ruby theme (feat-007)

## Goal

Ship the locked `004-hybrid` Black & Ruby look as static theme files in `themes/cindy/`, plus one stdlib Python installer with `make theme-cindy`, `theme-cindy-dry-run`, `theme-cindy-restore` and `theme-cindy-restore-dry-run`.

## Current context / assumptions

- Repo: `/home/aioz/personal/agent-d0tfile`, branch `main`. Design is committed as `11f7b50` in `docs/plans/2026-11-12-cindy-black-ruby-theme-design.md`. Read it first.
- Harness: `AGENTS.md` startup workflow. `./init.sh` runs `python3 -m unittest discover -s tests`, `bash -n scripts/*.sh`, `compileall scripts hermes-cron tests`, JSON checks and `make -n help`. `RULES.md` is missing (tracked as feat-006); ignore references to it.
- `feature_list.json` has feat-001..006. This work becomes **feat-007**.
- Existing tests use plain `unittest` with paths relative to the repo root (see `tests/test_validated_mistery_loop_plugin.py`).
- The real targets mostly live in **another repo**. `~/.config/{nvim,kitty,yazi,herdr}` are symlinked dirs into `~/tools/d0t_file/configs/...`, `~/.config/starship.toml` is a symlink to `~/tools/d0t_file/starship.toml`, and the Hermes skins in `~/.hermes/profiles/cindy/skins/` symlink into d0t_file. Installing therefore changes the d0t_file working tree; that is expected.
- `~/.config/lazygit` is a real dir and `config.yml` is empty. `~/.hermes/profiles/cindy/config.yaml` is mode 0600 and has exactly one `skin:` line (`  skin: solarized-osaka-cindy`, under `display:`).
- nvim is LazyVim. Every `lua/plugins/*.lua` file is a lazy spec. A file renamed to `*.lua.pre-cindy.*` stops loading.
- Bearded nvim port: `Ferouk/bearded-nvim` with lazy `name = "bearded"`. `require("bearded").setup({ flavor = "black-&-ruby" })`, `vim.cmd.colorscheme("bearded")`, and `require("bearded").palette("black-&-ruby")` returns `{ colors = {blue, green, purple, red, salmon, turquoize, yellow, ...}, ui = {default, defaultalt, primary, primaryalt, uibackground, ...} }`.

### Deviations from the committed design (fixed in Task 9)

| Design said | Plan does | Why |
|---|---|---|
| `scripts/install-theme-cindy.sh` | `scripts/install_theme_cindy.py` (stdlib only) | Swapping TOML blocks and doing idempotent edits is about 10 lines in Python and fragile in bash/awk. The script is still picked up by `compileall scripts`. |
| restore puts back the newest backup | restore puts back the **oldest** `.pre-cindy.*` backup, then deletes all of them | After repeated installs the newest backup is a cindy version; the oldest is the true pre-cindy original. |
| `herdr.toml`, `starship.toml` | `herdr-theme.toml`, `starship-palette.toml` | Both are block fragments, not whole configs. |
| 22 tokens | 24 tokens (`diff_add`, `diff_del` added), all hex lowercase | The Hermes skin needs diff backgrounds. A test requires every hex to come from the palette. |
| herdr gets `bg_agent` | herdr has no per-pane background token; it uses the standard `[theme.custom]` keys only | No such key exists. |

## Architecture

`themes/cindy/black-ruby.palette` is the single color source. A test fails if any file in `themes/cindy/` (sketches excluded) uses a hex value that is not in the palette. `scripts/install_theme_cindy.py` uses three operations:

- **link:** symlink a whole file, moving any existing file to `<file>.pre-cindy.<stamp>`.
- **retire:** move a file to a backup (`solarized.lua`).
- **edit:** apply a text function and keep a `copy2` backup. The function either swaps a `# >>> cindy theme` / `# <<< cindy theme` block, replacing a named TOML table on first run, or substitutes one line.

Dry-run prints `would …` and writes nothing. Restore reverses everything from the oldest backups.

## Card notes (from cindy)

- Run this from the main checkout after THM-1 and THM-2 are merged into `main`. The installer links to `REPO/themes/cindy`, so running it from a worktree would link to a temporary path.
- Before the real install, ask Gin whether d0t_file should `.gitignore` `*.pre-cindy.*`. That change belongs to the d0t_file repo.

## Step-by-step tasks

### Task 13 — Real install (gated: needs Gin's go-ahead)

This changes real config and the `~/tools/d0t_file` working tree.

1. Run `make theme-cindy-dry-run` and paste the full output to Gin. Wait for approval.
2. Run `make theme-cindy` and keep the output as evidence.
3. Check each tool:

| Tool | Command | Expected |
|---|---|---|
| kitty | `ctrl+shift+F5` (reload) | ruby cursor, `#111418` background |
| nvim | `nvim --headless "+Lazy! sync" +qa` then `nvim --headless "+lua io.write(require('bearded').palette('black-&-ruby').ui.primary)" +qa` | prints `#c62f52` |
| nvim visual | open nvim | bearded colors, ruby NORMAL pill, `#1a0f14` statusline |
| yazi | `yazi` | ruby tabs and mode, blue folders |
| lazygit | `lazygit` in any repo | ruby active border |
| herdr | restart herdr | ruby accent |
| starship | new shell | path blue, branch violet, green `❯` |
| Hermes | restart the cindy TUI | ruby banner, `#130e11` background |

4. Run `git -C ~/tools/d0t_file status --short`. Show Gin the changes. Do **not** commit in d0t_file; that is Gin's call.
5. Set feat-007 `status` to `done`, add the install evidence, and update `progress.md`. Commit: `chore(harness): close feat-007`.
6. Pushing needs Gin's approval. Never force-push.

## Tests / validation summary

- `tests/test_theme_cindy_palette.py`: no stray colors in the theme files.
- `tests/test_install_theme_cindy.py`: dry-run writes nothing; install creates links, backups and edits; editing `starship.toml` keeps it a symlink; the second run is a byte-identical no-op; restore returns the original bytes and links, and restore dry-run writes nothing.
- `./init.sh` is green, and `make theme-cindy-dry-run` / `theme-cindy-restore-dry-run` were run because those targets were touched.

## Risks, tradeoffs, open questions

1. **d0t_file side effects.** Links and backups land inside `~/tools/d0t_file/configs/...` because those `~/.config` dirs are symlinks, so git there will show typechanges and untracked `.pre-cindy.*` files. Should d0t_file `.gitignore` `*.pre-cindy.*`? That is Gin's call, in that repo.
2. **kitty include swap** comments out every active `include <x>.conf` except `black_ruby.conf`. Today only the theme include is active. A future non-theme include would also be commented out. Restore reverts it either way.
3. **Hermes `config.yaml`** has the first `skin:` line replaced. Today exactly one exists. The backup keeps 0600 via `copy2`, but it still holds whatever secrets `config.yaml` holds; it stays in the profile dir and is deleted on restore.
4. **bearded-nvim** downloads from GitHub on `Lazy sync`. It needs network access and the plugin is unpinned. Pin a commit if it ever breaks.
5. **Sketches** are deleted by default in Task 12. Confirm with Gin, or keep them under `themes/cindy/sketches` (the palette test already skips them).
6. **The starship prompt `❯` stays green**, not ruby as in the mock. Only the palette block is managed; changing `[character]` would mean editing outside the markers. Add it later if wanted.
7. **The yazi theme is a one-time snapshot** of the current Osaka layout. Later upstream yazi key changes won't flow in; regenerate with the Task 6 `sed` if needed.
