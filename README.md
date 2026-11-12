# agents-dotfile

**Hermes agent profile + skills + plugins monorepo.**  
Batteries-included agent stack for AI-assisted development.

---

## What This Is

A portable, version-controlled Hermes profile containing:

- **Skills** — Reusable procedures for recurring dev tasks (planning, TDD, debugging, code review, skill authoring)
- **Plugins** — Hermes plugins extending agent capabilities
- **Profile config** — Hermes skins + helper Make targets
- **Cron templates** — JSON cron job templates under `hermes-cron/`

---

## Repository Layout

```
agents-dotfile/
├── AGENTS.md                  # Agent startup/done/session workflow
├── init.sh                    # Read-only verification entrypoint
├── feature_list.json          # Feature tracker
├── progress.md                # Session progress log
├── session-handoff.md         # Restartable handoff
├── hermes/                    # Hermes skins + cf-tunnel Make target
├── hermes-cron/               # Cron job JSON templates
├── hermes-plugins/            # Hermes plugins (symlinked into profile at runtime)
│   ├── english-tutor/
│   └── validated-mistery-loop/
├── skills/                    # Skills (procedural memory) — symlinked into profile
│   ├── mattcopock/            # Matt Pocock skills (tdd, grilling, to-spec, wayfinder, ...)
│   └── superpowers/           # Superpowers skills (brainstorming, executing-plans, ...)
├── scripts/                   # Helper scripts (link plugins/skills, add cron)
├── tests/                     # unittest suite (run via init.sh)
└── 9router/                   # (gitignored) 9router operational data
```

---

## Skills Catalog

| Skill | Category | Description |
|-------|----------|-------------|
| `mattcopock:ask-matt` | **Router** | Pick which skill/flow fits the situation |
| `mattcopock:code-review` | **Code Quality** | Review changes since a fixed point |
| `mattcopock:codebase-design` | **Design** | Vocabulary for designing deep modules |
| `mattcopock:diagnosing-bugs` | **Debugging** | Diagnosis loop for hard bugs / perf regressions |
| `mattcopock:domain-modeling` | **Design** | Build and sharpen a domain model |
| `mattcopock:grill-me` / `grill-with-docs` / `grilling` | **Planning** | Relentless interview to sharpen a plan |
| `mattcopock:handoff` | **Session** | Compact conversation into a handoff doc |
| `mattcopock:prototype` | **Exploration** | Throwaway prototype for a design question |
| `mattcopock:research` | **Research** | Investigate against primary sources |
| `mattcopock:resolving-merge-conflicts` | **Git** | Resolve in-progress merge conflicts |
| `mattcopock:tdd` | **Code Quality** | Test-driven development loop |
| `mattcopock:teach` | **Learning** | Teach a concept within the codebase |
| `mattcopock:to-questionnaire` | **Planning** | Turn open decision into questionnaire |
| `mattcopock:to-spec` | **Planning** | Turn conversation into a spec |
| `mattcopock:triage` | **Issues** | Move issues/PRs through a state machine |
| `mattcopock:wayfinder` | **Planning** | Plan multi-session work |
| `mattcopock:wizard` | **DevOps / Setup** | Generate interactive bash wizard |
| `brainstorming` | **Superpowers** | Structured brainstorming before creative work |
| `dispatching-parallel-agents` | **Superpowers** | Parallel subagents for independent tasks |
| `executing-plans` | **Superpowers** | Execute written plans |
| `finishing-a-development-branch` | **Superpowers** | Complete branch: tests pass, review done, merge ready |
| `receiving-code-review` | **Superpowers** | Process code review feedback |
| `using-git-worktrees` | **Superpowers** | Isolated feature work via git worktrees |
| `using-superpowers` | **Superpowers** | Meta-skill: how to use superpowers |
| `verification-before-completion` | **Superpowers** | Verify before claiming done |
| `writing-skills` | **Superpowers** | Author new skills |

---

## Plugins

| Plugin | Description |
|--------|-------------|
| `english-tutor` | English tutor plugin |
| `validated-mistery-loop` | File-based VML checker/reviewer/starter/validator/stress coach |

