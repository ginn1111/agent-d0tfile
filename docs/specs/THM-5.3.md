---
status: completed
card: THM-5.3
assignee: ginb
blocked_by: [THM-5.1]
parent_spec: docs/specs/THM-5.md
scope: Recolour desktop to VS Code Dark Modern
owner: Gin
---

# Spec — THM-5.3 Recolour desktop to VS Code Dark Modern

Parent: `docs/specs/THM-5.md` (umbrella; stays approved until all cards are done).

## Problem
The desktop Targets in the d0t_file repo still carry Warm Dusk hexes. Parent spec: `docs/specs/THM-5.md`.

## Desired behavior
Recolour by Role:
- i3 `client.*` (text on `accent` is `fg_bright`), and the xborders tint `accent`+`e6`
- polybar `[colors]` and the workspaces script
- a new `rofi/colors/vscode-dark-modern.rasi`, with the imports switched to it
- dunstrc and `dunst-rail.glsl` together
- picom `shadow-color`
- neofetch

Then remove these Targets from `PENDING_RECOLOUR` and add the rofi row in agent-d0tfile.

## Acceptance criteria
- [ ] Drift test shows 0 Stray Colours for the desktop Targets; missing ones are listed
- [ ] Shader `vec3()` values match the new card backgrounds (listed in the evidence)
- [ ] In d0t_file, only theme files are staged; local commits only; live reload and visual sign-off left to Gin
