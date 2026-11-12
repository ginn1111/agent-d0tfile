#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)
MODE=${1:-install}
THEME_NAME=${TOOL_THEME:-${2:-}}
THEMES_ROOT=${THEMES_ROOT:-"$REPO_ROOT/agent-tool-themes"}
CONFIG_HOME=${TOOL_THEME_CONFIG_HOME:-${XDG_CONFIG_HOME:-"$HOME/.config"}}
STAMP=$(date +%Y%m%d%H%M%S)

usage() {
  cat <<EOF
Usage:
  scripts/install-tool-theme.sh [install|list] [theme_name]

Env overrides:
  TOOL_THEME              Theme dir name under agent-tool-themes/. Optional if passed as arg.
  THEMES_ROOT             Source themes dir. Default: <repo>/agent-tool-themes
  TOOL_THEME_CONFIG_HOME  Config root. Default: \$XDG_CONFIG_HOME or ~/.config

Installs (only files present in theme dir):
  herdr.toml        -> replaces [theme]/[theme.*] blocks in <config>/herdr/config.toml
  yazi-theme.toml   -> symlink <config>/yazi/theme.toml
  starship.toml     -> symlink <config>/starship.toml
  nvim/lualine.lua  -> symlink <config>/nvim/lua/plugins/lualine.lua
  nvim/solarized.lua-> symlink <config>/nvim/lua/plugins/solarized.lua

Behavior:
  - list mode prints planned actions, writes nothing
  - existing targets are moved to <target>.bak-tooltheme-<timestamp> first
  - re-run with same theme is a no-op for symlinks
  - if theme name missing in interactive shell, prompts from detected themes
EOF
}

[[ "$MODE" == "-h" || "$MODE" == "--help" ]] && { usage; exit 0; }
[[ "$MODE" == "list" || "$MODE" == "install" ]] || { usage >&2; exit 1; }

THEMES=()
while IFS= read -r name; do
  [[ -n "$name" ]] && THEMES+=("$name")
done < <(find "$THEMES_ROOT" -mindepth 1 -maxdepth 1 -type d -exec basename {} \; 2>/dev/null | sort)
[[ ${#THEMES[@]} -gt 0 ]] || { printf 'No themes found under: %s\n' "$THEMES_ROOT" >&2; exit 1; }

if [[ -z "$THEME_NAME" ]]; then
  [[ -t 0 ]] || { printf 'Missing theme name. Pass arg, set TOOL_THEME, or run interactively.\n' >&2; exit 1; }
  printf 'Select tool theme:\n' >&2
  i=1
  for name in "${THEMES[@]}"; do printf '  %d) %s\n' "$i" "$name" >&2; ((i += 1)); done
  while true; do
    read -r -p 'Theme number: ' pick
    if [[ "$pick" =~ ^[0-9]+$ ]] && (( pick >= 1 && pick <= ${#THEMES[@]} )); then
      THEME_NAME=${THEMES[$((pick - 1))]}
      break
    fi
    printf 'Enter number 1-%d.\n' "${#THEMES[@]}" >&2
  done
fi

SRC_DIR="$THEMES_ROOT/$THEME_NAME"
[[ -d "$SRC_DIR" ]] || { printf 'Theme not found: %s\n' "$SRC_DIR" >&2; exit 1; }

linked=0 unchanged=0 merged=0

backup() { mv "$1" "$1.bak-tooltheme-$STAMP"; printf 'backup  %s\n' "$1.bak-tooltheme-$STAMP"; }

link_file() {
  local src="$SRC_DIR/$1" dest="$2"
  [[ -f "$src" ]] || return 0
  if [[ "$MODE" == "list" ]]; then printf 'link    %s -> %s\n' "$src" "$dest"; return 0; fi
  if [[ -L "$dest" && "$(readlink "$dest")" == "$src" ]]; then
    printf 'ok      %s\n' "$dest"; ((unchanged += 1)); return 0
  fi
  mkdir -p "$(dirname "$dest")"
  [[ -e "$dest" || -L "$dest" ]] && backup "$dest"
  ln -s "$src" "$dest"
  printf 'linked  %s\n' "$dest"; ((linked += 1))
}

# Herdr config holds keys/session settings too, so swap only [theme] tables in place.
merge_herdr() {
  local src="$SRC_DIR/herdr.toml" dest="$CONFIG_HOME/herdr/config.toml"
  [[ -f "$src" ]] || return 0
  if [[ "$MODE" == "list" ]]; then printf 'merge   %s [theme] <- %s\n' "$dest" "$src"; return 0; fi
  [[ -f "$dest" ]] || { printf 'skip    %s (missing; run herdr once first)\n' "$dest" >&2; return 0; }
  local tmp
  tmp=$(mktemp "${dest}.XXXXXX")
  awk -v frag="$src" '
    /^\[/ { in_theme = ($0 ~ /^\[theme(\.[^]]*)?\][[:space:]]*(#.*)?$/) }
    in_theme && !done { while ((getline line < frag) > 0) print line; print ""; done = 1 }
    !in_theme { print }
    END { if (!done) { print ""; while ((getline line < frag) > 0) print line } }
  ' "$dest" > "$tmp"
  if cmp -s "$tmp" "$dest"; then
    rm "$tmp"; printf 'ok      %s\n' "$dest"; ((unchanged += 1)); return 0
  fi
  cp -p "$dest" "$dest.bak-tooltheme-$STAMP"
  printf 'backup  %s\n' "$dest.bak-tooltheme-$STAMP"
  mv "$tmp" "$dest"
  printf 'merged  %s\n' "$dest"; ((merged += 1))
}

merge_herdr
link_file yazi-theme.toml "$CONFIG_HOME/yazi/theme.toml"
link_file starship.toml "$CONFIG_HOME/starship.toml"
link_file nvim/lualine.lua "$CONFIG_HOME/nvim/lua/plugins/lualine.lua"
link_file nvim/solarized.lua "$CONFIG_HOME/nvim/lua/plugins/solarized.lua"

[[ "$MODE" == "list" ]] && exit 0
printf 'done    theme=%s linked=%d merged=%d unchanged=%d\n' "$THEME_NAME" "$linked" "$merged" "$unchanged"
printf 'note    restart herdr/yazi/nvim and open new shell to apply\n'