---

## Quick Start

```bash
# Clone into Hermes profile location
git clone <this-repo> ~/.hermes/profiles/gintary

# Or symlink into existing profile
ln -s /path/to/agents-dotfile/hermes ~/.hermes/profiles/gintary/hermes
ln -s /path/to/agents-dotfile/hermes-plugins ~/.hermes/profiles/gintary/hermes-plugins
ln -s /path/to/agents-dotfile/skills ~/.hermes/profiles/gintary/skills

# Reload Hermes profile
hermes profile reload gintary
```

### Link Skills into Universal Agent Folder

```bash
make universal-skills
```

Default target: `~/.agents/skills`

Override target dir:

```bash
make universal-skills AGENTS_SKILLS_DIR=~/.copilot/skills
```

Preview links without writing:

```bash
make us-dry-run
# or
make universal-skills-dry-run
```

Cindy Black & Ruby theme (`scripts/install_theme_cindy.py`):

```bash
make theme-cindy                 # link cindy Black & Ruby theme into ~/.config + cindy profile (backs up originals)
make theme-cindy-dry-run         # preview theme links/edits without writing
make theme-cindy-restore         # restore pre-cindy originals, remove theme links
make theme-cindy-restore-dry-run # preview restore without writing
```

Raw script still available:

```bash
scripts/setup-universal-skills.sh
```

### Create Cron Jobs via Hermes CLI

Use Hermes CLI for user-facing cron creation.

```bash
hermes --profile gintary cron create "every 2h" "Check server status"
hermes --profile gintary cron create "every 1h" "Summarize new feed items" --skill blogwatcher
hermes --profile gintary cron create "every 1h" "Use both skills and combine the result" \
  --skill blogwatcher \
  --skill maps \
  --name "Skill combo"
```

Use explicit `--profile <profile>` and keep examples aligned with real available profiles.

If you keep cron jobs as JSON templates under `hermes-cron/`, use helper script to convert supported JSON fields into equivalent `hermes cron create ...` commands.

Interactive mode asks for profile first, then cron config name from JSON filenames, with `all` option:

```bash
scripts/add-hermes-cron.sh
```

If JSON `script` points to repo/local file and file is not already under Hermes scripts dir, helper script copies basename into `$HERMES_HOME/profiles/<profile>/scripts/` and keeps cron config on basename-only `--script <name>`.

Non-interactive examples:

```bash
HERMES_PROFILE_NAME=gintary CRON_SELECTION=english-tutor-review scripts/add-hermes-cron.sh list
HERMES_PROFILE_NAME=gintary CRON_SELECTION=all scripts/add-hermes-cron.sh add
```

### Link Plugin into Profile

Use helper script when plugin should be symlinked into one Hermes profile. Behavior mirrors cron helper shape: if profile or plugin not passed, script shows picker list and lets user choose.

```bash
make letp-dry-run HERMES_PROFILE_NAME=gintary PLUGIN_NAME=english-tutor
make letp HERMES_PROFILE_NAME=gintary PLUGIN_NAME=english-tutor
make letp-dry-run HERMES_PROFILE_NAME=gintary PLUGIN_NAME=validated-mistery-loop
make letp HERMES_PROFILE_NAME=gintary PLUGIN_NAME=validated-mistery-loop
make lvmlp-dry-run HERMES_PROFILE_NAME=gintary
make lvmlp HERMES_PROFILE_NAME=gintary
```

Interactive form:

```bash
make letp-dry-run
make letp
```

Direct script form:

```bash
HERMES_PROFILE_NAME=gintary PLUGIN_NAME=english-tutor scripts/link-hermes-plugin.sh list
HERMES_PROFILE_NAME=gintary PLUGIN_NAME=english-tutor scripts/link-hermes-plugin.sh link
HERMES_PROFILE_NAME=gintary PLUGIN_NAME=validated-mistery-loop scripts/link-hermes-plugin.sh list
HERMES_PROFILE_NAME=gintary PLUGIN_NAME=validated-mistery-loop scripts/link-hermes-plugin.sh link
scripts/link-hermes-plugin.sh list
scripts/link-hermes-plugin.sh link
```

