# See `RULES.md`

Project rules moved to `RULES.md`.
Read and follow that file for repo-specific guidance.

## Startup Workflow
Before writing code:
1. Read `RULES.md`, `progress.md`, `feature_list.json`, `session-handoff.md`.
2. Run `./init.sh`. Fix red baseline before new work.
3. Pick ONE feature (`status` not `done`, dependencies done). Set it `in-progress`.

## Working Rules
- One feature at a time. Stay in scope: unrelated fixes go into `feature_list.json` as new `not-started` entries, not into current diff.
- Mutating Hermes profile state: dry-run first, isolated `HERMES_HOME` (see `RULES.md`).

## Verification Commands
- `./init.sh` — tests (`python3 -m unittest`), shell syntax, python compile, JSON, Makefile parse. Read-only.
- Touched Make target: also run its `*-dry-run` target.

## Definition of Done
Feature is done only when:
- `./init.sh` passes.
- Targeted check for touched files ran (see `RULES.md` Verification).
- Evidence (command + result) written to `feature_list.json` `evidence` and `progress.md`.
- Docs updated per `RULES.md` "When adding things".

## End of Session
Before ending:
1. Update `progress.md` (Current State, Last Updated, What's Next).
2. Update feature `status` in `feature_list.json`.
3. Fill `session-handoff.md` so next session is restartable from clean checkout.
