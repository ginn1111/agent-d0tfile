# validated-mistery-loop Plugin Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Create Hermes plugin `validated-mistery-loop` that inspects a VML vault at `/Users/gin/dev/validated-mastery-loop/` and registers skills/hooks to support `check`, `review`, `start`, and `validate` workflows.

**Architecture:** Build one Python runtime plugin under `hermes-plugins/validated-mistery-loop/` with hook-based skill registration and file-only VML operations. Plugin reads VML markdown files (`goal.md`, `capability-map.md`, `kanban.md`, `knowledge.md`, `sessions/*`) and exposes deterministic workflow entrypoints without using Hermes kanban APIs.

**Tech Stack:** Hermes plugin system (`plugin.yaml`, `__init__.py`), Python stdlib only, markdown file parsing, existing repo helper script `scripts/link-hermes-plugin.sh`.

---

## Current context / assumptions

- VML repo root: `/Users/gin/dev/validated-mastery-loop/`.
- Repo rules say VML tracking must stay file-based. `RULES.md:13` forbids Hermes kanban for capability tracking.
- Goal-template backlink rules already exist:
  - `goal.md` contains `[[capability-map]]`
  - `capability-map.md` contains `[[goal]]`
- Existing VML structure seen:
  - `goals/<goal>/goal.md`
  - `goals/<goal>/capability-map.md`
  - `goals/<goal>/kanban.md`
  - `goals/<goal>/knowledge.md`
  - `goals/<goal>/sessions/_session-template.md`
- Existing repo plugin patterns seen:
  - metadata in `hermes-plugins/*/plugin.yaml`
  - runtime hooks in `hermes-plugins/*/__init__.py`
  - linking via `scripts/link-hermes-plugin.sh`
- User asked for plugin name `validated-mistery-loop`. Source vault path uses `validated-mastery-loop`. Treat plugin name literally for now; keep typo as requested unless user wants rename.

## Proposed behavior

Plugin should own five operator workflows:

1. **check**
   - Detect missing backlinks:
     - `goal.md` ↔ `capability-map.md`
     - goal/capability ↔ kanban relationship if required by plugin contract
     - `knowledge.md` ↔ done capability cards / completed kanban evidence links
   - Detect structural drift:
     - missing required VML files
     - more than one `In Progress` card
     - Done cards without evidence
     - capability statuses without evidence or missing last-validated fields
   - Return report only. No silent mutation.

2. **review**
   - Find current WIP goal(s)
   - For each active goal, list capabilities and status summary
   - Highlight `Practising`, `Unknown`, `Blocked`, and review-ready items

3. **start**
   - Input: chosen capability
   - Create session file from `sessions/_session-template.md`
   - Add or move corresponding card in goal `kanban.md`
   - Enforce max one `In Progress` card
   - Must not call Hermes kanban tools or create Hermes kanban tasks

4. **validate**
   - Read active goal `kanban.md` acceptance criteria
   - Read output/evidence linked to selected capability or goal artifact
   - Produce per-AC pass/fail report with file-based evidence
   - If pass path chosen, update:
     - kanban status
     - capability status in `capability-map.md`
     - `knowledge.md` with reusable knowledge pack
     - backlinks among goal / capability / knowledge / evidence
   - Must verify only, not re-implement user work

5. **stress**
   - Trigger after `review` or `validate`, or as explicit command
   - Read selected capability output / evidence / knowledge pack
   - Generate stress-test questions that probe edge cases, trade-offs, failure modes, and transfer ability
   - Present questions to user, collect answers, then ask deeper follow-up based on answer quality
   - Escalate from direct recall → application → adversarial/advanced reasoning
   - Save stress result into session note, and optionally capability evidence or knowledge if reusable insight emerges
   - Must question and evaluate; must not provide full solution before user answers

---

## Files likely to change