Resulting symlink:

```text
~/.hermes/profiles/<profile>/plugins/<plugin-name> -> <repo>/hermes-plugins/<plugin-name>
```

### Load a Skill

```bash
hermes skill load mattcopock:tdd
hermes skill load mattcopock:code-review
```

---

## Skills vs Plugins vs Profile Config

| Layer | Purpose | Location |
|-------|---------|----------|
| **Profile config** | Skins, tunnel helper | `hermes/skins/*.yaml`, `hermes/Makefile` |
| **Plugins** | Extend agent runtime (Python/JS) | `hermes-plugins/*` → symlinked to `~/.hermes/profiles/gintary/plugins/` |
| **Skills** | Procedural memory (markdown + scripts) | `skills/*` → symlinked to `~/.hermes/profiles/gintary/skills/` |

---

## Adding a Skill

```bash
# Create skill scaffold
hermes skill create my-skill --category devops

# Edit the skill
# ~/.hermes/profiles/gintary/skills/my-skill/SKILL.md

# Test it
hermes skill load my-skill
hermes skill run my-skill

# Commit to this repo (if under skills/)
git add skills/my-skill
git commit -m "skill: add my-skill"
```

---

## Adding a Plugin

```bash
mkdir -p hermes-plugins/my-plugin
# Create plugin.yaml + __init__.py
# Symlink into profile
HERMES_PROFILE_NAME=gintary PLUGIN_NAME=my-plugin scripts/link-hermes-plugin.sh link
# Example: VML plugin
HERMES_PROFILE_NAME=gintary PLUGIN_NAME=validated-mistery-loop scripts/link-hermes-plugin.sh link
# Or use picker
scripts/link-hermes-plugin.sh link
```

For make shortcut:

```bash
make letp HERMES_PROFILE_NAME=gintary PLUGIN_NAME=my-plugin
```

---

## Profile Structure (Hermes)

```
~/.hermes/profiles/gintary/
├── profile.yaml       # Profile identity, model, provider
├── config.yaml        # Toolsets, permissions, tool config
├── dist.yaml          # Distro overrides (pinned versions)
├── plugins/           # Symlinks to hermes-plugins/*
├── skills/            # Symlinks to skills/*
├── scripts/           # Profile-local scripts
├── cron/              # Cron jobs (local-only delivery)
├── memories/          # Persistent memory (injected each turn)
└── audio_cache/       # TTS cache
```

---

## Git Hygiene

- **Track**: `hermes/skins/**`, `hermes-cron/**`, `hermes-plugins/**`, `skills/**`, `scripts/**`, `tests/**`, harness files, `README.md`
- **Ignore**: `.git/objects` (git objects), `__pycache__`, `node_modules`, `.env`, `.make/` (generated caches), `9router/data`, `.hermes/profiles/gintary/{cron,memories,audio_cache,scripts}`, `*.pyc`, `.DS_Store`
- **Never commit**: secrets, API keys, local DBs, cron output, memory DBs

```bash
# Typical commit
git add skills/mattcopock/tdd
git commit -m "skill: update tdd skill"
```

---

## Philosophy

- **Portable** — Clone to any machine, symlink, reload profile, works.
- **Versioned** — Skills/plugins versioned with profile config. Reproducible agent.
- **Composable** — Load only skills you need per session. No bloat.
- **Procedural memory** — Skills = repeatable procedures, not prompts.
- **Extensible** — Plugins for runtime extensions; skills for procedural knowledge.
- **Local-first** — Cron, memories, audio cache stay local (gitignored).

---

## Related Projects

- **Hermes** — The agent runtime: `github.com/.../hermes`
- **9router** — Local router for multi-model routing (gitignored here)
- **aioz-wallet-mobile** — Main product repo (GitLab internal)

---

## License

Internal / proprietary. Not for public distribution.