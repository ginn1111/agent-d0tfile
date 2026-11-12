#!/usr/bin/env bash
# Verification entrypoint. Read-only: no Hermes profile state touched.
set -euo pipefail
cd "$(dirname "$0")"

echo "=== Tests ==="
python3 -m unittest discover -s tests

echo "=== Static checks: shell syntax ==="
for f in scripts/*.sh init.sh; do bash -n "$f"; done

echo "=== Static checks: python compile ==="
python3 -m compileall -q scripts hermes-cron tests

echo "=== Static checks: JSON ==="
for f in feature_list.json hermes-cron/*.json; do python3 -m json.tool "$f" >/dev/null; done

echo "=== Makefile parse ==="
make -n help >/dev/null

echo "=== Verification Complete ==="
echo "Next steps: read feature_list.json + progress.md, work ONE feature, re-run ./init.sh before claiming done."
