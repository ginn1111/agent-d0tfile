---
status: completed
scope: plan Tasks 8-11: installer, make targets, docs, harness state
owner: cindy
---

# THM-2 — Cindy Black & Ruby theme (feat-007)

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

- THM-1's branch is stacked under this one, so the theme files already exist.

## Step-by-step tasks

### Task 8 — Installer test (RED) (5 min)

Create `tests/test_install_theme_cindy.py`:

```python
import os
import subprocess
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "scripts" / "install_theme_cindy.py"
THEME = REPO / "themes" / "cindy"

FIXTURES = {
    ".config/kitty/kitty.conf": "font_size 12\n# include gruvbox.conf\ninclude solarized_osaka_dark.conf\n",
    ".config/yazi/theme.toml": '[app]\noverall = { fg = "#9eabac" }\n',
    ".config/lazygit/config.yml": "",
    ".config/nvim/lua/plugins/solarized.lua": "return {}\n",
    ".config/nvim/lua/plugins/lualine.lua": "return {}\n",
    ".config/herdr/config.toml": 'name = "solarized"\n\n[theme.custom]\naccent = "#268bd3"\n\n[terminal]\nshell_mode = "auto"\n',
    "dotfiles/starship.toml": 'palette = "solarized"\n\n[palettes.solarized]\ngreen = "#859900"\n\n[character]\nsuccess_symbol = "[>](green)"\n',
    ".hermes/profiles/cindy/config.yaml": "display:\n  skin: solarized-osaka-cindy\n  language: en\n",
    ".hermes/profiles/cindy/skins/solarized-osaka-cindy.yaml": "name: x\n",
}

LINKS = {
    ".config/kitty/black_ruby.conf": "kitty.conf",
    ".config/yazi/theme.toml": "yazi-theme.toml",
    ".config/lazygit/config.yml": "lazygit.yml",
    ".config/nvim/lua/plugins/bearded.lua": "nvim/bearded.lua",
    ".config/nvim/lua/plugins/lualine.lua": "nvim/lualine.lua",
    ".hermes/profiles/cindy/skins/black-ruby-cindy.yaml": "hermes-skin.yaml",
}


def snapshot(home):
    out = {}
    for p in sorted(home.rglob("*")):
        rel = str(p.relative_to(home))
        if p.is_symlink():
            out[rel] = ("link", os.readlink(p))
        elif p.is_file():
            out[rel] = ("file", p.read_bytes())
        else:
            out[rel] = ("dir", None)
    return out


class InstallThemeCindyTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name)
        for rel, text in FIXTURES.items():
            p = self.home / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text)
        # Real setup: ~/.config/starship.toml is a symlink into another repo.
        (self.home / ".config/starship.toml").symlink_to(self.home / "dotfiles/starship.toml")
        self.original = snapshot(self.home)

    def tearDown(self):
        self.tmp.cleanup()

    def run_script(self, *args):
        env = {**os.environ, "HOME": str(self.home), "HERMES_HOME": str(self.home / ".hermes")}
        r = subprocess.run([sys.executable, str(SCRIPT), *args], env=env, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return r.stdout

    def test_dry_run_writes_nothing(self):
        out = self.run_script("--dry-run")
        self.assertIn("would link", out)
        self.assertIn("would edit", out)
        self.assertEqual(snapshot(self.home), self.original)

    def test_install_links_edits_and_backs_up(self):
        self.run_script()
        for rel, src in LINKS.items():
            self.assertEqual((self.home / rel).resolve(), (THEME / src).resolve(), rel)
        plugins = self.home / ".config/nvim/lua/plugins"
        self.assertFalse((plugins / "solarized.lua").exists())
        self.assertEqual(len(list(plugins.glob("solarized.lua.pre-cindy.*"))), 1)
        kitty = (self.home / ".config/kitty/kitty.conf").read_text()
        self.assertIn("# include solarized_osaka_dark.conf", kitty)
        self.assertIn("\ninclude black_ruby.conf\n", kitty)
        herdr = tomllib.loads((self.home / ".config/herdr/config.toml").read_text())
        self.assertEqual(herdr["theme"]["custom"]["accent"], "#c62f52")
        self.assertEqual(herdr["terminal"]["shell_mode"], "auto")
        star_link = self.home / ".config/starship.toml"
        self.assertTrue(star_link.is_symlink(), "edit must write through the symlink")
        star = tomllib.loads(star_link.read_text())
        self.assertEqual(star["palette"], "black_ruby")
        self.assertEqual(set(star["palettes"]), {"black_ruby"})
        self.assertIn("  skin: black-ruby-cindy\n", (self.home / ".hermes/profiles/cindy/config.yaml").read_text())

    def test_second_run_is_noop(self):
        self.run_script()
        after = snapshot(self.home)
        out = self.run_script()
        self.assertEqual(snapshot(self.home), after)
        self.assertTrue(all(line.startswith("ok ") for line in out.splitlines()), out)

    def test_restore_returns_original(self):
        self.run_script()
        installed = snapshot(self.home)
        self.run_script("--restore", "--dry-run")
        self.assertEqual(snapshot(self.home), installed)
        self.run_script("--restore")
        self.assertEqual(snapshot(self.home), self.original)


if __name__ == "__main__":
    unittest.main()
```

