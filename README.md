# agents-dotfile

**Hermes agent profile + skills + plugins monorepo.**  
Batteries-included agent stack for AI-assisted development.

---

## What This Is

A portable, version-controlled Hermes profile containing:

- **Skills** — Reusable, versioned procedures for recurring dev tasks (code review, codebase understanding, debugging, codegen, task planning, code review, debugging, skill authoring, etc.)
- **Plugins** — Hermes plugins extending agent capabilities (agent state persistence, etc.)
- **Profile config** — Portable `profile.yaml`, `config.yaml`, `dist.yaml` + symlinked plugins/skills
- **Rituals** — Daily focus rituals (morning focus, end-of-day shutdown)
- **Project docs** — Ephemeral project docs (hiring, issues, product) gitignored

---

## Repository Layout

```
agents-dotfile/
├── .gitignore                 # gitignore (secrets, 9router data, OS files)
├── hermes/                    # Hermes profile config (profile.yaml, config.yaml, dist.yaml)
├── hermes-plugins/            # Hermes plugins (symlinked into profile at runtime)
│   └── herdr-agent-state/     # Agent state persistence plugin
├── skills/                    # Skills (procedural memory) — symlinked into profile
│   ├── ritual/                # Daily focus ritual (morning focus, EOD shutdown)
│   ├── understand-anything/   # Codebase understanding engine (graph-based)
│   │   ├── understand/        # Core: scan, fingerprint, graph, tour
│   │   ├── understand-chat/   # Chat over codebase graph
      │   ├── understand-dashboard/ # Web dashboard for graph viz
      │   ├── understand-diff/      # Git diff analysis via graph
      │   ├── understand-domain/    # Domain knowledge extraction
      │   ├── understand-explain/   # Deep-dive explanations
      │   ├── understand-figma/     # Figma file analysis
      │   ├── understand-knowledge/ # Knowledge graph merge/parse
      │   └── understand-onboard/   # Onboarding guide generation
│   ├── mattcopock/            # Third-party skills (wizard, prototype, code-reviewer, ...)
│   └── ...                    # (more skills symlinked from ~/.hermes/profiles/gintary/skills)
├── 9router/                   # (gitignored) 9router operational data
├── paperclip/                 # Scratchpad / scratchpad tooling
└── scripts/                   # Helper scripts (gitignored)
```

---

## Skills Catalog (Trendy AI Agent Toolkit)

