#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)
PLUGIN_NAME=${PLUGIN_NAME:-english-tutor}
PLUGIN_ROOT=${PLUGIN_ROOT:-"$REPO_ROOT/hermes-plugins/$PLUGIN_NAME"}
MODE=${1:-link}
PROFILE_NAME=${HERMES_PROFILE_NAME:-${2:-}}
HERMES_HOME_DIR=${HERMES_HOME:-"$HOME/.hermes"}
PROFILES_DIR=${HERMES_PROFILES_DIR:-"$HERMES_HOME_DIR/profiles"}

usage() {
  cat <<EOF
Usage:
  scripts/link-hermes-plugin.sh [link|list] [profile_name]

Env overrides:
  HERMES_PROFILE_NAME   Target Hermes profile name. Optional if passed as arg.
  PLUGIN_NAME          Plugin dir name under hermes-plugins/. Default: english-tutor
  PLUGIN_ROOT          Source plugin dir. Default: <repo>/hermes-plugins/<plugin_name>
  HERMES_HOME          Hermes home dir. Default: ~/.hermes
  HERMES_PROFILES_DIR  Hermes profiles dir. Default: \$HERMES_HOME/profiles

Behavior:
  - links plugin dir into ~/.hermes/profiles/<profile_name>/plugins/
  - replaces existing symlink when it points elsewhere
  - refuses to overwrite real files or directories
  - if profile name missing in interactive shell, prompts for it
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

if [[ ! -d "$PLUGIN_ROOT" ]]; then
  printf 'Missing plugin root: %s\n' "$PLUGIN_ROOT" >&2
  exit 1
fi

if [[ ! -f "$PLUGIN_ROOT/plugin.yaml" ]]; then
  printf 'Missing plugin.yaml under: %s\n' "$PLUGIN_ROOT" >&2
  exit 1
fi

if [[ -z "$PROFILE_NAME" ]]; then
  if [[ -t 0 ]]; then
    read -r -p 'Hermes profile name: ' PROFILE_NAME
  fi
fi

if [[ -z "$PROFILE_NAME" ]]; then
  printf 'Missing profile name. Pass arg or set HERMES_PROFILE_NAME.\n' >&2
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
