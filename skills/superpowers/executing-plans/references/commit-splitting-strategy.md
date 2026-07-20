# Commit-Splitting Strategy

When user asks "commit these changes, split into small commits":

## Workflow

1. **Analyze the diff** — `git diff --stat` to see all changed/new/deleted files.
2. **Group by logical change** — each group is a single coherent concern:
   - Cleanup/refactor that touches only one domain
   - New component + its supporting files (registry, config)
   - Feature integration (mounting, tooltips, wiring)
   - Independent bugfix
   - Generated file regeneration
   - Unrelated config changes (dev IPs, etc.)
3. **Order groups** — prep commits first (generated code, bugfixes), then feature commits.
4. **Present the plan** — table with:
   - Commit message
   - Files included
   - Why they belong together
5. **Wait for confirmation** before staging/committing.

## Grouping Heuristics

| Signal | Likely group |
|--------|-------------|
| New `.ts`/`.tsx` file + related registry/store changes | Single coherent feature |
| Deleted file + replacement file | Refactor (same concern) |
| Hook change + store change + config change | All part of same feature wiring |
| Standalone `.html` doc | Separate commit (docs) |
| `package.json` + lockfile | chore: deps |
| `next.config.ts` alone | chore: config |
| Unrelated bugfix in unrelated file | Separate fix commit |
| Generated API files | chore: regenerate |

## Edge Cases

- **Pre-commit hook fails on pre-existing tsc errors** — use `--no-verify` and note the pre-existing errors to the user. Don't try to fix unrelated failures in the same session unless user asks.
- **Lint-staged reverts commits when hook fails** — all staged changes are lost. Restore from unstaged changes and re-run with `--no-verify`.
- **User says "cleanup dead code first"** — treat as a separate group, commit it as prep before feature work.
