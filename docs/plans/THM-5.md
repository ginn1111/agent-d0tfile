---
status: approved
scope: Execution order for THM-5 (VS Code Dark Modern theme), split into 3 cards
owner: Gin
---

# Plan — THM-5 VS Code Dark Modern theme

Spec: `docs/specs/THM-5.md`. Source of hexes: `sketches/006-vscode-faithful/index.html` and `sketches/themes/vscode.css`.

## Cards

| Card | Assignee | Depends on | Repo(s) |
|---|---|---|---|
| THM-5.1 Restore theme system + VS Code palette + registry + tests | ginb | none | agent-d0tfile |
| THM-5.2 Recolour TUIs + Hermes skins (in-repo Targets) | ginb | THM-5.1 | agent-d0tfile (+ live herdr/starship blocks in d0t_file) |
| THM-5.3 Recolour desktop (i3, xborders, polybar, rofi, dunst+picom shader, picom, neofetch) | ginb | THM-5.1 | d0t_file |

THM-5.2 and THM-5.3 can run in parallel after 5.1.

## THM-5.1 steps

1. `git checkout f087465^ -- themes/cindy tests/test_theme_cindy_palette.py tests/test_install_theme_cindy.py`. Run `python3 -m unittest discover -s tests` and confirm it is green with Warm Dusk as the baseline.
2. `git tag theme-warm-dusk` on the restore commit.
3. Write `themes/cindy/vscode-dark-modern.palette`: the 006 `:root` values, plus `accent_text`, `syn_string`, `syn_number`, `syn_comment`, `mode_*`, `match_bg` and `match_edge` from `vscode.css`. Use `@alias` for the repeated greys.
4. Test changes: point `PALETTE` at the new palette and resolve `@alias`. The uniqueness check covers literal hexes only. In the comfort check, `accent` is fill-only and `accent_text` must be ≥4.5 on `bg`. Write the tests first and watch them fail before the palette lands.
5. REGISTRY.md: update the Palette line, the Warm Dusk inactive note, rule 5 (text on fill is `fg_bright`), and Roles for `accent_text`, syntax, modes and match. Leave the Worked Targets text for 5.2/5.3 to update per tool.
6. Repoint installer `LINKS` skin names to `vscode-cindy`/`vscode-ginb`, and the profile `skin:` edits too. Update `tests/test_install_theme_cindy.py` to match.
7. Verify with `python3 -m unittest discover -s tests` and `make theme-cindy-dry-run`. Paste the output into the card.

## THM-5.2 steps

For each in-repo Target, rewrite the colours by Role using the Registry: nvim `colorscheme.lua` (mini.base16, plus syntax highlight overrides for the VS Code token colours), `lualine.lua` (mode fills `mode_*`, white text), `yazi-theme.toml`, `lazygit.yml`, `herdr-theme.toml`, `starship-palette.toml`, `hermes-skin.yaml` → `vscode-cindy`, and `hermes-skin-ginb.yaml` → `vscode-ginb`. Then update the live herdr block and live `starship.toml` `[palettes.cindy]` in d0t_file. Update the Worked Targets sections. Verify with the drift test at 0 strays and `make theme-cindy-dry-run`.

## THM-5.3 steps

Recolour by Role using the Worked Targets mappings: i3 `client.*` (text on `accent` = `fg_bright`), xborders tint `accent`+`e6`, polybar `[colors]` plus the workspaces script, rofi (new `colors/vscode-dark-modern.rasi`, imports switched, `black-ruby.rasi` kept), `dunstrc` plus `picom/dunst-rail.glsl` together, picom `shadow-color`, and neofetch. Add the new rofi file to Targets. Commit in d0t_file with only the theme files staged. Verify with the drift test, then `i3-msg reload`, `polybar` restart and `dunstify` test notifications on Gin's machine (only Gin can confirm visually).

## Gates

- Real `make theme-cindy` (install) needs Gin's approval of the dry-run.
- `git push` on either repo needs Gin's approval.
- Visual sign-off is Gin's.
