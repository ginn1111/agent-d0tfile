---
status: completed
card: THM-5.1
assignee: ginb
blocked_by: []
parent_spec: docs/specs/THM-5.md
scope: Restore theme system + VS Code Dark Modern palette, registry, tests
owner: Gin
---

# Spec — THM-5.1 Restore theme system + VS Code Dark Modern palette, registry, tests

Parent: `docs/specs/THM-5.md` (umbrella; stays approved until all cards are done).

## Problem
`themes/cindy/` and its tests were deleted in `f087465`. The VS Code palette and its rules (aliases, fill-only accent) don't exist yet. Parent spec: `docs/specs/THM-5.md`.

## Desired behavior
- Restore `themes/cindy/` and both theme tests from `f087465^`. Tag the restore `theme-warm-dusk`.
- Add `vscode-dark-modern.palette`, with every hex taken from sketch 006 or `vscode.css`, and `@alias` for the repeated greys.
- Point the Registry and the drift test at that palette. `accent` is fill-only; `accent_text` must be ≥4.5. Text on a fill is `fg_bright`.
- Rename the installer's skins to `vscode-cindy` / `vscode-ginb`.
- Leave Target files unchanged. They are skipped by `PENDING_RECOLOUR` until THM-5.2/5.3.

## Acceptance criteria
- [x] `python3 -m unittest discover -s tests` passes (28 tests, OK, 18 skipped)
- [x] Palette hexes all appear in the sketch (re-checked by Cindy: 0 missing)
- [x] Registry updated, Warm Dusk inactive, tag `theme-warm-dusk` → 679b6a4
- [x] Commits 679b6a4, f35d676, local only
