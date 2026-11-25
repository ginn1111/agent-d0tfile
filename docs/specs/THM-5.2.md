---
status: completed
card: THM-5.2
assignee: ginb
blocked_by: [THM-5.1]
parent_spec: docs/specs/THM-5.md
scope: Recolour TUIs + Hermes skins to VS Code Dark Modern
owner: Gin
---

# Spec — THM-5.2 Recolour TUIs + Hermes skins to VS Code Dark Modern

Parent: `docs/specs/THM-5.md` (umbrella; stays approved until all cards are done).

## Problem
The in-repo TUI Targets and both Hermes skins still carry Warm Dusk hexes. Parent spec: `docs/specs/THM-5.md`.

## Desired behavior
Recolour by Role, following `themes/cindy/REGISTRY.md`:
- nvim colorscheme, with the VS Code syntax overrides
- lualine, with `mode_*` fills and `fg_bright` text
- yazi, lazygit, herdr (source + live block), starship (fragment + live `[palettes.cindy]`)
- Hermes skins `vscode-cindy` and `vscode-ginb`; `vscode-ginb` keeps turquoise focus with `bg` text

Then remove these Targets from `PENDING_RECOLOUR` and update the Worked Targets sections.

## Acceptance criteria
- [ ] Drift test shows 0 Stray Colours for these Targets (with none left in `PENDING_RECOLOUR`); missing ones are listed
- [ ] `python3 -m unittest discover -s tests` passes; `make theme-cindy-dry-run` output is on the card
- [ ] No real install, local commits only, kitty untouched
