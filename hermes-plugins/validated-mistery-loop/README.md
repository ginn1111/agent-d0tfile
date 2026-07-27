# validated-mistery-loop plugin

Hermes runtime plugin for file-based VML workflows in vault:
`/Users/gin/dev/validated-mastery-loop/`

## Purpose

Add deterministic VML helpers without using Hermes kanban system.

Supported commands:
- `vml check`
- `vml review`
- `vml start "<capability>"`
- `vml validate`
- `vml stress`
- `vml stress "<capability>"`

Bundled plugin skills:
- `validated-mistery-loop:vml-check`
- `validated-mistery-loop:vml-review`
- `validated-mistery-loop:vml-start`
- `validated-mistery-loop:vml-validate`
- `validated-mistery-loop:vml-stress`

## Guarantees

- Uses VML markdown files only.
- Never creates Hermes kanban tasks.
- `check` and `review` are read-only.
- `start` mutates only session note + `kanban.md`.
- `validate` mutates only `kanban.md`, `capability-map.md`, `knowledge.md`, and session notes.
- `stress` questions user first. No full answer before user attempts response.

## Expected VML layout

```text
goals/<goal>/
├── goal.md
├── capability-map.md
├── kanban.md
├── knowledge.md
└── sessions/
    └── _session-template.md
```

Backlink invariants:
- `goal.md` contains `[[capability-map]]`
- `capability-map.md` contains `[[goal]]`

Kanban invariants:
- max one card in `## In Progress`
- done card needs `Evidence:`

## Data model

Minimal internal records:
- `GoalRecord` — goal directory + required files + parsed fields
- `CapabilityRecord` — capability heading + status + evidence + last validated
- `KanbanCard` — section + title + objective + acceptance + evidence
- `SessionRecord` — session note path + linked capability
- `ValidationReport` — per-AC pass/fail report with evidence

## Error policy

Return structured error/result instead of silent fallback for:
- missing VML root
- missing required files
- malformed required headings
- ambiguous active goal
- ambiguous capability match

## Notes

- Plugin name stays `validated-mistery-loop` to match request.
- VML vault path keeps upstream spelling `validated-mastery-loop`.
