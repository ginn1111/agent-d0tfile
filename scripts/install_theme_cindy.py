#!/usr/bin/env python3
"""Install the Cindy Black & Ruby theme into ~/.config and the cindy Hermes profile.

Usage: install_theme_cindy.py [--dry-run] [--restore]
  (none)     link/retire/edit; replaced files saved as <file>.pre-cindy.<stamp>
  --dry-run  print what would happen, write nothing
  --restore  put back the oldest .pre-cindy.* backups, remove created links
Env: HOME. HERMES_HOME is ignored: inside a profile session it already points at a profile dir.
"""
import re
import shutil
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "themes" / "cindy"
CFG = Path.home() / ".config"
PROFILE = Path.home() / ".hermes" / "profiles" / "cindy"
GINB = PROFILE.parent / "ginb"  # ponytail: fixed root; HERMES_HOME is profile-scoped in sessions
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
    (SRC / "hermes-skin-ginb.yaml", GINB / "skins" / "black-ruby-ginb.yaml"),
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
    (GINB / "config.yaml",
     lambda t: sub_line(r"^([ \t]*skin:[ \t]*).*$", r"\g<1>black-ruby-ginb", t)),
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
