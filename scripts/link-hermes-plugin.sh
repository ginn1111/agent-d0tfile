#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)
MODE=${1:-link}
PROFILE_NAME=${HERMES_PROFILE_NAME:-${2:-}}
PLUGIN_NAME=${PLUGIN_NAME:-${3:-}}
PLUGIN_ROOT=${PLUGIN_ROOT:-}
HERMES_HOME_DIR=${HERMES_HOME:-"$HOME/.hermes"}
PROFILES_DIR=${HERMES_PROFILES_DIR:-"$HERMES_HOME_DIR/profiles"}
PLUGINS_ROOT=${PLUGINS_ROOT:-"$REPO_ROOT/hermes-plugins"}

usage() {
  cat <<EOF
Usage:
  scripts/link-hermes-plugin.sh [link|list] [profile_name] [plugin_name]

Env overrides:
  HERMES_PROFILE_NAME   Target Hermes profile name. Optional if passed as arg.
  PLUGIN_NAME          Plugin dir name under hermes-plugins/. Optional.
  PLUGIN_ROOT          Source plugin dir. Optional explicit path.
  PLUGINS_ROOT         Source plugins dir. Default: <repo>/hermes-plugins
  HERMES_HOME          Hermes home dir. Default: ~/.hermes
  HERMES_PROFILES_DIR  Hermes profiles dir. Default: \$HERMES_HOME/profiles

Behavior:
  - links plugin dir into ~/.hermes/profiles/<profile_name>/plugins/
  - replaces existing symlink when it points elsewhere
  - refuses to overwrite real files or directories
  - if profile name missing in interactive shell, prompts for it
  - if plugin name missing in interactive shell, prompts from detected plugin list
EOF
}

if [[ ${MODE} == "-h" || ${MODE} == "--help" ]]; then
  usage
  exit 0
fi

if [[ "$MODE" != "list" && "$MODE" != "link" ]]; then
  usage >&2
  exit 1
fi

