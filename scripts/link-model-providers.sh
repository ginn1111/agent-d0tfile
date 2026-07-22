#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)
PROVIDERS_ROOT=${PROVIDERS_ROOT:-"$REPO_ROOT/hermes-plugins/model-providers"}
MODE=${1:-link}
PROFILE_NAME=${HERMES_PROFILE_NAME:-${2:-}}

usage() {
  cat <<'EOF'
Usage:
  scripts/link-model-providers.sh [link|list] [profile_name]

Env overrides:
  HERMES_PROFILE_NAME   Target Hermes profile name. Optional if passed as arg.
  PROVIDERS_ROOT        Source model-provider plugins dir.

Behavior:
  - links every directory under PROVIDERS_ROOT that contains plugin.yaml
  - target dir: ~/.hermes/profiles/<profile_name>/plugins/
  - replaces existing symlink when it points elsewhere
  - refuses to overwrite real files or directories
  - if profile name missing in interactive shell, prompts for it
EOF
}

if [[ ${MODE} == "-h" || ${MODE} == "--help" ]]; then
  usage
  exit 0
fi

if [[ ! -d "$PROVIDERS_ROOT" ]]; then
  printf 'Missing providers root: %s\n' "$PROVIDERS_ROOT" >&2
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

TARGET_DIR="${HOME}/.hermes/profiles/${PROFILE_NAME}/plugins/model-providers"
PROFILE_DIR=$(dirname "$TARGET_DIR")

if [[ ! -d "$PROFILE_DIR" ]]; then
  printf 'Missing Hermes profile: %s\n' "$PROFILE_DIR" >&2
  exit 1
fi

PROVIDER_DIRS=()
while IFS= read -r src; do
  PROVIDER_DIRS+=("$src")
done < <(
  find "$PROVIDERS_ROOT" -mindepth 1 -maxdepth 1 -type d \
    -exec test -f '{}/plugin.yaml' ';' -print | sort
)

if [[ ${#PROVIDER_DIRS[@]} -eq 0 ]]; then
  printf 'No model-provider plugins found under: %s\n' "$PROVIDERS_ROOT" >&2
  exit 1
fi

if [[ "$MODE" == "list" ]]; then
  for src in "${PROVIDER_DIRS[@]}"; do
    name=$(basename "$src")
    printf '%s -> %s/%s\n' "$src" "$TARGET_DIR" "$name"
  done
  exit 0
fi

if [[ "$MODE" != "link" ]]; then
  usage >&2
  exit 1
fi

mkdir -p "$TARGET_DIR"

linked=0
skipped=0

for src in "${PROVIDER_DIRS[@]}"; do
  name=$(basename "$src")
  dest="$TARGET_DIR/$name"

  if [[ -L "$dest" ]]; then
    current=$(readlink "$dest")
    if [[ "$current" == "$src" ]]; then
      printf 'ok      %s\n' "$name"
      skipped=$((skipped + 1))
      continue
    fi
    rm "$dest"
  elif [[ -e "$dest" ]]; then
    printf 'refuse  %s (exists and is not symlink)\n' "$name" >&2
    exit 1
  fi

  ln -s "$src" "$dest"
  printf 'linked  %s\n' "$name"
  linked=$((linked + 1))
done

printf 'done    linked=%d unchanged=%d profile=%s target=%s\n' "$linked" "$skipped" "$PROFILE_NAME" "$TARGET_DIR"