### In this repo
- Create: `hermes-plugins/validated-mistery-loop/plugin.yaml`
- Create: `hermes-plugins/validated-mistery-loop/__init__.py`
- Create: `hermes-plugins/validated-mistery-loop/README.md`
- Create: `hermes-plugins/validated-mistery-loop/references/stress-session-template.md` (optional, if prompt template helps)
- Modify: `README.md` — plugin add/install usage
- Modify: `RULES.md` — only if repo-level plugin maintenance/verification rules need documenting
- Modify: `tests/test_link_hermes_plugin.py` — if link-script coverage expanded for new plugin fixture name
- Create: `tests/test_validated_mistery_loop_plugin.py`

### In VML vault touched by plugin at runtime
- Read-only for `check` and `review`
- Mutating for `start` and `validate`:
  - `/Users/gin/dev/validated-mastery-loop/goals/*/kanban.md`
  - `/Users/gin/dev/validated-mastery-loop/goals/*/capability-map.md`
  - `/Users/gin/dev/validated-mastery-loop/goals/*/knowledge.md`
  - `/Users/gin/dev/validated-mastery-loop/goals/*/sessions/*.md`

---

## Task 1: Freeze plugin contract from repo reality

**Objective:** Convert user request plus VML conventions into exact plugin I/O contract before code.

**Files:**
- Read: `/Users/gin/dev/validated-mastery-loop/AGENTS.md`
- Read: `/Users/gin/dev/validated-mastery-loop/RULES.md`
- Read: `/Users/gin/dev/validated-mastery-loop/goals/_template/goal.md`
- Read: `/Users/gin/dev/validated-mastery-loop/goals/_template/capability-map.md`
- Read: `/Users/gin/dev/validated-mastery-loop/goals/_template/kanban.md`
- Create: `hermes-plugins/validated-mistery-loop/README.md`

**Step 1: Write contract section in README**

Document:
- plugin purpose
- expected VML root path
- supported commands: `check`, `review`, `start`, `validate`
- required file invariants
- no-Hermes-kanban guarantee
- exact mutation policy per command

**Step 2: Define data model in README**

Specify minimal parsed entities:
- GoalRecord
- CapabilityRecord
- KanbanCard
- SessionRecord
- ValidationReport

**Step 3: Define error policy**

Expected outcomes:
- missing VML root
- missing required files
- malformed markdown sections
- ambiguous active goal
- ambiguous capability match

**Step 4: Commit**

```bash
git add hermes-plugins/validated-mistery-loop/README.md
git commit -m "docs: define validated-mistery-loop plugin contract"
```

---

## Task 2: Add plugin scaffold

**Objective:** Create minimal Hermes plugin skeleton matching existing repo style.

**Files:**
- Create: `hermes-plugins/validated-mistery-loop/plugin.yaml`
- Create: `hermes-plugins/validated-mistery-loop/__init__.py`
- Compare with: `hermes-plugins/english-tutor/plugin.yaml`
- Compare with: `hermes-plugins/herdr-agent-state/__init__.py`

**Step 1: Write failing test for plugin load metadata**

```python
from pathlib import Path
import importlib.util
import yaml


def test_plugin_yaml_declares_validated_mistery_loop_metadata():
    text = Path("hermes-plugins/validated-mistery-loop/plugin.yaml").read_text()
    assert "name: validated-mistery-loop" in text
```

**Step 2: Run test to verify failure**

Run: `python3 -m pytest tests/test_validated_mistery_loop_plugin.py -k metadata -v`
Expected: FAIL — plugin files missing

**Step 3: Write minimal plugin files**

`plugin.yaml` should contain at least:
```yaml
name: validated-mistery-loop
version: 1.0.0
description: Validate and manage file-based VML workflows
provides_hooks:
  - pre_llm_call
```

`__init__.py` should contain:
- module docstring
- `register(ctx)`
- no-op initial hook until command dispatch logic lands

**Step 4: Run test to verify pass**

Run: `python3 -m pytest tests/test_validated_mistery_loop_plugin.py -k metadata -v`
Expected: PASS

