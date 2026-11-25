# Cindy Theme Registry

The Theme Registry for Gin's VS Code Dark Modern look (picked from `sketches/006-vscode-faithful`, 2026-11-25). Read this before giving any tool (a Target) its colours. Terms: `GLOSSARY.md` (Theme section). Why reference-only: `docs/adr/0001-theme-registry-reference-not-generator.md`.

- **Palette**: `vscode-dark-modern.palette`, the only source of hex values (all taken from the sketch). A line `name=@other` is an alias: the same hex under a second Colour name, as VS Code reuses its greys. `warm-dusk.palette` is the previous look (honey focus, low blue light), now **inactive**: kept for a later switch (tag `theme-warm-dusk`); no Target may use it. `black-ruby.palette` is older and also inactive (tag `theme-black-ruby`). This file uses Colour names only.
- **Warm Dusk (inactive)**: Targets recoloured to VS Code lose their Warm Dusk values; `git checkout theme-warm-dusk -- themes/cindy` brings them back. `kitty.conf` is still Warm Dusk and is not a Target (kitty is skipped unless Gin names it, RULES.md).
- **Drift test**: `tests/test_theme_cindy_palette.py` reads the Targets table below and fails on any Stray Colour.

## Rules

1. Every solid colour in a Target is a Palette Colour. A new colour gets a name in `vscode-dark-modern.palette` first; give it a Role here if it has a job.
2. A Tint (Palette Colour + alpha, e.g. `accent` at `e6` for xborders) counts as its Colour. Fully transparent (alpha `00`) is free.
3. Comments count: an example hex in a comment is still a Stray Colour.
4. `accent` (VS Code blue) means focus only, and is a fill-only Colour: at 3.6:1 on `bg` it is too dim for text. Focus text (prompt, active label, cursor line number) uses `accent_text`. Errors, urgency and critical states use `err`.
5. Text on any filled colour (accent, err, ok, `mode_*`, …) is `fg_bright`. Exception: the `ginb` focus fill `turquoise` is light, so text on it is `bg`.
6. Pick colours by Role, then read the Colour from the Role table. Use the tool's own variables where it has them (polybar `[colors]`, rofi `*{}`, starship `[palettes]`, shell vars) named after the Colour.
7. Start each Target's colour section with a comment pointing to this file or the Palette.
8. List every new Target in the Targets table in the same change.
9. Shape: slight rounding. Desktop windows, panels and cards use a 6px radius (picom `corner-radius`, xborders `--border-radius`, polybar `radius`, dunst `corner_radius`, rofi `window`). Inner elements use 4px (rofi entries/buttons), progress bars 2px. Fullscreen, docks and the xborders overlay stay square. TUIs use their rounded box style: nvim `winborder = "rounded"`, lazygit `gui.border: rounded`. kitty is skipped unless Gin asks for it by name (RULES.md).

## Variants

A Variant re-points some Roles; a Colour's hex never changes.

| Variant | Worn by | Differs from `cindy` |
|---|---|---|
| `cindy` | desktop (i3, xborders, polybar, rofi, dunst, picom), terminal apps, Cindy's Hermes pane | (base) |
| `ginb` | Ginb's Hermes pane | focus → `turquoise`, agent pane → `bg_ginb`, bar → `bar_ginb`, selection/rule → `rule_ginb`; syntax uses colour (see Hermes skin) |

## Roles

