---
status: approved
scope: plan Tasks 0-7: feat-007 entry, palette test, theme files
owner: cindy
---

# THM-1 — Cindy Black & Ruby theme (feat-007)

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

- Work in the Kanban worktree. Its branch is `wt/<task-id>`. Skip `git switch -c` in Task 0.
- Run all commands from the worktree root. Treat `~/.config` and `~/.hermes` as **read-only**: read them as sources (lualine glyphs, yazi theme) and never write them.
- Do not stage unrelated untracked files (`skills/*`, `INTAKE.md`, `themes/tools.md`, `themes/cindy/sketches`, `.hermes/`, etc.).
- Do not edit `docs/plans/THM-*.md` except to change this file's frontmatter `status` to `completed` before review.
- Do not push.

## Step-by-step tasks

### Task 0 — Start feature (2 min)

```bash
cd /home/aioz/personal/agent-d0tfile
git status --short          # note unrelated dirt; do NOT stage it
./init.sh                   # expect: "=== Verification Complete ==="
git switch -c feat/cindy-black-ruby-theme
```

Add to the `features` array in `feature_list.json`:

```json
{
  "id": "feat-007",
  "name": "Cindy Black & Ruby theme",
  "description": "Static Black & Ruby (004-hybrid) theme files in themes/cindy/ + scripts/install_theme_cindy.py + make theme-cindy{,-dry-run,-restore,-restore-dry-run}. Design: docs/plans/2026-11-12-cindy-black-ruby-theme-design.md",
  "dependencies": [],
  "status": "in-progress",
  "evidence": ""
}
```

Verify: `python3 -m json.tool feature_list.json >/dev/null && echo ok` prints `ok`.

Commit: `git add feature_list.json && git commit -m "chore(harness): add feat-007 cindy black & ruby theme"`

### Task 1 — Palette test (RED) (3 min)

Create `tests/test_theme_cindy_palette.py`:

```python
import re
import unittest
from pathlib import Path

THEME = Path("themes/cindy")
HEX = re.compile(r"#[0-9a-fA-F]{6}\b")


class ThemeCindyPaletteTest(unittest.TestCase):
    def test_theme_files_use_only_palette_colors(self):
        palette = {h.lower() for h in HEX.findall((THEME / "black-ruby.palette").read_text())}
        files = [
            p for p in THEME.rglob("*")
            if p.is_file() and "sketches" not in p.parts and p.name != "black-ruby.palette"
        ]
        self.assertTrue(files, "no theme files found")
        for p in files:
            stray = {h.lower() for h in HEX.findall(p.read_text())} - palette
            self.assertFalse(stray, f"{p}: colors not in palette: {sorted(stray)}")


if __name__ == "__main__":
    unittest.main()
```

Run: `python3 -m unittest tests.test_theme_cindy_palette -v`. Expect **ERROR** `FileNotFoundError: ... black-ruby.palette`.

### Task 2 — Palette file (GREEN-ish) (2 min)

Create `themes/cindy/black-ruby.palette`:

```
# Cindy Black & Ruby palette. Source: BeardedBear src/variations/black.ts
# blackAndRuby + 004-hybrid tokens. Single source of truth: every hex in
# themes/cindy/ must appear here (tests/test_theme_cindy_palette.py).
bg=#111418
bg_alt=#0c0f11
bg_mid=#0f1215
bg_agent=#130e11
bar=#1a0f14
border=#040506
surface=#1c2027
rule=#3a1a26
fg=#bec6d0
sub=#a0acbb
dim=#6b7686
ghost=#475262
accent=#c62f52
err=#e35535
warn=#d4770c
ok=#00a884
info=#11b7d4
purple=#a85ff1
pink=#d46ec0
yellow=#c7910c
turquoise=#38c7bd
green_alt=#3585bb
diff_add=#0f2a24
diff_del=#2a0f12
```

Run the same test. Expect **FAIL** `no theme files found`. That is correct; the content tasks turn it green.

### Task 3 — kitty theme (2 min)

Create `themes/cindy/kitty.conf`:

```
# vim:ft=kitty
## name: Cindy Black & Ruby (BeardedBear Black & Ruby + 004-hybrid)
## palette: themes/cindy/black-ruby.palette

background #111418
foreground #bec6d0
selection_background #3a1a26
selection_foreground #bec6d0
url_color #11b7d4
cursor #c62f52
cursor_text_color #111418

# Tabs
active_tab_background #c62f52
active_tab_foreground #111418
inactive_tab_background #0c0f11
inactive_tab_foreground #475262
tab_bar_background #0c0f11

# Windows
active_border_color #c62f52
inactive_border_color #1c2027

# normal
color0 #1c2027
color1 #e35535
color2 #00a884
color3 #c7910c
color4 #11b7d4
color5 #a85ff1
color6 #38c7bd
color7 #a0acbb

# bright
color8 #475262
color9 #e35535
color10 #00a884
color11 #d4770c
color12 #3585bb
color13 #d46ec0
color14 #38c7bd
color15 #bec6d0
```