**Step 5: Commit**

```bash
git add hermes-plugins/validated-mistery-loop/plugin.yaml hermes-plugins/validated-mistery-loop/__init__.py tests/test_validated_mistery_loop_plugin.py
git commit -m "plugin: scaffold validated-mistery-loop"
```

---

## Task 3: Implement VML discovery helpers

**Objective:** Parse VML goals and required files with stdlib only.

**Files:**
- Modify: `hermes-plugins/validated-mistery-loop/__init__.py`
- Modify: `tests/test_validated_mistery_loop_plugin.py`

**Step 1: Write failing tests for goal discovery**

Test cases:
- finds goals under `goals/*/`
- skips `_template/`
- rejects goals missing `goal.md` or `capability-map.md`
- extracts active goal candidates from kanban state

**Step 2: Run test to verify failure**

Run: `python3 -m pytest tests/test_validated_mistery_loop_plugin.py -k discovery -v`
Expected: FAIL — helpers not implemented

**Step 3: Write minimal implementation**

Add stdlib helpers only:
- `Path.glob()` for goal dirs
- tiny markdown section readers
- `GoalRecord` / `CapabilityRecord` / `KanbanCard` as `dataclass`
- one parser per file type

Leave parser deliberately small. Use exact headings seen in templates.

**Step 4: Run test to verify pass**

Run: `python3 -m pytest tests/test_validated_mistery_loop_plugin.py -k discovery -v`
Expected: PASS

**Step 5: Commit**

```bash
git add hermes-plugins/validated-mistery-loop/__init__.py tests/test_validated_mistery_loop_plugin.py
git commit -m "plugin: add VML discovery helpers"
```

---

## Task 4: Implement `check` report

**Objective:** Report VML structural violations and missing backlinks.

**Files:**
- Modify: `hermes-plugins/validated-mistery-loop/__init__.py`
- Modify: `tests/test_validated_mistery_loop_plugin.py`

**Step 1: Write failing tests for backlink checks**

Cases:
- missing `[[capability-map]]` in `goal.md`
- missing `[[goal]]` in `capability-map.md`
- more than one `In Progress` card
- Done card missing evidence
- capability marked `Demonstrated` without evidence
- knowledge missing backlink to completed capability record

**Step 2: Run test to verify failure**

Run: `python3 -m pytest tests/test_validated_mistery_loop_plugin.py -k check -v`
Expected: FAIL

**Step 3: Write minimal implementation**

Implement pure functions:
- `check_goal_backlinks(goal_dir)`
- `check_kanban_rules(goal_dir)`
- `check_knowledge_links(goal_dir)`
- `build_check_report(vml_root)`

Return structured dict or dataclass. No file writes.

**Step 4: Run test to verify pass**

Run: `python3 -m pytest tests/test_validated_mistery_loop_plugin.py -k check -v`
Expected: PASS

**Step 5: Commit**

```bash
git add hermes-plugins/validated-mistery-loop/__init__.py tests/test_validated_mistery_loop_plugin.py
git commit -m "plugin: add VML consistency checks"
```

---

## Task 5: Implement `review` summary

**Objective:** Produce WIP goal and capability summary from current VML files.

**Files:**
- Modify: `hermes-plugins/validated-mistery-loop/__init__.py`
- Modify: `tests/test_validated_mistery_loop_plugin.py`

**Step 1: Write failing tests for review output**

Cases:
- one active goal with one in-progress card
- no active goal
- multiple candidate goals flagged as ambiguity
- capability list grouped by status

**Step 2: Run test to verify failure**

Run: `python3 -m pytest tests/test_validated_mistery_loop_plugin.py -k review -v`
Expected: FAIL

**Step 3: Write minimal implementation**

Implement:
- `find_active_goals(vml_root)`
- `summarize_capabilities(goal_dir)`
- `build_review_report(vml_root)`

Output should name:
- active goal
- in-progress card
- capability statuses
- blocked/review items