| Role | `cindy` | `ginb` |
|---|---|---|
| base background | `bg` | `bg` |
| agent pane background | `bg_agent` | `bg_ginb` |
| chrome background (tab strip, unfocused frame, menu) | `bg_alt` | `bg_alt` |
| float background | `bg_mid` | `bg_mid` |
| status bar background | `bar` | `bar_ginb` |
| split line | `border` | `border` |
| raised surface (pill, inactive selection, normal card) | `surface` | `surface` |
| selection / active row | `rule` | `rule_ginb` |
| rule / divider / frame edge | `rule` | `rule_ginb` |
| text | `fg` | `fg` |
| headline text | `fg_bright` | `fg_bright` |
| secondary text | `sub` | `sub` |
| hint / comment | `dim` | `dim` |
| disabled / inactive / line number | `ghost` | `ghost` |
| focus fill (border, cursor, active tab/workspace) | `accent` | `turquoise` |
| focus text (prompt, active label, current line number) | `accent_text` | `turquoise` |
| text on filled colour | `fg_bright` | `bg` (on `turquoise`), else `fg_bright` |
| error / urgent / critical | `err` | `err` |
| warning | `warn` | `warn` |
| success / added | `ok` | `ok` |
| info / link / path / directory | `info` | `info` |
| attention | `yellow` | `yellow` |
| search match: background · outline | `match_bg` · `match_edge` | same |
| syntax: string · number · comment | `syn_string` · `syn_number` · `syn_comment` | same |
| syntax: keyword · function · type · variable | `purple` · `yellow` · `turquoise` · `green_alt` | same |
| mode (fill, text `fg_bright`): normal · insert · visual · replace · command · terminal | `accent` · `mode_insert` · `mode_visual` · `mode_replace` · `mode_command` · `mode_terminal` | same, normal → `turquoise` (text `bg`) |
| diff background added · removed | `diff_add` · `diff_del` | same |
| shadow | `shadow` (as Tint) | same |
| notification card: low · normal · critical | `card` · `surface` · `alert_card` | same |
| notification card: app-keyed · OSD | `card_raised` · `card_muted` | same |
| notification card edge: normal · critical | `card_edge` · `alert_edge` | same |

Spare hues with no other Role: `pink` (media, marked), `purple` (branches), `turquoise` (symlinks), `green_alt`. Aliases (same hex, different Role name): `bg_agent`, `bar`, `bg_ginb`, `bar_ginb` = `bg_alt`; `card` = `bg_mid`; `rule`, `rule_ginb` = `border`.

## Targets

`~` is the login user's home (not `$HOME` inside a Hermes profile session). Scope `block` = only the `# >>> cindy theme` … `# <<< cindy theme` block is checked. A missing path is skipped.

| Target | Path | Scope |
|---|---|---|
| Neovim colorscheme | `themes/cindy/nvim/colorscheme.lua` | file |
| Neovim lualine | `themes/cindy/nvim/lualine.lua` | file |
| herdr (source) | `themes/cindy/herdr-theme.toml` | file |
| herdr (live) | `~/tools/d0t_file/configs/herdr/config.toml` | block |
| Hermes skin cindy | `themes/cindy/hermes-skin.yaml` | file |
| Hermes skin ginb | `themes/cindy/hermes-skin-ginb.yaml` | file |
| yazi | `themes/cindy/yazi-theme.toml` | file |
| lazygit | `themes/cindy/lazygit.yml` | file |
| starship | `themes/cindy/starship-palette.toml` | file |
| starship (live) | `~/tools/d0t_file/starship.toml` | file |
| i3 + xborders | `~/tools/d0t_file/i3/config` | file |
| polybar | `~/tools/d0t_file/configs/polybar/config.ini` | file |
| polybar workspaces | `~/tools/d0t_file/configs/polybar/scripts/i3-workspaces.py` | file |
| rofi | `~/tools/d0t_file/configs/rofi/colors/vscode-dark-modern.rasi` | file |
| dunst | `~/.config/dunst/dunstrc` | file |
| picom | `~/tools/d0t_file/configs/picom/picom.conf` | file |
| neofetch | `~/tools/d0t_file/configs/neofetch/config.conf` | file |

Install/links for the in-repo files: `make theme-cindy` (see design doc `docs/plans/2026-11-12-cindy-black-ruby-theme-design.md`).

## Worked Targets

One mapping per existing Target: tool setting → Role (Colour). Copy the closest one when adding a new tool.

### i3 (`client.*`: border · background · text · indicator · child_border)