Verify: `python3 -m unittest tests.test_theme_cindy_palette` prints `OK`.

### Task 4 — Hermes skin (3 min)

Create `themes/cindy/hermes-skin.yaml`. It keeps the `branding`, `spinner`, `tool_prefix` and `banner_logo` structure of `hermes/skins/solarized-osaka-cindy.yaml`:

```yaml
# Bearded Black & Ruby skin for cindy (004-hybrid: ruby-tinted pane + bars).
# Palette: themes/cindy/black-ruby.palette
name: black-ruby-cindy
description: Bearded Black & Ruby secretary skin for Cindy

colors:
  background: "#130e11"
  ui_accent: "#c62f52"
  ui_label: "#a0acbb"
  banner_accent: "#c62f52"
  banner_title: "#c62f52"
  banner_text: "#bec6d0"
  banner_dim: "#6b7686"
  banner_border: "#3a1a26"
  ui_text: "#bec6d0"
  ui_border: "#3a1a26"
  ui_ok: "#00a884"
  ui_warn: "#d4770c"
  ui_error: "#e35535"
  prompt: "#c62f52"
  input_rule: "#3a1a26"
  response_border: "#c62f52"
  status_bar_bg: "#1a0f14"
  status_bar_text: "#a0acbb"
  status_bar_strong: "#c62f52"
  status_bar_dim: "#6b7686"
  status_bar_good: "#00a884"
  status_bar_warn: "#c7910c"
  status_bar_bad: "#d4770c"
  status_bar_critical: "#e35535"
  session_label: "#c62f52"
  session_border: "#3a1a26"
  shell_dollar: "#c62f52"
  voice_status_bg: "#1a0f14"
  selection_bg: "#3a1a26"
  completion_menu_bg: "#1a0f14"
  completion_menu_current_bg: "#3a1a26"
  completion_menu_meta_bg: "#1c2027"
  completion_menu_meta_current_bg: "#3a1a26"
  diff_added: "#0f2a24"
  diff_removed: "#2a0f12"
  diff_added_word: "#00a884"
  diff_removed_word: "#e35535"
  syntax_string: "#00a884"
  syntax_number: "#a85ff1"
  syntax_keyword: "#c7910c"
  syntax_comment: "#6b7686"

branding:
  agent_name: Cindy
  response_label: " ◇ Cindy "
  prompt_symbol: "◇"
  help_header: "◇ Cindy Command Palette"
  welcome: "Cindy secretary ready. Type /help for commands."
  goodbye: "Cindy offline."

spinner:
  waiting_faces: ["◇", "◈", "◆"]
  thinking_faces: ["◇", "◈", "◆"]
  thinking_verbs:
    - organizing
    - triaging
    - drafting
    - scheduling

tool_prefix: "│"

banner_logo: |
  [bold #e35535] ██████╗██╗███╗   ██╗██████╗ ██╗   ██╗[/]
  [bold #c62f52]██╔════╝██║████╗  ██║██╔══██╗╚██╗ ██╔╝[/]
  [bold #c62f52]██║     ██║██╔██╗ ██║██║  ██║ ╚████╔╝ [/]
  [bold #c62f52]██║     ██║██║╚██╗██║██║  ██║  ╚██╔╝  [/]
  [bold #c62f52]╚██████╗██║██║ ╚████║██████╔╝   ██║   [/]
  [#475262] ╚═════╝╚═╝╚═╝  ╚═══╝╚═════╝    ╚═╝   [/]
```

Verify the color keys match the existing skin exactly (system python has PyYAML):

```bash
/usr/bin/python3 -c "import yaml; a=yaml.safe_load(open('themes/cindy/hermes-skin.yaml')); b=yaml.safe_load(open('hermes/skins/solarized-osaka-cindy.yaml')); assert set(a['colors'])==set(b['colors']), set(a['colors'])^set(b['colors']); print('keys match')"
python3 -m unittest tests.test_theme_cindy_palette
```

Expected output: `keys match`, then `OK`.

### Task 5 — nvim specs (3 min)

Create `themes/cindy/nvim/bearded.lua`:

```lua
-- Cindy theme: Bearded Black & Ruby (themes/cindy, installed by `make theme-cindy`).
return {
  "Ferouk/bearded-nvim",
  name = "bearded",
  lazy = false,
  priority = 1000,
  config = function()
    require("bearded").setup({ flavor = "black-&-ruby" })
    vim.cmd.colorscheme("bearded")
  end,
}
```

