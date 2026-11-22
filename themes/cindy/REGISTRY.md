# Cindy Theme Registry

The Theme Registry for Gin's Warm Dusk look (low blue light, honey focus; picked from `sketches/005-warm-dusk`, 2026-11-22). Read this before giving any tool (a Target) its colours. Terms: `GLOSSARY.md` (Theme section). Why reference-only: `docs/adr/0001-theme-registry-reference-not-generator.md`.

- **Palette**: `warm-dusk.palette`, the only source of hex values. `black-ruby.palette` is the previous look, kept inactive for a later switch (feat-011; tag `theme-black-ruby`); no Target may use it. This file uses Colour names only.
- **Drift test**: `tests/test_theme_cindy_palette.py` reads the Targets table below and fails on any Stray Colour.

## Rules

1. Every solid colour in a Target is a Palette Colour. A new colour gets a name in `warm-dusk.palette` first; give it a Role here if it has a job.
2. A Tint (Palette Colour + alpha, e.g. `accent` at `e6` for xborders) counts as its Colour. Fully transparent (alpha `00`) is free.
3. Comments count: an example hex in a comment is still a Stray Colour.
4. `accent` (honey) means focus only. Errors, urgency and critical states use `err`.
5. Text on any filled colour (accent, err, ok, …) is `bg`.
6. Pick colours by Role, then read the Colour from the Role table. Use the tool's own variables where it has them (polybar `[colors]`, rofi `*{}`, starship `[palettes]`, shell vars) named after the Colour.
7. Start each Target's colour section with a comment pointing to this file or the Palette.
8. List every new Target in the Targets table in the same change.

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
| focus (border, cursor, prompt, active tab/workspace) | `accent` | `turquoise` |
| text on filled colour | `bg` | `bg` |
| error / urgent / critical | `err` | `err` |
| warning | `warn` | `warn` |
| success / added | `ok` | `ok` |
| info / link / path / directory | `info` | `info` |
| attention / search match | `yellow` | `yellow` |
| mode: normal · insert · visual · replace · command · terminal | `accent` · `ok` · `purple` · `err` · `yellow` · `turquoise` | same, normal → `turquoise` |
| diff background added · removed | `diff_add` · `diff_del` | same |
| shadow | `shadow` (as Tint) | same |
| notification card: low · normal · critical | `card` · `surface` · `alert_card` | same |
| notification card: app-keyed · OSD | `card_raised` · `card_muted` | same |
| notification card edge: normal · critical | `card_edge` · `alert_edge` | same |

Spare hues with no Role yet: `pink` (media, marked), `purple` (numbers, branches), `turquoise` (types, symlinks), `green_alt`.

## Targets

`~` is the login user's home (not `$HOME` inside a Hermes profile session). Scope `block` = only the `# >>> cindy theme` … `# <<< cindy theme` block is checked. A missing path is skipped.

| Target | Path | Scope |
|---|---|---|
| kitty | `themes/cindy/kitty.conf` | file |
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
| rofi | `~/tools/d0t_file/configs/rofi/colors/black-ruby.rasi` | file |
| dunst | `~/.config/dunst/dunstrc` | file |
| picom | `~/tools/d0t_file/configs/picom/picom.conf` | file |
| neofetch | `~/tools/d0t_file/configs/neofetch/config.conf` | file |

Install/links for the in-repo files: `make theme-cindy` (see design doc `docs/plans/2026-11-12-cindy-black-ruby-theme-design.md`).

## Worked Targets

One mapping per existing Target: tool setting → Role (Colour). Copy the closest one when adding a new tool.

### i3 (`client.*`: border · background · text · indicator · child_border)

| Class | Colours |
|---|---|
| focused | `accent` · `accent` · `bg` · `err` · `accent` |
| focused_inactive | `surface` · `surface` · `sub` · `surface` · `surface` |
| unfocused | `bg_alt` · `bg_alt` · `ghost` · `bg_alt` · `bg_alt` |
| urgent | `err` · `err` · `bg` · `err` · `err` |
| placeholder | `bg_alt` · `bg` · `fg` · `bg_alt` · `bg` |
| `client.background` | `bg` |

### xborders (launched from i3 config)

`--border-rgba` = focus as Tint: `accent` + `e6` (~90%).

### polybar