**Step 4: Run test to verify pass**

Run: `python3 -m pytest tests/test_validated_mistery_loop_plugin.py -k review -v`
Expected: PASS

**Step 5: Commit**

```bash
git add hermes-plugins/validated-mistery-loop/__init__.py tests/test_validated_mistery_loop_plugin.py
git commit -m "plugin: add VML review summary"
```

---

## Task 6: Implement `start` workflow without Hermes kanban

**Objective:** From chosen capability, create session note and update file-based kanban.

**Files:**
- Modify: `hermes-plugins/validated-mistery-loop/__init__.py`
- Modify: `tests/test_validated_mistery_loop_plugin.py`
- Read: `/Users/gin/dev/validated-mastery-loop/goals/*/sessions/_session-template.md`

**Step 1: Write failing tests for start flow**

Cases:
- creates timestamped session file from template
- inserts or moves one kanban card to `In Progress`
- keeps at most one `In Progress`
- does not touch Hermes kanban APIs
- refuses ambiguous capability names

**Step 2: Run test to verify failure**

Run: `python3 -m pytest tests/test_validated_mistery_loop_plugin.py -k start -v`
Expected: FAIL

**Step 3: Write minimal implementation**

Implement:
- capability lookup by exact heading match first, fuzzy fallback only if unique
- session filename convention from current date/time
- section-rewrite helper for `kanban.md`
- explicit guard comment or test proving no `kanban_` / Hermes kanban calls used

Add `ponytail:` comment if first pass assumes single-goal mutation path.

**Step 4: Run test to verify pass**

Run: `python3 -m pytest tests/test_validated_mistery_loop_plugin.py -k start -v`
Expected: PASS

**Step 5: Commit**

```bash
git add hermes-plugins/validated-mistery-loop/__init__.py tests/test_validated_mistery_loop_plugin.py
git commit -m "plugin: add VML start workflow"
```

---

## Task 7: Implement `validate` report and state updates

**Objective:** Validate output against kanban acceptance criteria and update VML files when appropriate.

**Files:**
- Modify: `hermes-plugins/validated-mistery-loop/__init__.py`
- Modify: `tests/test_validated_mistery_loop_plugin.py`
- Runtime targets: `/Users/gin/dev/validated-mastery-loop/goals/*/{kanban.md,capability-map.md,knowledge.md}`

**Step 1: Write failing tests for validation report**

Cases:
- parses acceptance criteria from active kanban card
- reports pass/fail per AC with evidence path
- moves card to `Review` or `Done` only when evidence exists
- updates capability status after success
- appends reusable knowledge with backlinks
- leaves files unchanged on failed validation except optional review note

**Step 2: Run test to verify failure**

Run: `python3 -m pytest tests/test_validated_mistery_loop_plugin.py -k validate -v`
Expected: FAIL

**Step 3: Write minimal implementation**

Implement:
- acceptance criteria parser from current kanban card block
- evidence collector from file path / commit hash references
- `ValidationReport` builder
- file update helpers for kanban section move, capability status line, knowledge append, backlink insertion

Keep validation deterministic. No AI scoring.

**Step 4: Run test to verify pass**

Run: `python3 -m pytest tests/test_validated_mistery_loop_plugin.py -k validate -v`
Expected: PASS

**Step 5: Commit**

```bash
git add hermes-plugins/validated-mistery-loop/__init__.py tests/test_validated_mistery_loop_plugin.py
git commit -m "plugin: add VML validation workflow"
```

---

## Task 8: Connect plugin command dispatch

**Objective:** Hook plugin into Hermes runtime so user can trigger workflows safely.

**Files:**
- Modify: `hermes-plugins/validated-mistery-loop/__init__.py`
- Modify: `hermes-plugins/validated-mistery-loop/plugin.yaml`
- Modify: `hermes-plugins/validated-mistery-loop/README.md`

**Step 1: Write failing tests for dispatch behavior**

