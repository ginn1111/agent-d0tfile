# english-tutor plugin

Capture user prompts into daily JSONL files for later English tutor review.

## Link into profile

```bash
make letp HERMES_PROFILE_NAME=gintary
# or
HERMES_PROFILE_NAME=gintary scripts/link-hermes-plugin.sh link
```

Resulting symlink:

```text
~/.hermes/profiles/<profile>/plugins/english-tutor -> <repo>/hermes-plugins/english-tutor
```

## Files

- `__init__.py` — hook registration and prompt capture
- `plugin.yaml` — Hermes plugin metadata
