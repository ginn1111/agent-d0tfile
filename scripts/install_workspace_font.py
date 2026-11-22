#!/usr/bin/env python3
"""Install the Workspace Font (Terminess Nerd Font) rootless and point desktop Targets at it.

Usage: install_workspace_font.py [--dry-run] [--restore]
  (none)     install font files, edit Targets; edited files saved as <file>.pre-wsfont.<stamp>
  --dry-run  print what would happen, write nothing
  --restore  put back the oldest .pre-wsfont.* backups, remove font files this script installed
Platforms: Linux (i3, polybar, rofi, dunst; fonts in ~/.local/share/fonts)
           macOS (sketchybar labels; icons stay SF Symbols; fonts in ~/Library/Fonts)
kitty is never touched (RULES.md).
Env: HOME; WORKSPACE_FONT_ARCHIVE=<local Terminus.tar.xz> skips the download;
     WORKSPACE_FONT_PLATFORM=linux|macos overrides detection.
"""
import io
import os
import re
import shutil
import subprocess
import sys
import tarfile
import time
import urllib.request
from pathlib import Path

FAMILY = "Terminess Nerd Font"
URL = "https://github.com/ryanoasis/nerd-fonts/releases/latest/download/Terminus.tar.xz"
TAG = ".pre-wsfont."
STAMP = time.strftime("%Y%m%d-%H%M%S")
HOME = Path.home()
CFG = HOME / ".config"
PLATFORM = os.environ.get("WORKSPACE_FONT_PLATFORM") or ("macos" if sys.platform == "darwin" else "linux")
FONT_DIR = HOME / "Library" / "Fonts" if PLATFORM == "macos" else HOME / ".local" / "share" / "fonts" / "terminess"
MANIFEST = FONT_DIR / ".workspace-font-installed"  # lists files this script added
ICON_FONTS = r"feather|sketchybar-app-font|" + re.escape(FAMILY)
HEAVY = {"Semibold": "Bold", "Black": "Bold", "Heavy": "Bold", "Medium": "Regular", "Light": "Regular"}


def i3(t):
    return re.sub(r"^font pango:.*$", f"font pango:{FAMILY} 10", t, count=1, flags=re.M)


def polybar(t):
    # font-0 / font-1 are text slots; later slots are glyph fallbacks and stay.
    return re.sub(r"^(font-[01]\s*=\s*)[^:;\n]+", rf"\g<1>{FAMILY}", t, flags=re.M)


def rofi(t):
    # "Family [Bold|Italic …] 12" inside any line mentioning font; icon fonts skipped.
    pat = re.compile(rf'"(?!{ICON_FONTS})([A-Za-z][A-Za-z ]*?)((?: (?:Bold|Italic|Regular|Semibold|Light))* \d+(?:\.\d+)?)"')
    return "".join(pat.sub(lambda m: f'"{FAMILY}{m[2]}"', line) if "font" in line.lower() else line
                   for line in t.splitlines(keepends=True))


def dunst(t):
    return re.sub(r"^(\s*font\s*=\s*).+?(\s+\d+(?:\.\d+)?)(?=\s*(?:#|$))", rf"\g<1>{FAMILY}\g<2>", t, count=1, flags=re.M)


def sketchybar(t):
    # Labels only: icons are SF Symbols (need SF Pro) / app-font glyphs, so icon.font and $FONT stay.
    pat = re.compile(rf'(label\.font=")(?!{ICON_FONTS})(?:\$FONT|[^":]+):(\w+)')
    return pat.sub(lambda m: f"{m[1]}{FAMILY}:{HEAVY.get(m[2], m[2])}", t)


