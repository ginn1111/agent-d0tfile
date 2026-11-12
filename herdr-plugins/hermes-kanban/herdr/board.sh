#!/usr/bin/env bash
set -euo pipefail

plugin_root="${HERDR_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
binary="$plugin_root/target/release/hermes-kanban-tui"
if [[ ! -x "$binary" ]]; then
  printf 'Build Hermes Kanban first:\n  cargo build --release --locked --manifest-path %q/Cargo.toml\n' "$plugin_root" >&2
  status=1
elif "$binary" "$@"; then
  exit 0
else
  status=$?
fi
if [[ -t 0 ]]; then
  printf '\nPress Enter to close.\n'
  read -r _ || true
fi
exit "$status"