Run: `python3 -m unittest tests.test_install_theme_cindy -v`. Expect 4 **FAIL**s, with return code ≠ 0 and `can't open file ... install_theme_cindy.py`.

### Task 9 — Installer (GREEN) (5 min)

Create `scripts/install_theme_cindy.py`:

```python
#!/usr/bin/env python3
"""Install the Cindy Black & Ruby theme into ~/.config and the cindy Hermes profile.

Usage: install_theme_cindy.py [--dry-run] [--restore]
  (none)     link/retire/edit; replaced files saved as <file>.pre-cindy.<stamp>
  --dry-run  print what would happen, write nothing
  --restore  put back the oldest .pre-cindy.* backups, remove created links
Env: HOME, HERMES_HOME (default ~/.hermes).
"""
import os
import re
import shutil
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "themes" / "cindy"
CFG = Path.home() / ".config"
PROFILE = Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes")) / "profiles" / "cindy"
TAG = ".pre-cindy."
STAMP = time.strftime("%Y%m%d-%H%M%S")
BEGIN, END = "# >>> cindy theme", "# <<< cindy theme"

LINKS = [  # (repo source, target)
    (SRC / "kitty.conf", CFG / "kitty" / "black_ruby.conf"),
    (SRC / "yazi-theme.toml", CFG / "yazi" / "theme.toml"),
    (SRC / "lazygit.yml", CFG / "lazygit" / "config.yml"),
    (SRC / "nvim" / "bearded.lua", CFG / "nvim" / "lua" / "plugins" / "bearded.lua"),
    (SRC / "nvim" / "lualine.lua", CFG / "nvim" / "lua" / "plugins" / "lualine.lua"),
    (SRC / "hermes-skin.yaml", PROFILE / "skins" / "black-ruby-cindy.yaml"),
]
RETIRE = [CFG / "nvim" / "lua" / "plugins" / "solarized.lua"]


def swap(text, table, block):
    """Put block between markers; first run replaces TOML `table` (header to next header) or appends."""
    block = f"{BEGIN}\n{block.rstrip()}\n{END}\n"
    if BEGIN in text:
        return re.sub(rf"{re.escape(BEGIN)}.*?{re.escape(END)}\n?", lambda _: block, text, flags=re.S)
    m = table and re.search(rf"^{re.escape(table)}\n.*?(?=^\[|\Z)", text, flags=re.S | re.M)
    if m:
        return text[: m.start()] + block + "\n" + text[m.end():]
    return text.rstrip("\n") + "\n\n" + block


def sub_line(pattern, repl, text):
    return re.sub(pattern, repl, text, count=1, flags=re.M)


def frag(name):
    return (SRC / name).read_text()


EDITS = [  # (target, text -> text)
    (CFG / "kitty" / "kitty.conf",
     lambda t: swap(re.sub(r"^include (?!black_ruby\.conf)", "# include ", t, flags=re.M), None, "include black_ruby.conf")),
    (CFG / "herdr" / "config.toml",
     lambda t: swap(t, "[theme.custom]", frag("herdr-theme.toml"))),
    (CFG / "starship.toml",
     lambda t: swap(sub_line(r"^palette = .*$", 'palette = "black_ruby"', t), "[palettes.solarized]", frag("starship-palette.toml"))),
    (PROFILE / "config.yaml",
     lambda t: sub_line(r"^([ \t]*skin:[ \t]*).*$", r"\g<1>black-ruby-cindy", t)),
]


def backup(p):
    return p.with_name(p.name + TAG + STAMP)


def backups(p):
    return sorted(p.parent.glob(p.name + TAG + "*"))


def act(dry, msg, fn):
    print(("would " if dry else "") + msg)
    if not dry:
        fn()


def install(dry):
    for p in RETIRE:
        if p.exists():
            act(dry, f"retire {p} -> {backup(p).name}", lambda p=p: p.rename(backup(p)))
    for src, dst in LINKS:
        if dst.is_symlink() and dst.resolve() == src.resolve():
            print(f"ok {dst}")
            continue

        def link(src=src, dst=dst):
            dst.parent.mkdir(parents=True, exist_ok=True)
            if dst.exists() or dst.is_symlink():
                dst.rename(backup(dst))
            dst.symlink_to(src)

        act(dry, f"link {dst} -> {src}", link)
    for path, fn in EDITS:
        if not path.exists():
            print(f"missing {path}; skipped")
            continue
        old = path.read_text()
        new = fn(old)
        if new == old:
            print(f"ok {path}")
            continue

        def edit(path=path, new=new):
            shutil.copy2(path, backup(path))  # keeps mode (config.yaml is 0600)
            path.write_text(new)  # writes through symlinks (starship.toml)

        act(dry, f"edit {path} (backup {backup(path).name})", edit)


def restore(dry):
    for path in [dst for _, dst in LINKS] + RETIRE:
        found = backups(path)
        if found:
            def put_back(path=path, found=found):
                if path.is_symlink():
                    path.unlink()
                found[0].rename(path)
                for extra in found[1:]:
                    extra.unlink()

            act(dry, f"restore {path} <- {found[0].name}", put_back)
        elif path.is_symlink() and path.resolve().is_relative_to(SRC.resolve()):
            act(dry, f"unlink {path}", path.unlink)
    for path, _ in EDITS:
        found = backups(path)
        if found:
            def put_back(path=path, found=found):
                path.write_text(found[0].read_text())
                for b in found:
                    b.unlink()

            act(dry, f"restore {path} <- {found[0].name}", put_back)


def main(argv):
    args = set(argv)
    if not args <= {"--dry-run", "--restore"}:
        print(__doc__, file=sys.stderr)
        return 2
    (restore if "--restore" in args else install)("--dry-run" in args)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
```