| Class | Colours |
|---|---|
| focused | `accent` · `accent` · `fg_bright` · `err` · `accent` |
| focused_inactive | `surface` · `surface` · `sub` · `surface` · `surface` |
| unfocused | `bg_alt` · `bg_alt` · `ghost` · `bg_alt` · `bg_alt` |
| urgent | `err` · `err` · `fg_bright` · `err` · `err` |
| placeholder | `bg_alt` · `bg` · `fg` · `bg_alt` · `bg` |
| `client.background` | `bg` |

### xborders (launched from i3 config)

`--border-rgba` = focus as Tint: `accent` + `e6` (~90%).

### polybar

`[colors]`: `background`=`bg`, `background-alt`=`bar`, `surface`, `rule`, `foreground`=`fg`, `sub`, `dim`, `ghost`, `primary`=`accent`, `ok`, `warn`, `info`, `alert`=`err`, `fg_bright` (text on `alert`), `disabled`=`ghost`. Bar border is fully transparent. Inline `%{F…}` icons: focus icons `accent`, offline `ghost`, IPs `dim`/`sub`.
Workspaces script: focused = `rule` background + `fg` text + `accent` underline; occupied `sub`; icons `dim`; urgent `err` background + `fg_bright` text.

### rofi (`colors/vscode-dark-modern.rasi`, imported by launcher + applets; `black-ruby.rasi` stays, inactive)

`background`=`bg`, `background-alt`=`surface`, `foreground`=`fg`, `selected`=`accent`, `active`=`sub`, `urgent`=`err`.

### dunst (+ picom `dunst-rail.glsl`)

| Urgency / rule | background · edge · text · highlight | header |
|---|---|---|
| global | – · – · – · `accent`; separator `rule` | `dim` header, `fg_bright` title |
| low | `card` · `card_edge` · `sub` · `ghost` | `ghost` |
| normal | `surface` · `card_edge` · `sub` · `accent` | `dim` |
| critical | `alert_card` · `alert_edge` · `fg` · `err` | `err` |
| slack (app-keyed) | `card_raised` | `dim` |
| OSD (volume/brightness) | `card_muted` | `dim` |

The picom rail shader picks the rail colour by matching the card background exactly (`alert_card`→`err`, `surface`→`accent`, `card_raised`→`info`, `card`/`card_muted`→`ghost`) and writes them as `vec3(0x..)`, which the drift test cannot see. Change card backgrounds in dunstrc and the shader together.

### picom

`shadow-color` = `shadow`.

### kitty

`background`=`bg`, `foreground`=`fg`, selection `rule`/`fg`, `url_color`=`info`, `cursor`=`accent`, cursor text `bg`. Tabs: active `accent` on `bg` text, inactive `ghost` on `bg_alt`, strip `bg_alt`. Window borders: active `accent`, inactive `surface`.
ANSI 0–7: `surface` `err` `ok` `yellow` `info` `purple` `turquoise` `sub`. 8–15: `ghost` `err` `ok` `warn` `green_alt` `pink` `turquoise` `fg`.

### Neovim

Colorscheme: `mini.base16` (`nvim/colorscheme.lua`): base00 `bg`, 01 `surface`, 02 `rule`, 03 `dim`, 04 `sub`, 05 `fg`, 06/07 `fg_bright`, 08 `err`, 09 `warn`, 0A `yellow`, 0B `ok`, 0C `turquoise`, 0D `info`, 0E `purple`, 0F `pink`. VS Code syntax overrides are set after base16 (`nvim_set_hl`): keyword/statement/conditional/repeat/exception `purple`, function `yellow`, type `turquoise`, variable/identifier `green_alt`, string `syn_string`, number/float `syn_number`, comment `syn_comment` (italic). lualine: section c on `bar`; b-section pill `surface`; mode pills (text `fg_bright`) normal `accent`, insert `mode_insert`, visual `mode_visual`, replace `mode_replace`, command `mode_command`, terminal `mode_terminal`; inactive `dim` on `bar`; diff `ok`/`yellow`/`err`; LSP name `turquoise`.

