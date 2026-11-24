---
name: vml-check
description: "Use when user wants VML consistency check. Read-only check for backlinks, kanban invariants, evidence gaps."
version: 1.0.0
platforms: [linux, macos, windows]
---

# vml-check

Use for VML vault consistency review.

## What to inspect
- `goal.md` ↔ `capability-map.md` backlinks
- max one card in `## In Progress`
- done cards must have `Evidence:`
- demonstrated capabilities must have evidence
- `knowledge.md` should backlink completed capabilities

## Expected command
- `vml check`

## Behavior
- Read only
- Report concrete file issues
- Do not mutate VML files
