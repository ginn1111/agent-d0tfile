# Session Progress Log

## Current State

**Last Updated:** 2026-11-12
**Active Feature:** none (feat-003 done)

## Status

### What's Done
- [x] feat-001 Agent harness.
- [x] feat-002 Validated-mistery-loop plugin.
- [x] feat-003 Reconcile working tree: tracked cleanup committed.

### What's In Progress
- [ ] none

### What's Next
1. feat-004 Rotate leaked Hermes API tokens (was in `hermes/.make/hermes-profiles.mk`, pushed).
2. feat-005 Triage untracked files.
3. feat-006 Restore or drop `RULES.md` reference in `AGENTS.md`.

## Blockers / Risks
- [ ] Tokens in git history on origin/main; untracking does not remove them. Rotate.

## Decisions Made
- **Removed orphaned Make targets**: `hermes-profiles-config` + `hermes-health*` (needed deleted `hermes_profile_map.py`), `lmp*` + `scripts/link-model-providers.sh` (needed deleted `hermes-plugins/model-providers`).
- **`hermes/Makefile` uses `-include .env`**: `make help` no longer fails without `.env`.
- **`init.sh` drops `-t .`**: `tests/` has no `__init__.py`; discovery failed with "Start directory is not importable".
- **`.make/` gitignored**: generated cache holds tokens.

## Files Modified This Session
- `Makefile`, `hermes/Makefile`, `init.sh`, `.gitignore`, `README.md`
- Removed: `scripts/link-model-providers.sh`, untracked `hermes/.make/hermes-profiles.mk`
- Cleanup (by Gin): plugins, `paperclip/`, `hermes/scripts/hermes_profile_map.py`, skills

## Evidence of Completion
- [x] `./init.sh` exit 0, 12 tests OK
- [x] `make help`, `make -C hermes help`, `make us-dry-run`, `make lvmlp-dry-run` exit 0

## Notes for Next Session
Run `./init.sh` first. Under a profile session, set `HERMES_HOME=~/.hermes` for link dry-runs.