def targets():
    """(path, fn) for this platform. Globs resolve now; symlinked dirs are followed."""
    if PLATFORM == "macos":
        sb = CFG / "sketchybar"
        return [(p, sketchybar) for p in [sb / "sketchybarrc", *sorted(sb.glob("items/*.sh"))]]
    rofi_files = sorted(p for p in (CFG / "rofi").rglob("*") if p.suffix in {".rasi", ".sh"} and TAG not in p.name
                        and ".bak" not in p.name) if (CFG / "rofi").exists() else []
    return [(CFG / "i3" / "config", i3), (CFG / "polybar" / "config.ini", polybar),
            (CFG / "dunst" / "dunstrc", dunst), *[(p, rofi) for p in rofi_files]]


def act(dry, msg, fn):
    print(("would " if dry else "") + msg)
    if not dry:
        fn()


def backups(path):
    return sorted(path.parent.glob(path.name + TAG + "*"))


def font_files(archive):
    """Yield (name, bytes) for TTFs + license from the Nerd Fonts Terminus archive."""
    data = Path(archive).read_bytes() if archive else urllib.request.urlopen(URL, timeout=60).read()
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:xz") as tar:
        for m in tar.getmembers():
            name = Path(m.name).name
            if m.isfile() and (name.startswith("TerminessNerdFont") and name.endswith(".ttf") or name == "LICENSE.txt"):
                f = tar.extractfile(m)
                if f:
                    yield name, f.read()


def install_font(dry):
    if MANIFEST.exists() and all((FONT_DIR / n).exists() for n in MANIFEST.read_text().split()):
        print(f"ok {FONT_DIR} ({FAMILY})")
        return
    if dry:
        print(f"would install {FAMILY} into {FONT_DIR}")
        return
    FONT_DIR.mkdir(parents=True, exist_ok=True)
    added = []
    for name, blob in font_files(os.environ.get("WORKSPACE_FONT_ARCHIVE")):
        dst = FONT_DIR / ("Terminess-LICENSE.txt" if PLATFORM == "macos" and name == "LICENSE.txt" else name)
        if not dst.exists():
            dst.write_bytes(blob)
            added.append(dst.name)
    MANIFEST.write_text("\n".join(sorted(added + (MANIFEST.read_text().split() if MANIFEST.exists() else []))) + "\n")
    print(f"install {FAMILY} into {FONT_DIR} ({len(added)} files)")
    if PLATFORM == "linux" and shutil.which("fc-cache"):
        subprocess.run(["fc-cache", "-f", str(FONT_DIR)], check=False)


def install(dry):
    install_font(dry)
    for path, fn in targets():
        if not path.exists():
            print(f"missing {path}; skipped")
            continue
        old = path.read_text()
        new = fn(old)
        if new == old:
            print(f"ok {path}")
            continue

        def edit(path=path, new=new):
            shutil.copy2(path, path.with_name(path.name + TAG + STAMP))
            path.write_text(new)  # writes through symlinks into dotfile repos

        act(dry, f"edit {path}", edit)
    if not dry:
        print("reload: " + ("sketchybar --reload" if PLATFORM == "macos"
                            else "i3-msg reload; polybar/rofi pick it up; restart dunst"))


def restore(dry):
    for path, _ in targets():
        found = backups(path)
        if found:
            def put_back(path=path, found=found):
                path.write_text(found[0].read_text())
                for b in found:
                    b.unlink()

            act(dry, f"restore {path} <- {found[0].name}", put_back)
    if MANIFEST.exists():
        def remove_fonts():
            for n in MANIFEST.read_text().split():
                (FONT_DIR / n).unlink(missing_ok=True)
            MANIFEST.unlink()
            if PLATFORM == "linux" and not any(FONT_DIR.iterdir()):
                FONT_DIR.rmdir()

        act(dry, f"remove {FAMILY} from {FONT_DIR}", remove_fonts)


def main(argv):
    args = set(argv)
    if not args <= {"--dry-run", "--restore"} or PLATFORM not in {"linux", "macos"}:
        print(__doc__, file=sys.stderr)
        return 2
    (restore if "--restore" in args else install)("--dry-run" in args)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