Cases:
- `check` command routed to report builder
- `review` command routed to summary builder
- `start` command requires capability input
- `validate` command requires active goal/card context
- unrelated prompts ignored

**Step 2: Run test to verify failure**

Run: `python3 -m pytest tests/test_validated_mistery_loop_plugin.py -k dispatch -v`
Expected: FAIL

**Step 3: Write minimal implementation**

Need one concrete dispatch choice. Preferred order:
1. explicit slash-like prompt prefix parsing inside `pre_llm_call`
2. optional helper env vars for VML root override
3. narrow command grammar only

Example accepted inputs:
- `vml check`
- `vml review`
- `vml start "CLI Framework (cobra)"`
- `vml validate`
- `vml stress`
- `vml stress "CLI Framework (cobra)"`

Document exact grammar in README.

**Step 4: Run test to verify pass**

Run: `python3 -m pytest tests/test_validated_mistery_loop_plugin.py -k dispatch -v`
Expected: PASS

**Step 5: Commit**

```bash
git add hermes-plugins/validated-mistery-loop/plugin.yaml hermes-plugins/validated-mistery-loop/__init__.py hermes-plugins/validated-mistery-loop/README.md
git commit -m "plugin: wire validated-mistery-loop command dispatch"
```

---

## Task 9: Implement `stress` questioning workflow

**Objective:** Turn reviewed or validated output into a stress-test dialogue that questions user, evaluates answers, then asks deeper follow-up.

**Files:**
- Modify: `hermes-plugins/validated-mistery-loop/__init__.py`
- Modify: `hermes-plugins/validated-mistery-loop/README.md`
- Create: `hermes-plugins/validated-mistery-loop/references/stress-session-template.md` (optional)
- Modify: `tests/test_validated_mistery_loop_plugin.py`

**Step 1: Write failing tests for stress flow**

Cases:
- `stress` builds questions from reviewed output or validation evidence
- first round asks direct, application, and edge-case questions
- follow-up question changes based on strong vs weak answer
- plugin does not reveal final answer before user attempts response
- plugin stores stress results into current session note
- reusable insight can be appended into `knowledge.md` with backlink

**Step 2: Run test to verify failure**

Run: `python3 -m pytest tests/test_validated_mistery_loop_plugin.py -k stress -v`
Expected: FAIL

**Step 3: Write minimal implementation**

Implement:
- `build_stress_prompt(...)`
- `build_stress_questions(...)`
- `evaluate_stress_answer(...)`
- `build_follow_up_question(...)`
- `record_stress_result(...)`

Question ladder should be deterministic:
1. recall / explain
2. apply to nearby variation
3. edge case / failure mode
4. advanced trade-off or adversarial follow-up based on answer quality

Need explicit rule:
- if answer weak, ask narrower diagnostic follow-up
- if answer strong, ask transfer/trade-off follow-up

**Step 4: Run test to verify pass**

Run: `python3 -m pytest tests/test_validated_mistery_loop_plugin.py -k stress -v`
Expected: PASS

**Step 5: Commit**

```bash
git add hermes-plugins/validated-mistery-loop/__init__.py hermes-plugins/validated-mistery-loop/README.md hermes-plugins/validated-mistery-loop/references/stress-session-template.md tests/test_validated_mistery_loop_plugin.py
git commit -m "plugin: add VML stress questioning workflow"
```

---

## Task 10: Link-script and docs verification

**Objective:** Ensure plugin can be linked into Hermes profile and documented in this setup repo.

**Files:**
- Modify: `README.md`
- Modify: `tests/test_link_hermes_plugin.py` only if needed

**Step 1: Write docs update**

Add plugin to repo examples:
- plugin path
- link command
- optional env var for VML root
- sample usage commands

**Step 2: Run verification commands**

```bash
python3 -m pytest tests/test_link_hermes_plugin.py -v
HERMES_HOME=/tmp/hermes-plugin-test HERMES_PROFILE_NAME=tester PLUGIN_NAME=validated-mistery-loop scripts/link-hermes-plugin.sh list tester validated-mistery-loop
```

