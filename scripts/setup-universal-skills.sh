#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)
SKILLS_ROOT=${SKILLS_ROOT:-"$REPO_ROOT/skills"}
TARGET_DIR=${AGENTS_SKILLS_DIR:-"${HOME}/.agents/skills"}
MODE=${1:-link}

usage() {
  cat <<'EOF'
Usage:
  scripts/setup-universal-skills.sh [link|list]

Env overrides:
  AGENTS_SKILLS_DIR   Target universal skills dir. Default: $HOME/.agents/skills
  SKILLS_ROOT         Source skills dir. Default: <repo>/skills

Behavior:
  - links every directory under SKILLS_ROOT that contains SKILL.md
  - preserves category paths, example: superpowers/using-superpowers
  - replaces existing symlink when it points elsewhere
  - refuses to overwrite real files or directories
EOF
}

if [[ ${MODE} == "-h" || ${MODE} == "--help" ]]; then
  usage
  exit 0
fi

if [[ ! -d "$SKILLS_ROOT" ]]; then
  printf 'Missing skills root: %s\n' "$SKILLS_ROOT" >&2
  exit 1
fi

mapfile -t SKILL_DIRS < <(
  find "$SKILLS_ROOT" -type f -name SKILL.md -printf '%h\n' | sort
)

if [[ ${#SKILL_DIRS[@]} -eq 0 ]]; then
  printf 'No skills found under: %s\n' "$SKILLS_ROOT" >&2
  exit 1
fi

if [[ "$MODE" == "list" ]]; then
  for src in "${SKILL_DIRS[@]}"; do
    rel=${src#"$SKILLS_ROOT"/}
    printf '%s -> %s/%s\n' "$src" "$TARGET_DIR" "$rel"
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

for src in "${SKILL_DIRS[@]}"; do
  rel=${src#"$SKILLS_ROOT"/}
  dest="$TARGET_DIR/$rel"
  dest_parent=$(dirname "$dest")
  mkdir -p "$dest_parent"

  if [[ -L "$dest" ]]; then
    current=$(readlink "$dest")
    if [[ "$current" == "$src" ]]; then
      printf 'ok      %s\n' "$rel"
      skipped=$((skipped + 1))
      continue
    fi
    rm "$dest"
  elif [[ -e "$dest" ]]; then
    printf 'refuse  %s (exists and is not symlink)\n' "$rel" >&2
    exit 1
  fi

  ln -s "$src" "$dest"
  printf 'linked  %s\n' "$rel"
  linked=$((linked + 1))
done

printf 'done    linked=%d unchanged=%d target=%s\n' "$linked" "$skipped" "$TARGET_DIR"
