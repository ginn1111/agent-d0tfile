# agents-dotfile rules

## Scope
- This repo manages shared Hermes setup artifacts: skills, plugins, helper scripts, and cron job templates.
- Treat repo as setup/tooling workspace, not product app workspace.
- Keep changes narrow. Prefer shortest diff.

## Key paths
- `skills/` — versioned reusable skills
- `hermes-plugins/` — Hermes plugins and model-provider plugins
- `herdr-plugins/` — native Herdr terminal plugins; Kanban TUI uses Cargo and a stdlib Python reader
- `hermes-cron/` — cron job JSON templates
- `scripts/` — setup and linking scripts
- `Makefile` — thin wrappers around setup scripts
- `README.md` — user-facing setup and usage docs

## Working rules
- Read relevant files before editing. Match existing shell/Python/doc style.
- Edit files with smallest change that solves task.
- Do not touch secrets, profile runtime state, or generated cache files.
- Do not assume Hermes profile paths; use existing script parameters and env vars.
- Preserve existing user data when editing setup scripts. For cron sync, merge by stable key instead of overwriting runtime fields.

## Script conventions
- Shell: use `bash`, `set -euo pipefail`, quote paths, fail with clear stderr.
- Python snippets: use stdlib only unless repo already depends on something else.
- Prefer idempotent behavior. Re-running setup should update/link, not duplicate.
- Dry-run/list mode first when operation mutates external Hermes profile state.

## Verification
- Herdr Kanban changes: run `cargo test --locked --manifest-path herdr-plugins/hermes-kanban/Cargo.toml`, `cargo clippy --locked --manifest-path herdr-plugins/hermes-kanban/Cargo.toml --all-targets -- -D warnings`, and `bash -n herdr-plugins/hermes-kanban/herdr/{open,board}.sh` in addition to `./init.sh`. Rebuild with `make hkb` after Rust or reader changes; the reader is embedded in the binary. `make hkb-dry-run` previews the build.
- Keep Kanban viewer read-only: no Hermes CLI list calls (they recompute readiness), schema migrations, or board-pointer writes. Use SQLite URI `mode=ro` with live WAL visibility; fixture writes belong only in temporary roots. Persist UI selection only in Herdr plugin state.
- For docs-only changes, verify changed paths read clean and examples still match repo files.
- Theme colour changes (any Target in `themes/cindy/REGISTRY.md`, incl. `~/tools/d0t_file`): use only `black-ruby.palette` Colours, list new Targets in REGISTRY.md, run `python3 -m unittest tests.test_theme_cindy_palette`.
- For script or Makefile changes, run relevant command in dry-run mode when possible.
- For every new `Makefile` target, add and run at least one verification command that proves target behavior.
- If new `Makefile` target touches Hermes profile state, test with isolated Hermes home so real config stays clean.
- Use temporary home pattern like:
  ```bash
  export HERMES_HOME=/tmp/hermes-test
  rm -rf "$HERMES_HOME"
  mkdir -p "$HERMES_HOME"
  ```
- Put any test-only plugins, config, or profile files under `$HERMES_HOME`, not under real `~/.hermes`.
- Prefer command flow that sets `HERMES_HOME`, creates minimal fixture, runs target or Hermes command, then deletes temp dir.
- Example for provider/plugin checks:
  ```bash
  export HERMES_HOME=/tmp/hermes-plugin-test
  rm -rf "$HERMES_HOME"
  mkdir -p "$HERMES_HOME/plugins/model-providers/my-provider"
  cat > "$HERMES_HOME/plugins/model-providers/my-provider/__init__.py" <<'EOF'
  from providers import register_provider
  from providers.base import ProviderProfile

  register_provider(ProviderProfile(
      name="my-provider",
      env_vars=("MY_API_KEY",),
      base_url="https://api.my-provider.example.com/v1",
      auth_type="api_key",
  ))
  EOF
  export MY_API_KEY=your-test-key
  hermes -z "hello" --provider my-provider -m some-model
  rm -rf "$HERMES_HOME"
  ```
- Before finishing, run targeted checks for touched files and report exact command/output.

## Git hygiene
- Never commit credentials, `.env`, profile memories, cron runtime output, or caches.
- Ignore generated files like `__pycache__/` and OS junk.
- Do not rewrite unrelated files or reformat repo wholesale.

## When adding things
- New script: add usage/help text and wire through `Makefile` if end-user facing.
- New cron template: prefer Hermes CLI creation flow (`hermes cron create ...`) over direct JSON sync scripts when adding user-facing cron setup.
- When documenting or testing cron creation, use explicit profile selection with `--profile <profile>` and keep examples aligned with real available profiles.
- Keep cron jobs self-contained and safe for repeated sync or repeated execution.
- New plugin or skill: include minimal README or inline docs if behavior is non-obvious.
- New Make target: offer short alias and dry-run target when mutation exists.
- After adding new feature, check existing docs that mention affected behavior, commands, paths, or workflows.
- Update `RULES.md` when feature changes repo working rules, verification flow, setup flow, or maintenance expectations.
- Update `README.md` when feature changes user-facing setup, usage, commands, examples, repo layout, or supported capabilities.
- Do not leave feature behavior documented in code only. If feature matters to future work or users, document it in `RULES.md` and/or `README.md` in same change.
