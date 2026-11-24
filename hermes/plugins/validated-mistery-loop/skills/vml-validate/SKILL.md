---
name: vml-validate
description: "Use when user wants validate output against VML acceptance criteria. Check evidence, update kanban/capability/knowledge on pass."
version: 1.0.0
platforms: [linux, macos, windows]
---

# vml-validate

Use to verify active VML work.

## Expected command
- `vml validate`

## Behavior
- Read active kanban card acceptance criteria
- Evaluate output against each criterion
- Report pass/fail per criterion with evidence
- On pass: update `kanban.md`, `capability-map.md`, `knowledge.md`
- Do not re-implement user work