`[colors]`: `background`=`bg`, `background-alt`=`bar`, `surface`, `rule`, `foreground`=`fg`, `sub`, `dim`, `ghost`, `primary`=`accent`, `ok`, `warn`, `info`, `alert`=`err`, `disabled`=`ghost`. Bar border is fully transparent. Inline `%{F…}` icons: focus icons `accent`, offline `ghost`, IPs `dim`/`sub`.
Workspaces script: focused = `rule` background + `fg` text + `accent` underline; occupied `sub`; icons `dim`; urgent `err` background + `bg` text.

### rofi (`colors/black-ruby.rasi`, imported by launcher + applets)

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

Colorscheme: `mini.base16` (`nvim/colorscheme.lua`): base00 `bg`, 01 `surface`, 02 `rule`, 03 `dim`, 04 `sub`, 05 `fg`, 06/07 `fg_bright`, 08 `err`, 09 `warn`, 0A `yellow`, 0B `ok`, 0C `turquoise`, 0D `info`, 0E `purple`, 0F `pink`. lualine: section c on `bar`; b-section pill `surface`; mode pills normal `accent`, insert `ok`, visual `purple`, replace `err`, command `yellow`, terminal `turquoise`, pill text `bg`; inactive `dim` on `bar`; diff ok/yellow/err; LSP name `turquoise`.

### herdr (`[theme.custom]`)

`panel_bg`=`bg`, `surface0`=`surface`, `surface1`=`rule`, `surface_dim`=`bg_alt`, `active_row_bg`=`bar`, `selection_bg`=`rule`, `overlay0`=`ghost`, `overlay1`=`dim`, `text`=`fg`, `subtext0`=`sub`, `mauve`=`purple`, `accent`=`accent`, `green`=`ok`, `yellow`=`yellow`, `red`=`err`, `blue`=`info`, `teal`=`turquoise`, `peach`=`warn`.

### Hermes skins

| Key group | `cindy` | `ginb` |
|---|---|---|
| `background` | `bg_agent` | `bg_ginb` |
| `ui_accent`, `prompt`, `response_border`, `banner_title`, `status_bar_strong`, `session_label` | `accent` | `turquoise` |
| `ui_border`, `banner_border`, `input_rule`, `selection_bg`, `session_border`, `completion_menu_current_bg` | `rule` | `rule_ginb` |
| `status_bar_bg`, `voice_status_bg`, `completion_menu_bg` | `bar` | `bar_ginb` |
| `ui_label`, `shell_dollar` | `sub`, `accent` | `ok`, `ok` |
| `status_bar_good` · `_warn` · `_bad` · `_critical` | `ok` · `yellow` · `warn` · `err` | same |
| syntax string · number · keyword · comment | `sub` · `fg` · `accent` · `dim` (muted) | `ok` · `purple` · `turquoise` · `dim` |
| diff bg / word | `diff_add`/`diff_del`, `ok`/`err` | same |

### yazi

cwd, selected marker, active tab, mode normal, borders of input/confirm: `accent` (text on it `bg`). Status/tab strip `bar`; borders `surface`; selection `rule`. Directories `info`, executables `ok`, symlinks `turquoise`, hidden `dim`, archives `warn`, media `pink`, images `yellow`, broken `err` on `diff_del`. Notify info/warn/error: `accent`/`yellow`/`err`.

### lazygit

Active border `accent`, inactive `ghost`, searching `yellow`, options `info`, selected line `rule`, inactive selected `surface`, cherry-picked `purple` on `surface`, marked base `info` on `yellow`, unstaged `err`, default text `fg`.

### starship

Fragment `[palettes.black_ruby]`: `base01`=`dim`, `base0`=`sub`, `yellow`, `orange`=`warn`, `red`=`err`, `magenta`=`pink`, `violet`=`purple`, `blue`=`info`, `cyan`=`turquoise`, `green`=`ok`.

Live `~/tools/d0t_file/starship.toml` (linked from `~/.config/starship.toml`) uses `[palettes.cindy]`, keys named after Colours. Prompt `❯` `accent` (fail `err`); directory `info`; branch `purple`; detached hash / hostname `dim`; git state `yellow`; dirty status `warn` (staged `ok`, conflicts `err`); line metrics `ok`/`err`; jobs `turquoise`; exit code `err`; duration `yellow`. Runtimes use spare hues only (never `accent`/`err`).

### neofetch

Shell variables named after Colours (`ruby`=`accent`, `fg`, `sub`, `dim`, `ghost`, `rule`, `info_c`=`info`, `turq`=`turquoise`, `purple`, `pink`, `yellow`, `ok`); frame lines `rule`.