Expected:
- pytest PASS
- list output prints source plugin dir and target profile plugin path

**Step 3: Commit**

```bash
git add README.md tests/test_link_hermes_plugin.py
if git diff --cached --quiet; then echo "no doc/test changes"; else git commit -m "docs: add validated-mistery-loop plugin usage"; fi
```

---

## Task 11: End-to-end dry run in isolated Hermes home

**Objective:** Prove plugin links and basic command routing work without touching real profile state.

**Files:**
- No code changes expected
- Temp files under `/tmp/hermes-plugin-test/`

**Step 1: Create isolated Hermes home**

```bash
export HERMES_HOME=/tmp/hermes-plugin-test
rm -rf "$HERMES_HOME"
mkdir -p "$HERMES_HOME/profiles/tester/plugins"
```

**Step 2: Link plugin**

```bash
HERMES_PROFILE_NAME=tester PLUGIN_NAME=validated-mistery-loop scripts/link-hermes-plugin.sh link
```

Expected: symlink created under `$HERMES_HOME/profiles/tester/plugins/validated-mistery-loop`

**Step 3: Smoke test import**

```bash
python3 - <<'PY'
import importlib.util
from pathlib import Path
p = Path('hermes-plugins/validated-mistery-loop/__init__.py')
spec = importlib.util.spec_from_file_location('validated_mistery_loop', p)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
print(hasattr(mod, 'register'))
PY
```

Expected: `True`

**Step 4: If Hermes CLI supports profile-local plugin auto-load, run one smoke command**

```bash
HERMES_PROFILE=tester hermes --profile tester chat -q "vml review"
```

Expected: command recognized or plugin log evidence visible. If runtime contract differs, replace with lowest-level import/dispatch smoke test.

**Step 5: Cleanup**

```bash
rm -rf "$HERMES_HOME"
```

---

## Tests / validation summary

Run targeted checks in this order:

```bash
python3 -m pytest tests/test_validated_mistery_loop_plugin.py -v
python3 -m pytest tests/test_link_hermes_plugin.py -v
HERMES_HOME=/tmp/hermes-plugin-test HERMES_PROFILE_NAME=tester PLUGIN_NAME=validated-mistery-loop scripts/link-hermes-plugin.sh list tester validated-mistery-loop
HERMES_HOME=/tmp/hermes-plugin-test HERMES_PROFILE_NAME=tester PLUGIN_NAME=validated-mistery-loop scripts/link-hermes-plugin.sh link
```

If VML fixture tests need temp data, build them under `tempfile.TemporaryDirectory()` from Python tests, not real vault.

---

## Risks / tradeoffs

- Command surface unclear. Existing examples show hook registration, not explicit custom command registration. Need first implementation to pick one stable trigger grammar.
- Markdown parsing brittle if VML headings drift. Keep parser narrow and template-backed.
- `validate` can over-mutate if evidence matching too loose. Must require explicit evidence references.
- Knowledge backlink rule in user request is underspecified. Need exact backlink target convention in `knowledge.md`.
- Plugin name typo may become permanent API. Confirm later if rename wanted.

## Open questions

1. Should plugin mutate VML files immediately on `validate`, or produce report first and require second confirm step?
2. What exact backlink format should `knowledge.md` use for completed capabilities and done kanban cards?
3. Should active goal detection allow multiple goals with Done-only history, or exactly one goal with live `In Progress`/`Review` work?
4. Should `start` create new card when capability missing from kanban, or fail hard?
5. Do you want plugin command prefix `vml ...`, or another trigger string?

## Recommended implementation notes

- Use stdlib only. No markdown parser dependency.
- Prefer tiny line-based parsers over generic AST.
- Keep plugin pure-function heavy. File writes in thin helpers only.
- Add one small self-check per non-trivial parser path.
- Keep diff local to plugin + tests + docs. No repo-wide refactor.
