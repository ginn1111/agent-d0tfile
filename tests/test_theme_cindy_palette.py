import os
import pwd
import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
THEME = REPO / "themes" / "cindy"
REGISTRY = THEME / "REGISTRY.md"
PALETTE = THEME / "warm-dusk.palette"
# 8-digit first so "#c62f52e6" is read as one Tint, not "#c62f52" + "e6".
HEX = re.compile(r"#([0-9a-fA-F]{8}|[0-9a-fA-F]{6})\b")
BEGIN, END = "# >>> cindy theme", "# <<< cindy theme"
# Login home, not $HOME: Hermes profile sessions point HOME at a profile dir.
LOGIN_HOME = Path(pwd.getpwuid(os.getuid()).pw_dir)


def palette():
    names = {}
    for line in PALETTE.read_text().splitlines():
        if line.strip() and not line.startswith("#"):
            name, value = line.split("=", 1)
            names[name.strip()] = value.strip().lower()
    return names


def contrast(a, b):
    """WCAG contrast ratio of two #rrggbb colours."""
    def lum(h):
        rgb = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
        rgb = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]
        return 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]
    hi, lo = sorted((lum(a), lum(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


# Eye comfort: readable everywhere, but no glare (body text capped at 12:1).
SIGNALS = ("accent", "err", "warn", "ok", "info", "yellow", "purple", "pink", "turquoise", "green_alt")
COMFORT = (
    [("fg", "bg", 7.0, 12.0)]
    + [("fg", b, 7.0, 99) for b in ("bg_agent", "bg_ginb", "surface", "rule", "rule_ginb")]
    + [("sub", "bg", 4.5, 99), ("sub", "bar", 4.5, 99), ("dim", "bg", 3.0, 99)]
    + [(h, "bg", 4.5, 99) for h in SIGNALS]
)


def section(title):
    text = REGISTRY.read_text()
    start = text.index(f"\n## {title}\n")
    end = text.find("\n## ", start + 1)
    return text[start:end if end != -1 else None]


def table_rows(text):
    rows = [l for l in text.splitlines() if l.startswith("|")]
    return [[c.strip() for c in r.strip("|").split("|")] for r in rows[2:]]


def targets():
    out = []
    for name, path, scope in table_rows(section("Targets")):
        path = path.strip("`")
        p = LOGIN_HOME / path[2:] if path.startswith("~/") else REPO / path
        out.append((name, p, scope))
    return out


def stray(text, colours):
    found = set()
    for m in HEX.finditer(text):
        h = m.group(1).lower()
        if len(h) == 8 and h[6:] == "00":  # fully transparent is free
            continue
        if "#" + h[:6] not in colours:
            found.add("#" + h[:6])
    return sorted(found)


class ThemeCindyPaletteTest(unittest.TestCase):
    def test_palette_names_and_hex_are_unique(self):
        names = palette()
        lines = [l for l in PALETTE.read_text().splitlines() if l.strip() and not l.startswith("#")]
        self.assertEqual(len(names), len(lines), "duplicate Colour name")
        self.assertEqual(len(set(names.values())), len(names), "two Colours share a hex")

    def test_palette_is_comfortable(self):
        p = palette()
        for fg, bg, lo, hi in COMFORT:
            with self.subTest(pair=f"{fg} on {bg}"):
                r = round(contrast(p[fg], p[bg]), 2)
                self.assertGreaterEqual(r, lo, f"{fg} on {bg}")
                self.assertLessEqual(r, hi, f"{fg} on {bg}")

    def test_registry_names_only_palette_colours(self):
        names = palette()
        for title in ("Roles", "Variants"):
            for row in table_rows(section(title)):
                for cell in row[1:]:
                    for token in re.findall(r"`([a-z_]+)`", cell):
                        if token in ("cindy", "ginb"):
                            continue
                        self.assertIn(token, names, f"{title}: `{token}` is not a Palette Colour")

    def test_theme_files_with_colours_are_listed_targets(self):
        listed = {p.resolve() for _, p, _ in targets()}
        for p in THEME.rglob("*"):
            if p.is_file() and p.suffix != ".palette" and HEX.search(p.read_text()):
                self.assertIn(p.resolve(), listed, f"{p} uses colours but is not in REGISTRY.md Targets")

    def test_targets_use_only_palette_colours(self):
        colours = set(palette().values())
        rows = targets()
        self.assertTrue(rows, "no Targets in REGISTRY.md")
        for name, path, scope in rows:
            with self.subTest(target=name, path=str(path)):
                if not path.exists():
                    self.skipTest(f"missing on this machine: {path}")
                text = path.read_text()
                if scope == "block":
                    self.assertIn(BEGIN, text, f"{path}: no cindy theme block")
                    text = text[text.index(BEGIN):text.index(END)]
                self.assertEqual(stray(text, colours), [], f"{path}: Stray Colours")


if __name__ == "__main__":
    unittest.main()