### herdr (`[theme.custom]`)

`panel_bg`=`bg`, `surface0`=`surface`, `surface1`=`rule`, `surface_dim`=`bg_alt`, `active_row_bg`=`bar`, `selection_bg`=`rule`, `overlay0`=`ghost`, `overlay1`=`dim`, `text`=`fg`, `subtext0`=`sub`, `mauve`=`purple`, `accent`=`accent`, `green`=`ok`, `yellow`=`yellow`, `red`=`err`, `blue`=`info`, `teal`=`turquoise`, `peach`=`warn`.

### Hermes skins

| Key group | `cindy` | `ginb` |
|---|---|---|
| `background` | `bg_agent` | `bg_ginb` |
| `ui_accent`, `prompt`, `banner_accent`, `banner_title`, `status_bar_strong`, `session_label`, `shell_dollar` (focus text) | `accent_text` | `turquoise` (`shell_dollar`: `ok`) |
| `response_border` (focus edge) | `accent` | `turquoise` |
| `ui_border`, `banner_border`, `input_rule`, `selection_bg`, `session_border`, `completion_menu_current_bg` | `rule` | `rule_ginb` |
| `status_bar_bg`, `voice_status_bg`, `completion_menu_bg` | `bar` | `bar_ginb` |
| `ui_label` | `sub` | `ok` |
| `status_bar_good` · `_warn` · `_bad` · `_critical` | `ok` · `yellow` · `warn` · `err` | same |
| syntax string · number · keyword · comment | `sub` · `fg` · `accent_text` · `dim` (muted) | `ok` · `purple` · `turquoise` · `dim` |
| `completion_menu_meta_bg` | `surface` | `surface` |
| banner logo | `err` first line, `accent_text` rest, `ghost` shadow | `yellow` first line, `turquoise` rest, `ghost` shadow |
| diff bg / word | `diff_add`/`diff_del`, `ok`/`err` | same |

### yazi

Fills (selected marker, active tab, mode normal, confirm yes, spot cell): `accent` with `fg_bright` text; fills in `ok`/`err` also take `fg_bright`, light fills (`pink`, `purple`, `turquoise`) take `bg`. Focus text (cwd, preview, titles, notify info, normal_alt): `accent_text`. Borders of input/confirm/cmp: `accent`. Status/tab strip `bar`; borders `surface`; selection `rule`. Directories `info`, executables `ok`, symlinks `turquoise`, hidden `dim`, archives `warn`, media `pink`, images `yellow`, broken `err` on `diff_del`. Notify warn/error: `yellow`/`err`.

### lazygit

Active border `accent`, inactive `ghost`, searching `yellow`, options `info`, selected line `rule`, inactive selected `surface`, cherry-picked `purple` on `surface`, marked base `info` on `yellow`, unstaged `err`, default text `fg`.

### starship

Fragment `[palettes.black_ruby]`: `base01`=`dim`, `base0`=`sub`, `yellow`, `orange`=`warn`, `red`=`err`, `magenta`=`pink`, `violet`=`purple`, `blue`=`info`, `cyan`=`turquoise`, `green`=`ok`.

Live `~/tools/d0t_file/starship.toml` (linked from `~/.config/starship.toml`) uses `[palettes.cindy]`, keys named after Colours. The palette carries `accent` plus `accent_text`. Prompt `❯` `accent_text` (fail `err`); directory `info`; branch `purple`; detached hash / hostname `dim`; git state `yellow`; dirty status `warn` (staged `ok`, conflicts `err`); line metrics `ok`/`err`; jobs `turquoise`; exit code `err`; duration `yellow`. Runtimes use spare hues only (never `accent`/`accent_text`/`err`).

### neofetch

Shell variables named after Colours (`ruby`=`accent_text` for title/section text, `disc`=`accent` for the logo fill, `fg`, `sub`, `dim`, `ghost`, `rule`, `info_c`=`info`, `turq`=`turquoise`, `purple`, `pink`, `yellow`, `ok`); frame lines `rule`.