Create `themes/cindy/nvim/lualine.lua`. It is the current `~/.config/nvim/lua/plugins/lualine.lua` with only the palette source and color names changed:

```lua
-- Cindy theme: lualine pills on Bearded Black & Ruby (themes/cindy, `make theme-cindy`).
return {
  "nvim-lualine/lualine.nvim",
  dependencies = { "nvim-tree/nvim-web-devicons", "Ferouk/bearded-nvim" },
  config = function()
    local p = require("bearded").palette("black-&-ruby")
    local c = {
      bar = "#1a0f14", -- palette `bar`: 004-hybrid ruby tint, not in bearded
      dark = p.ui.uibackground,
      fg = p.ui.default,
      dim = p.ui.defaultalt,
      accent = p.ui.primary,
      green = p.colors.green,
      purple = p.colors.purple,
      red = p.colors.red,
      yellow = p.colors.yellow,
      cyan = p.colors.turquoize,
    }
    local pill = p.ui.primaryalt
    local cap = { left = "", right = "" } -- rounded pill ends

    local function mode_theme(color)
      return {
        a = { fg = c.dark, bg = color, gui = "bold" },
        b = { fg = c.fg, bg = pill },
        c = { fg = c.fg, bg = c.bar },
      }
    end

    local theme = {
      normal = mode_theme(c.accent),
      insert = mode_theme(c.green),
      visual = mode_theme(c.purple),
      replace = mode_theme(c.red),
      command = mode_theme(c.yellow),
      terminal = mode_theme(c.cyan),
      inactive = {
        a = { fg = c.dim, bg = c.bar },
        b = { fg = c.dim, bg = c.bar },
        c = { fg = c.dim, bg = c.bar },
      },
    }

    local function lsp_name()
      local ft = vim.bo.filetype
      for _, client in ipairs(vim.lsp.get_clients({ bufnr = 0 })) do
        if client.config.filetypes and vim.tbl_contains(client.config.filetypes, ft) then
          return client.name
        end
      end
      return "No LSP"
    end

    require("lualine").setup({
      options = {
        theme = theme,
        component_separators = "",
        section_separators = cap,
        globalstatus = true,
      },
      sections = {
        lualine_a = { { "mode", separator = cap, padding = { left = 1, right = 1 } } },
        lualine_b = {
          { "filename", separator = cap },
          { "branch", icon = "", separator = cap },
        },
        lualine_c = {
          {
            "diff",
            symbols = { added = " ", modified = "󰝤 ", removed = " " },
            diff_color = {
              added = { fg = c.green },
              modified = { fg = c.yellow },
              removed = { fg = c.red },
            },
          },
          "%=",
          {
            "diagnostics",
            sources = { "nvim_diagnostic" },
            symbols = { error = " ", warn = " ", info = " " },
          },
        },
        lualine_x = {
          { lsp_name, icon = " ", color = { fg = c.cyan, gui = "bold" } },
          { "filetype", icon_only = true },
        },
        lualine_y = { { "progress", separator = cap } },
        lualine_z = { { "location", separator = cap } },
      },
      inactive_sections = {
        lualine_c = { "filename" },
        lualine_x = { "location" },
      },
    })
  end,
}
```

Copy the Nerd Font icon glyphs byte-for-byte from the current `~/.config/nvim/lua/plugins/lualine.lua`. This plan may not render them; check with `diff <(sed -n '/symbols/p;/icon/p' ~/.config/nvim/lua/plugins/lualine.lua) <(sed -n '/symbols/p;/icon/p' themes/cindy/nvim/lualine.lua)`, which should print nothing.

Verify Lua syntax (both files only return tables, so nothing runs):

```bash
for f in themes/cindy/nvim/*.lua; do nvim --clean --headless -l "$f" && echo "ok $f"; done
python3 -m unittest tests.test_theme_cindy_palette
```

Expected output: two `ok` lines, then `OK`.

### Task 6 — yazi theme, generated once by hex mapping (3 min)