| Skill | Category | Description |
|-------|----------|-------------|
| `ritual` | **Rituals** | Daily focus ritual (morning focus, EOD shutdown) |
| `understand-anything:understand` | **Codebase Understanding** | Graph-based codebase scanner: fingerprints, import graph, framework detection, guided tours |
| `understand-anything:understand-chat` | **Codebase Understanding** | Chat over codebase knowledge graph |
| `understand-anything:understand-dashboard` | **Codebase Understanding** | Interactive web dashboard for graph visualization |
| `understand-anything:understand-diff` | **Codebase Understanding** | Analyze git diffs via knowledge graph |
| `understand-anything:understand-domain` | **Codebase Understanding** | Extract domain knowledge from codebase |
| `understand-anything:understand-explain` | **Codebase Understanding** | Deep-dive explanations of code regions |
| `understand-anything:understand-figma` | **Codebase Understanding** | Analyze Figma files via REST API |
| `understand-anything:understand-knowledge` | **Codebase Understanding** | Merge/parse Karpathy-pattern knowledge bases |
| `understand-anything:understand-onboard` | **Codebase Understanding** | Generate onboarding guides from graph |
| `mattcopock:wizard` | **DevOps / Setup** | Project setup wizard (env, docker, CI, secrets) |
| `mattcopock:prototype` | **DevOps / Setup** | Logic prototyping discipline |
| `mattcopock:code-reviewer` | **Code Quality** | Code review with security scan, quality gates, auto-fix |
| `requesting-code-review` | **Code Quality** | Pre-commit review: security scan, quality gates, auto-fix |
| `simplify-code` | **Code Quality** | Parallel 3-agent cleanup of recent changes |
| `spike` | **Exploration** | Throwaway experiments to validate ideas |
| `systematic-debugging` | **Debugging** | 4-phase root cause debugging |
| `test-driven-development` | **Code Quality** | TDD: RED-GREEN-REFACTOR enforcement |
| `plan` | **Planning** | Write actionable markdown plans to `.hermes/plans/` |
| `dispatching-parallel-agents` | **Superpowers** | Parallel subagents for independent tasks |
| `executing-plans` | **Superpowers** | Execute written plans |
| `finishing-a-development-branch` | **Superpowers** | Complete branch: tests pass, review done, merge ready |
| `receiving-code-review` | **Superpowers** | Process code review feedback |
| `using-git-worktrees` | **Superpowers** | Isolated feature work via git worktrees |
| `verification-before-completion` | **Superpowers** | Verify before claiming done |
| `using-superpowers` | **Superpowers** | Meta-skill: how to use superpowers |
| `brainstorming` | **Superpowers** | Structured brainstorming before creative work |
| `writing-skills` | **Meta** | Author new skills |
| `hermes-agent-skill-authoring` | **Meta** | Author in-repo SKILL.md with validator |
| `understand` | **Codebase Understanding** | Analyze codebase → interactive knowledge graph |
| `understand-chat` | **Codebase Understanding** | Ask questions about codebase |
| `understand-dashboard` | **Codebase Understanding** | Launch interactive web dashboard |
| `understand-diff` | **Codebase Understanding** | Analyze git diffs / PRs |
| `understand-domain` | **Codebase Understanding** | Extract business domain knowledge |
| `understand-explain` | **Codebase Understanding** | Deep-dive explanation of specific feature |
| `understand-figma` | **Codebase Understanding** | Analyze Figma file via REST API |
| `understand-knowledge` | **Codebase Understanding** | Analyze Karpathy-pattern LLM wiki KB |
| `understand-onboard` | **Codebase Understanding** | Generate onboarding guide |
| `ritual` | **Rituals** | Daily focus ritual (morning focus, EOD shutdown) |

---

## Plugins

| Plugin | Description |
|--------|-------------|
| `herdr-agent-state` | Persist agent state across sessions (Hermes plugin) |

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

### Link english-tutor Plugin into Profile

Use helper script when plugin should be symlinked into one Hermes profile. Behavior mirrors cron helper shape, but action is symlink creation, not cron creation.

```bash
make letp-dry-run HERMES_PROFILE_NAME=gintary
make letp HERMES_PROFILE_NAME=gintary
```

Direct script form:

```bash
HERMES_PROFILE_NAME=gintary scripts/link-hermes-plugin.sh list
HERMES_PROFILE_NAME=gintary scripts/link-hermes-plugin.sh link
```

Resulting symlink:

```text
~/.hermes/profiles/<profile>/plugins/english-tutor -> <repo>/hermes-plugins/english-tutor
```

### Load a Skill

```bash
hermes skill load ritual
hermes skill load understand-anything:understand
hermes skill load mattcopock:code-reviewer
```

### Run a Ritual

```bash
hermes skill run ritual
```

---

## Skills vs Plugins vs Profile Config

| Layer | Purpose | Location |
|-------|---------|----------|
| **Profile config** | Model, tools, permissions, toolsets, hooks | `hermes/profile.yaml`, `config.yaml`, `dist.yaml` |
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
```

For english-tutor shortcut:

```bash
make letp HERMES_PROFILE_NAME=gintary
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

- **Track**: `profile.yaml`, `config.yaml`, `dist.yaml`, `hermes-plugins/**`, `skills/**`, `scripts/**`, `README.md`
- **Ignore**: `.git/objects` (git objects), `__pycache__`, `node_modules`, `.env`, `9router/data`, `.hermes/profiles/gintary/{cron,memories,audio_cache,scripts}`, `*.pyc`, `.DS_Store`
- **Never commit**: secrets, API keys, local DBs, cron output, memory DBs

```bash
# Typical commit
git add hermes-plugins/herdr-agent-state skills/ritual
git commit -m "plugin: add herdr-agent-state agent state plugin"
git commit -m "skill: add ritual daily focus skill"
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