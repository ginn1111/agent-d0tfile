---
status: approved
card: THM-5
assignee: ginb
blocked_by: []
scope: Make VS Code Dark Modern (sketch 006-vscode-faithful) the active Cindy theme across TUIs, Hermes skins and desktop; Warm Dusk kept inactive
owner: Gin
---

# Spec — VS Code Dark Modern theme (THM-5)

## Problem

Gin picked `sketches/006-vscode-faithful` ("my desktop = my VS Code"). The theme system that would carry it (`themes/cindy/`, the Theme Registry, the drift test and the installer's sources) was deleted in `f087465`. `scripts/install_theme_cindy.py` and the `make theme-cindy*` targets still reference `themes/cindy/`, so they are broken today.

## Desired behavior

1. `themes/cindy/` and its tests are restored from `f087465^`, unchanged in behaviour.
2. A new Palette `themes/cindy/vscode-dark-modern.palette` holds the hex values from `sketches/006-vscode-faithful/index.html` `:root`, using the same Colour names as `warm-dusk.palette`.
3. `REGISTRY.md` names VS Code Dark Modern as the active Palette. Warm Dusk becomes inactive in the same way Black & Ruby is today, and is tagged `theme-warm-dusk` so Gin can switch back.
4. Every Target in the Registry uses only VS Code Dark Modern Colours:
   - TUIs: nvim colorscheme, lualine, yazi, lazygit, herdr (source and live), starship (fragment and live)
   - Hermes skins: cindy and ginb
   - Desktop (d0t_file repo): i3 and xborders, polybar plus its workspaces script, rofi, dunst plus the picom rail shader, picom, neofetch
5. The `ginb` Variant keeps its own focus colour, `turquoise` (#4EC9B0), as in the sketch's `variant` toggle.
6. Nvim syntax uses the VS Code token colours from `sketches/themes/vscode.css`. Keyword is `purple`, function `yellow`, type `turquoise` and variable `green_alt`. String, number and comment use the new `syn_*` Colours (see Palette decisions).

## Palette decisions (VS Code specifics)

Several things in VS Code Dark Modern clash with existing Registry rules. Each needs a decision:

| Issue | Decision |
|---|---|
| Hex reuse: `bg_alt`=`bg_agent`=`bar`=`bg_ginb`=`bar_ginb`=#181818; `bg_mid`=`card`=#202020; `border`=`rule`=`rule_ginb`=#2B2B2B | Allow intentional aliases. The palette syntax gains `name=@other` (an alias to another Colour). The uniqueness test checks only literal hexes. This is faithful to VS Code without inventing near-duplicate greys. |
| `accent` #0078D4 is 3.64:1 on `bg`, below the 4.5 signal floor | `accent` is a fill-only Colour, as in VS Code. Add `accent_text`=#4DAAFC (VS Code textLink, about 6.6:1) for focus text such as the prompt and active labels. The comfort test exempts `accent` from the text check and checks `accent_text` instead. Rule 5 changes for VS Code: text on `accent` fill is `fg_bright` (#FFFFFF), not `bg`. |
| Syntax colours not in the base palette: string #CE9178, number #B5CEA8, comment #6A9955, function #DCDCAA (=`yellow`) | Add `syn_string`, `syn_number` and `syn_comment` as Colours, with the Role "syntax". Keywords use `purple`, types `turquoise`, functions `yellow`, variables `green_alt`. |
| Mode colours (VS Code status bar): insert #16825D, visual #68217A, replace #C72E0F, command #CC6633, terminal #0E639C | Add `mode_insert`, `mode_visual`, `mode_replace`, `mode_command` and `mode_terminal` (fills, with white text). Normal mode uses `accent`. |
| Search match: bg #623315, outline #9E6A03 | Add `match_bg` and `match_edge`. |
| `fg` on `bg` is 10.26 and `fg_bright` is #FFFFFF | Within the comfort range (body text ≤12). No change. |

## Constraints

- Hex values come only from sketch 006-vscode-faithful and `sketches/themes/vscode.css`. Do not invent hexes.
- Warm Dusk and Black & Ruby files stay in the repo and are not used by any Target.
- kitty is untouched unless Gin names it (RULES.md). `themes/cindy/kitty.conf` stays Warm Dusk, and its Targets row is removed. The installer's kitty link and edit stay but are not run for this theme. **Open question for Gin.**
- The d0t_file repo has a large unrelated dirty tree. Commit only the theme files, in their own commits.
- The test paths use `~/tools/...` (the login home). In the sandbox, the repos are at `/workspace/tools`. Targets that are missing are skipped, so verification there also needs the repo-relative checks to run.
- No real install (`make theme-cindy`) until Gin approves the dry-run output.

## Acceptance criteria

- [ ] `themes/cindy/` and `tests/test_theme_cindy_palette.py` and `tests/test_install_theme_cindy.py` are restored. `python3 -m unittest discover -s tests` passes.
- [ ] `vscode-dark-modern.palette` exists. Every hex in it appears in sketch 006 or in `vscode.css`.
- [ ] REGISTRY.md: Palette line, Variants, Roles (including `accent_text`, syntax, modes and match) and Worked Targets are updated for VS Code. Warm Dusk is marked inactive and tagged `theme-warm-dusk`.
- [ ] The drift test points at `vscode-dark-modern.palette`, supports `@alias`, and passes with 0 Stray Colours for every Target that exists.
- [ ] The comfort test passes with the VS Code rules (accent fill-only, `accent_text` ≥4.5).
- [ ] `make theme-cindy-dry-run` lists the expected links and edits, and the output is shown to Gin.
- [ ] Visual check: Gin confirms (screenshot or live) that nvim, the Hermes panes and the desktop match the sketch.

## Edge cases

- When a Target file is missing on the machine, the test skips it rather than failing. The card must list which Targets were skipped.
- The picom rail shader hard-codes `vec3()` colours the test cannot see. Change it together with the dunst card backgrounds.
- The Hermes skin `name:` stays `black-ruby-cindy` / `black-ruby-ginb` so that profile `config.yaml` needs no edit, or it gets renamed to `vscode-cindy` together with the installer edit. **Default: rename, with the installer updated.**