```bash
sed -e 's/#001419/#111418/g' -e 's/#002c38/#1a0f14/g' -e 's/#063540/#1c2027/g' \
    -e 's/#1a6397/#3a1a26/g' -e 's/#268bd3/#c62f52/g' -e 's/#29a298/#38c7bd/g' \
    -e 's/#380605/#2a0f12/g' -e 's/#46acf5/#c62f52/g' -e 's/#576d74/#6b7686/g' \
    -e 's/#6d71c4/#a85ff1/g' -e 's/#849900/#00a884/g' -e 's/#9eabac/#bec6d0/g' \
    -e 's/#adb7b7/#bec6d0/g' -e 's/#b28500/#c7910c/g' -e 's/#c94c16/#d4770c/g' \
    -e 's/#d23681/#d46ec0/g' -e 's/#db302d/#e35535/g' -e 's/#fdf5e2/#bec6d0/g' \
    -e '/^\[icon\]/,$ s/#c62f52/#11b7d4/g' \
    -e 's|^# Solarized Osaka palette.*|# Cindy Black \& Ruby palette (themes/cindy/black-ruby.palette).|' \
    -e 's|^# from craftzdog.*|# Generated once from the Solarized Osaka yazi theme by hex mapping.|' \
    ~/.config/yazi/theme.toml > themes/cindy/yazi-theme.toml
```

The ruby accent replaces Osaka blue in the UI. In `[icon]` and `[filetype]` (the last two sections) directories go back to info blue `#11b7d4`, so folders don't look like UI accents.

Verify:

```bash
python3 -c "import tomllib; tomllib.load(open('themes/cindy/yazi-theme.toml','rb')); print('toml ok')"
grep -c '#c62f52' themes/cindy/yazi-theme.toml      # > 0
sed -n '/^\[filetype\]/,$p' themes/cindy/yazi-theme.toml | grep -c '#c62f52'   # 0
python3 -m unittest tests.test_theme_cindy_palette  # OK
```

### Task 7 — lazygit, herdr and starship fragments (3 min)

Create `themes/cindy/lazygit.yml`:

```yaml
# Cindy Black & Ruby (themes/cindy/black-ruby.palette); installed by `make theme-cindy`.
gui:
  theme:
    activeBorderColor: ["#c62f52", bold]
    inactiveBorderColor: ["#475262"]
    searchingActiveBorderColor: ["#c7910c", bold]
    optionsTextColor: ["#11b7d4"]
    selectedLineBgColor: ["#3a1a26"]
    inactiveViewSelectedLineBgColor: ["#1c2027"]
    cherryPickedCommitFgColor: ["#a85ff1"]
    cherryPickedCommitBgColor: ["#1c2027"]
    markedBaseCommitFgColor: ["#11b7d4"]
    markedBaseCommitBgColor: ["#c7910c"]
    unstagedChangesColor: ["#e35535"]
    defaultFgColor: ["#bec6d0"]
```

Create `themes/cindy/herdr-theme.toml`. This is the block content; the installer wraps it in markers:

```toml
# Cindy Black & Ruby (themes/cindy/black-ruby.palette); managed by `make theme-cindy`.
[theme.custom]
panel_bg = "#111418"
surface0 = "#1c2027"
surface1 = "#3a1a26"
surface_dim = "#0c0f11"
overlay0 = "#475262"
overlay1 = "#6b7686"
text = "#bec6d0"
subtext0 = "#a0acbb"
mauve = "#a85ff1"
accent = "#c62f52"
green = "#00a884"
yellow = "#c7910c"
red = "#e35535"
blue = "#11b7d4"
teal = "#38c7bd"
peach = "#d4770c"
```

Create `themes/cindy/starship-palette.toml`. Its key names match the ones the existing starship styles reference (`base01`, `violet`, `green`, ...):

```toml
# Cindy Black & Ruby (themes/cindy/black-ruby.palette); managed by `make theme-cindy`.
[palettes.black_ruby]
base01 = "#6b7686"
base0 = "#a0acbb"
yellow = "#c7910c"
orange = "#d4770c"
red = "#e35535"
magenta = "#d46ec0"
violet = "#a85ff1"
blue = "#11b7d4"
cyan = "#38c7bd"
green = "#00a884"
```

Verify:

```bash
/usr/bin/python3 -c "import yaml; yaml.safe_load(open('themes/cindy/lazygit.yml')); print('yaml ok')"
python3 -c "import tomllib; [tomllib.load(open(f,'rb')) for f in ('themes/cindy/herdr-theme.toml','themes/cindy/starship-palette.toml')]; print('toml ok')"
python3 -m unittest tests.test_theme_cindy_palette   # OK
```

Commit (theme files only, no sketches):

```bash
git add tests/test_theme_cindy_palette.py themes/cindy/black-ruby.palette themes/cindy/kitty.conf \
  themes/cindy/hermes-skin.yaml themes/cindy/nvim themes/cindy/yazi-theme.toml \
  themes/cindy/lazygit.yml themes/cindy/herdr-theme.toml themes/cindy/starship-palette.toml
git commit -m "feat(themes): add cindy black & ruby theme files + palette test"
```

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
