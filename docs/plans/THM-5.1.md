---
status: completed
scope: THM-5.1 execution order
owner: Gin
---

# Plan — THM-5.1 Restore theme system + VS Code Dark Modern palette, registry, tests

Parent plan: `docs/plans/THM-5.md`.

1. `git checkout f087465^ -- themes/cindy tests/test_theme_cindy_palette.py tests/test_install_theme_cindy.py`, commit, tag `theme-warm-dusk`
2. Write the new tests first (they fail), then the palette, Registry and installer rename (they pass)
3. Run `python3 -m unittest discover -s tests` and `make theme-cindy-dry-run`
