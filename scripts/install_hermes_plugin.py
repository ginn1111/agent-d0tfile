#!/usr/bin/env python3
"""Install Hermes plugins (including model-providers) from this repo into Hermes profiles.

Usage:
  install_hermes_plugin.py list
  install_hermes_plugin.py install <plugin> --profile <name> [--profile <name> ...] [--copy] [--force] [--dry-run]
  install_hermes_plugin.py install <plugin> --all-profiles [--copy] [--force] [--dry-run]
  install_hermes_plugin.py uninstall <plugin> --profile <name> [--dry-run]
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PLUGINS_ROOT = REPO_ROOT / "hermes" / "plugins"


@dataclass(frozen=True)
class PluginSpec:
    name: str
    kind: str
    source: Path

    @property
    def target_relpath(self) -> Path:
        if self.kind == "model-provider" or self.source.parent.name == "model-providers":
            return Path("plugins") / "model-providers" / self.name
        return Path("plugins") / self.name


def default_hermes_root() -> Path:
    override = os.environ.get("HERMES_ROOT")
    if override:
        return Path(override).expanduser()
    real_home = os.environ.get("HERMES_REAL_HOME")
    base_home = Path(real_home).expanduser() if real_home else Path.home()
    return base_home / ".hermes"


def _parse_kind(manifest: Path) -> str:
    for line in manifest.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("kind:"):
            return stripped.split(":", 1)[1].strip().strip("\"'")
    return "plugin"


def discover_plugins(plugins_root: Path = DEFAULT_PLUGINS_ROOT) -> list[PluginSpec]:
    if not plugins_root.is_dir():
        return []
    found: list[PluginSpec] = []
    for manifest in sorted(plugins_root.rglob("plugin.yaml")):
        plugin_dir = manifest.parent
        rel_parts = plugin_dir.relative_to(plugins_root).parts
        if len(rel_parts) > 2:
            continue
        found.append(
            PluginSpec(
                name=plugin_dir.name,
                kind=_parse_kind(manifest),
                source=plugin_dir.resolve(),
            )
        )
    return sorted(found, key=lambda p: p.name)


def discover_profiles(hermes_root: Path) -> dict[str, Path]:
    profiles: dict[str, Path] = {}
    if hermes_root.is_dir():
        profiles["default"] = hermes_root
    profiles_dir = hermes_root / "profiles"
    if profiles_dir.is_dir():
        for entry in sorted(profiles_dir.iterdir()):
            if entry.is_dir():
                profiles[entry.name] = entry
    return profiles


def _prompt_choice(title: str, items: list[str]) -> str:
    if not sys.stdin.isatty():
        raise SystemExit(f"Missing selection for {title}. Available: {', '.join(items) or '(none)'}")
    if not items:
        raise SystemExit(f"No {title} found.")
    print(f"Select {title}:", file=sys.stderr)
    for idx, item in enumerate(items, 1):
        print(f"  {idx}) {item}", file=sys.stderr)
    while True:
        raw = input(f"{title.capitalize()} number: ").strip()
        if raw.isdigit() and 1 <= int(raw) <= len(items):
            return items[int(raw) - 1]
        print(f"Enter number 1-{len(items)}.", file=sys.stderr)


def resolve_plugin(name: str | None, plugins: list[PluginSpec]) -> PluginSpec:
    if not name:
        name = _prompt_choice("plugin", [p.name for p in plugins])
    for p in plugins:
        if p.name == name:
            return p
    available = ", ".join(p.name for p in plugins) or "(none)"
    raise SystemExit(f"Unknown plugin '{name}'. Available: {available}")


def resolve_profile_dir(profile: str, hermes_root: Path) -> Path:
    if profile == "default":
        if not hermes_root.is_dir():
            raise SystemExit(f"Missing default Hermes root: {hermes_root}")
        return hermes_root
    target = hermes_root / "profiles" / profile
    if not target.is_dir():
        known = ", ".join(discover_profiles(hermes_root).keys()) or "(none)"
        raise SystemExit(f"Unknown profile '{profile}'. Available: {known}")
    return target


def install_plugin(
    plugin: PluginSpec,
    profile_name: str,
    profile_dir: Path,
    *,
    copy: bool = False,
    force: bool = False,
    dry_run: bool = False,
) -> str:
    dest = profile_dir / plugin.target_relpath
    action = "copy" if copy else "link"

    if dest.is_symlink():
        current = dest.resolve(strict=False)
        if not copy and current == plugin.source:
            return f"ok       {profile_name}: {dest} -> {plugin.source}"
        if not dry_run:
            dest.unlink()
    elif dest.exists():
        if not force:
            raise SystemExit(
                f"Refusing to overwrite existing path (pass --force): {dest}"
            )
        if not dry_run:
            if dest.is_dir():
                shutil.rmtree(dest)
            else:
                dest.unlink()

    if dry_run:
        return f"dry-run  {profile_name}: would {action} {dest} <- {plugin.source}"

    dest.parent.mkdir(parents=True, exist_ok=True)
    if copy:
        shutil.copytree(plugin.source, dest)
        return f"copied   {profile_name}: {dest} <- {plugin.source}"
    dest.symlink_to(plugin.source, target_is_directory=True)
    return f"linked   {profile_name}: {dest} -> {plugin.source}"


def uninstall_plugin(
    plugin: PluginSpec,
    profile_name: str,
    profile_dir: Path,
    *,
    dry_run: bool = False,
) -> str:
    dest = profile_dir / plugin.target_relpath
    if not dest.exists() and not dest.is_symlink():
        return f"absent   {profile_name}: {dest}"
    if dry_run:
        return f"dry-run  {profile_name}: would remove {dest}"
    if dest.is_symlink() or dest.is_file():
        dest.unlink()
    else:
        shutil.rmtree(dest)
    return f"removed  {profile_name}: {dest}"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="install_hermes_plugin.py",
        description="Install repo Hermes plugins into one or more Hermes profiles.",
    )
    parser.add_argument(
        "--hermes-root",
        type=Path,
        default=None,
        help="Override Hermes root (default: ~/.hermes or $HERMES_ROOT)",
    )
    parser.add_argument(
        "--plugins-root",
        type=Path,
        default=DEFAULT_PLUGINS_ROOT,
        help=f"Override repo plugins dir (default: {DEFAULT_PLUGINS_ROOT})",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list", help="List available plugins and profiles")

    inst = sub.add_parser("install", help="Install a plugin into profile(s)")
    inst.add_argument("plugin", nargs="?", help="Plugin name (e.g. gin1111)")
    inst.add_argument(
        "-p",
        "--profile",
        action="append",
        dest="profiles",
        default=[],
        help="Target profile name (repeatable; use 'default' for ~/.hermes)",
    )
    inst.add_argument(
        "--all-profiles",
        action="store_true",
        help="Install into every discovered profile",
    )
    inst.add_argument(
        "--copy",
        action="store_true",
        help="Copy files instead of creating a symlink",
    )
    inst.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing non-symlink directory/file",
    )
    inst.add_argument(
        "--dry-run",
        action="store_true",
        help="Show actions without modifying disk",
    )

    uninst = sub.add_parser("uninstall", help="Remove a plugin from profile(s)")
    uninst.add_argument("plugin", nargs="?", help="Plugin name (e.g. gin1111)")
    uninst.add_argument(
        "-p",
        "--profile",
        action="append",
        dest="profiles",
        default=[],
        help="Target profile name (repeatable)",
    )
    uninst.add_argument(
        "--dry-run",
        action="store_true",
        help="Show actions without modifying disk",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    hermes_root = args.hermes_root.expanduser() if args.hermes_root else default_hermes_root()
    plugins = discover_plugins(args.plugins_root)

    if args.command == "list":
        print("Plugins:")
        if not plugins:
            print("  (none)")
        for p in plugins:
            print(f"  - {p.name} ({p.kind}) -> {p.target_relpath}")
        print("\nProfiles:")
        profiles = discover_profiles(hermes_root)
        if not profiles:
            print("  (none)")
        for name, path in profiles.items():
            print(f"  - {name}: {path}")
        return 0

    plugin = resolve_plugin(args.plugin, plugins)

    if args.command == "install":
        if args.all_profiles or "all" in args.profiles:
            targets = list(discover_profiles(hermes_root).items())
        elif args.profiles:
            targets = [(p, resolve_profile_dir(p, hermes_root)) for p in args.profiles]
        else:
            available = list(discover_profiles(hermes_root).keys())
            picked = _prompt_choice("profile", ["all", *available] if available else [])
            if picked == "all":
                targets = list(discover_profiles(hermes_root).items())
            else:
                targets = [(picked, resolve_profile_dir(picked, hermes_root))]

        for name, pdir in targets:
            print(
                install_plugin(
                    plugin,
                    name,
                    pdir,
                    copy=args.copy,
                    force=args.force,
                    dry_run=args.dry_run,
                )
            )
        if plugin.kind == "model-provider" and not args.dry_run:
            first = targets[0][0]
            flag = "" if first == "default" else f" --profile {first}"
            print(f"\nNext: hermes{flag} auth add {plugin.name}")
        return 0

    if args.command == "uninstall":
        if "all" in args.profiles:
            profiles = list(discover_profiles(hermes_root).keys())
        elif args.profiles:
            profiles = args.profiles
        else:
            available = list(discover_profiles(hermes_root).keys())
            picked = _prompt_choice("profile", ["all", *available] if available else [])
            profiles = available if picked == "all" else [picked]
        for name in profiles:
            pdir = resolve_profile_dir(name, hermes_root)
            print(uninstall_plugin(plugin, name, pdir, dry_run=args.dry_run))
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