Then `chmod +x scripts/install_theme_cindy.py`.

Run: `python3 -m unittest tests.test_install_theme_cindy -v`. Expect `Ran 4 tests ... OK`.

If `test_restore_returns_original` fails on a `dir` entry, check that no step creates a new directory: every fixture parent already exists.

Commit: `git add scripts/install_theme_cindy.py tests/test_install_theme_cindy.py && git commit -m "feat(themes): add install_theme_cindy.py with dry-run and restore"`

### Task 10 — Make targets (3 min)

Edit `Makefile`. Re-read it first, because another session recently removed some targets.

1. Below the other script variables, add `INSTALL_THEME_CINDY := scripts/install_theme_cindy.py`.
2. Append a continuation line to `.PHONY`: `theme-cindy theme-cindy-dry-run theme-cindy-restore theme-cindy-restore-dry-run`. Add ` \` to the previous last line.
3. In `help`, before the `''` line, add:
   ```make
   	  '  make theme-cindy                # link cindy Black & Ruby theme into ~/.config + cindy profile (backs up originals)' \
   	  '  make theme-cindy-dry-run        # preview theme links/edits without writing' \
   	  '  make theme-cindy-restore        # restore pre-cindy originals, remove theme links' \
   	  '  make theme-cindy-restore-dry-run # preview restore without writing' \
   ```
4. At the end of the file (recipe lines start with a TAB):
   ```make
   theme-cindy:
   	@python3 '$(INSTALL_THEME_CINDY)'

   theme-cindy-dry-run:
   	@python3 '$(INSTALL_THEME_CINDY)' --dry-run

   theme-cindy-restore:
   	@python3 '$(INSTALL_THEME_CINDY)' --restore

   theme-cindy-restore-dry-run:
   	@python3 '$(INSTALL_THEME_CINDY)' --restore --dry-run
   ```

Verify. This is safe because both targets are dry runs:

```bash
make help | grep theme-cindy            # 4 lines
make theme-cindy-dry-run                # every line starts "would " or "ok " or "missing "; nothing written
make theme-cindy-restore-dry-run        # prints nothing (no backups yet)
```

Commit: `git commit -m "feat(make): add theme-cindy install/restore targets" -- Makefile`

### Task 11 — Docs + harness state (4 min)

1. In `docs/plans/2026-11-12-cindy-black-ruby-theme-design.md`, apply the deviations table above:
   - the script name;
   - fragment file names;
   - restore uses the **oldest** backup;
   - `diff_add`/`diff_del` tokens;
   - lowercase hex;
   - herdr has no `bg_agent`.
2. In `README.md`, next to the existing `make us-dry-run` lines in Quick Start, add the 4 `make theme-cindy*` lines with the same comments as `help`.
3. Run `./init.sh`. Expect the existing tests plus the new ones to pass and `=== Verification Complete ===`.
4. In `feature_list.json` feat-007, set `"evidence": "./init.sh OK (N tests); python3 -m unittest tests.test_install_theme_cindy tests.test_theme_cindy_palette OK; make theme-cindy-dry-run OK"`, using the real N. Leave status `in-progress` until Task 13.
5. Update `progress.md` (Current State, Active Feature feat-007, What's Next) and `session-handoff.md` (objective, verification evidence rows).

Commit: `git add README.md docs/plans/2026-11-12-cindy-black-ruby-theme-design.md feature_list.json progress.md session-handoff.md && git commit -m "docs(themes): document theme-cindy targets, sync design + harness"`

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
