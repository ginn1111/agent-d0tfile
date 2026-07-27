---
name: vml-start
description: "Use when user wants start work from capability. Create session note and move one kanban card to In Progress."
version: 1.0.0
platforms: [linux, macos, windows]
---

# vml-start

Use to begin work on one capability.

## Expected command
- `vml start "<capability>"`

## Behavior
- Resolve capability from current VML vault
- Create session note from `_session-template.md`
- Move matching kanban card to `## In Progress`
- Refuse when another card already in progress
- Never use Hermes kanban system