select_profile_if_needed() {
  [[ -n "$PROFILE_NAME" ]] && return 0
  [[ -t 0 ]] || {
    printf 'Missing profile name. Pass arg, set HERMES_PROFILE_NAME, or run interactively.\n' >&2
    exit 1
  }
  [[ -d "$PROFILES_DIR" ]] || {
    printf 'Missing Hermes profiles dir: %s\n' "$PROFILES_DIR" >&2
    exit 1
  }

  local profiles=()
  while IFS= read -r name; do
    [[ -n "$name" ]] && profiles+=("$name")
  done < <(find "$PROFILES_DIR" -mindepth 1 -maxdepth 1 -type d -exec basename {} \; | sort)

  [[ ${#profiles[@]} -gt 0 ]] || {
    printf 'No Hermes profiles found under: %s\n' "$PROFILES_DIR" >&2
    exit 1
  }

  printf 'Select Hermes profile:\n' >&2
  local i=1
  for name in "${profiles[@]}"; do
    printf '  %d) %s\n' "$i" "$name" >&2
    ((i += 1))
  done

  local pick
  while true; do
    read -r -p 'Profile number: ' pick
    [[ "$pick" =~ ^[0-9]+$ ]] || {
      printf 'Enter number 1-%d.\n' "${#profiles[@]}" >&2
      continue
    }
    if (( pick >= 1 && pick <= ${#profiles[@]} )); then
      PROFILE_NAME=${profiles[$((pick - 1))]}
      return 0
    fi
    printf 'Enter number 1-%d.\n' "${#profiles[@]}" >&2
  done
}

PLUGIN_DIRS=()
while IFS= read -r src; do
  [[ -n "$src" ]] && PLUGIN_DIRS+=("$src")
done < <(
  find "$PLUGINS_ROOT" -mindepth 1 -maxdepth 1 -type d \
    -exec test -f '{}/plugin.yaml' ';' -print | sort
)

if [[ ${#PLUGIN_DIRS[@]} -eq 0 ]]; then
  printf 'No plugins found under: %s\n' "$PLUGINS_ROOT" >&2
  exit 1
fi

select_plugin_if_needed() {
  if [[ -n "$PLUGIN_ROOT" ]]; then
    return 0
  fi

  if [[ -n "$PLUGIN_NAME" ]]; then
    local selected_path="$PLUGINS_ROOT/$PLUGIN_NAME"
    [[ -d "$selected_path" ]] || {
      printf 'Plugin not found: %s\n' "$selected_path" >&2
      exit 1
    }
    [[ -f "$selected_path/plugin.yaml" ]] || {
      printf 'Missing plugin.yaml under: %s\n' "$selected_path" >&2
      exit 1
    }
    PLUGIN_ROOT="$selected_path"
    return 0
  fi

  [[ -t 0 ]] || {
    printf 'Missing plugin selection. Pass arg, set PLUGIN_NAME, set PLUGIN_ROOT, or run interactively.\n' >&2
    exit 1
  }

  printf 'Select plugin:\n' >&2
  local i=1
  local src
  for src in "${PLUGIN_DIRS[@]}"; do
    printf '  %d) %s\n' "$i" "$(basename "$src")" >&2
    ((i += 1))
  done

  local pick
  while true; do
    read -r -p 'Plugin number: ' pick
    [[ "$pick" =~ ^[0-9]+$ ]] || {
      printf 'Enter number 1-%d.\n' "${#PLUGIN_DIRS[@]}" >&2
      continue
    }
    if (( pick >= 1 && pick <= ${#PLUGIN_DIRS[@]} )); then
      PLUGIN_ROOT=${PLUGIN_DIRS[$((pick - 1))]}
      PLUGIN_NAME=$(basename "$PLUGIN_ROOT")
      return 0
    fi
    printf 'Enter number 1-%d.\n' "${#PLUGIN_DIRS[@]}" >&2
  done
}

select_profile_if_needed
select_plugin_if_needed

if [[ -z "$PLUGIN_NAME" ]]; then
  PLUGIN_NAME=$(basename "$PLUGIN_ROOT")
fi

if [[ ! -d "$PLUGIN_ROOT" ]]; then
  printf 'Missing plugin root: %s\n' "$PLUGIN_ROOT" >&2
  exit 1
fi

if [[ ! -f "$PLUGIN_ROOT/plugin.yaml" ]]; then
  printf 'Missing plugin.yaml under: %s\n' "$PLUGIN_ROOT" >&2
  exit 1
fi

PROFILE_DIR="$PROFILES_DIR/$PROFILE_NAME"
TARGET_DIR="$PROFILE_DIR/plugins"
DEST="$TARGET_DIR/$PLUGIN_NAME"

if [[ ! -d "$PROFILE_DIR" ]]; then
  printf 'Missing Hermes profile: %s\n' "$PROFILE_DIR" >&2
  exit 1
fi

if [[ "$MODE" == "list" ]]; then
  printf '%s -> %s\n' "$PLUGIN_ROOT" "$DEST"
  exit 0
fi

mkdir -p "$TARGET_DIR"

if [[ -L "$DEST" ]]; then
  current=$(readlink "$DEST")
  if [[ "$current" == "$PLUGIN_ROOT" ]]; then
    printf 'ok      %s\n' "$PLUGIN_NAME"
    printf 'done    linked=0 unchanged=1 profile=%s target=%s\n' "$PROFILE_NAME" "$DEST"
    exit 0
  fi
  rm "$DEST"
elif [[ -e "$DEST" ]]; then
  printf 'refuse  %s (exists and is not symlink)\n' "$PLUGIN_NAME" >&2
  exit 1
fi

ln -s "$PLUGIN_ROOT" "$DEST"
printf 'linked  %s\n' "$PLUGIN_NAME"
printf 'done    linked=1 unchanged=0 profile=%s target=%s\n' "$PROFILE_NAME" "$DEST"
