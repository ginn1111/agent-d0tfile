---
name: executing-plans
description: Use when you have a written implementation plan to execute in a separate session with review checkpoints
---

# Executing Plans

## Overview

Load plan, review critically, execute tasks in batches, report for review between batches.

**Core principle:** Batch execution with checkpoints for architect review.

**Announce at start:** "I'm using the executing-plans skill to implement this plan."

## The Process

### Step 0: Propose Plan If None Exists

Before executing, check if a written plan exists for this task.

**If no plan exists:** do NOT jump into terminal commands. Stop and plan:

1. Examine inputs (diff, user request, files to change).
2. Propose a concrete sequence of steps/commits/tasks.
3. Present the plan to your partner (short markdown or bullet list).
4. **Wait for confirmation** before executing anything.

This applies to multi-step work: commit splitting, refactors, migrations — anywhere the user asked for a strategy. The user wants to see the breakdown and approve it first.

**If plan exists:** proceed to Step 1 below.

### Step 1: Load and Review Plan
1. Read plan file
2. Review critically - identify any questions or concerns about the plan
3. If concerns: Raise them with your human partner before starting
4. If no concerns: Create TodoWrite and proceed

### Step 2: Execute Batch
**Default: First 3 tasks**

For each task:
1. Mark as in_progress
2. Follow each step exactly (plan has bite-sized steps)
3. Run verifications as specified
4. Mark as completed

### Step 3: Report
When batch complete:
- Show what was implemented
- Show verification output
- Say: "Ready for feedback."

### Step 4: Continue
Based on feedback:
- Apply changes if needed
- Execute next batch
- Repeat until complete

### Step 5: Complete Development

After all tasks complete and verified:
- Announce: "I'm using the finishing-a-development-branch skill to complete this work."
- **REQUIRED SUB-SKILL:** Use superpowers:finishing-a-development-branch
- Follow that skill to verify tests, present options, execute choice

## Dirty Repo / Partial-Baseline Rule

When executing a plan inside a repo that already has unrelated failures or WIP:
- First identify whether failures come from touched files or unrelated baseline noise.
- Still drive touched files to clean verification, even if global `tsc`/lint stays red from unrelated files.
- Record exact remaining blocker path(s) and keep them separate from your changes.
- Prefer targeted verification that proves your work is sound (`rg` filtered `tsc`, focused tests, relevant build path) before escalating.
- Do not "fix everything" outside plan scope just to get a green global run unless the unrelated failure blocks the requested deliverable.

## Refactor Execution Pattern

For large feature-slice refactors driven by a spec:
1. Land low-risk extraction first (constants, pure utils, tests).
2. Add feature entrypoints/re-exports early so imports can move before deeper rewiring.
3. Rewire page/container to consume extracted state and derived hooks next.
4. Remove duplicate in-file logic only after replacement path compiles.
5. Re-run targeted verification after each chunk so regressions stay local.

## When to Stop and Ask for Help

**STOP executing immediately when:**
- Hit a blocker mid-batch (missing dependency, test fails, instruction unclear)
- Plan has critical gaps preventing starting
- You don't understand an instruction
- Verification fails repeatedly

**Ask for clarification rather than guessing.**

## When to Revisit Earlier Steps

**Return to Review (Step 1) when:**
- Partner updates the plan based on your feedback
- Fundamental approach needs rethinking

**Don't force through blockers** - stop and ask.

**Don't skip Step 0** — jumping straight to execution without proposing a plan is the most common mistake in commit-split and refactor-sequencing tasks. If you catch yourself about to run a terminal command before your partner has seen the breakdown, stop and backtrack to Step 0.

## Remember
- Review plan critically first
- Follow plan steps exactly
- Don't skip verifications
- Reference skills when plan says to
- Between batches: just report and wait
- Stop when blocked, don't guess
- Step 0 first: plan then confirm before touching terminal
- See `references/commit-splitting-strategy.md` for commit-split workflow
