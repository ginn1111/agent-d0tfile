# Expand ginb Profile Diagram Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Update `docs/hermes-agents.drawio` so the diagram represents the scanned `ginb` Hermes profile using the existing hand-drawn node-and-connector format.

**Architecture:** Keep the existing `ginb profile` node as the root. Add sibling category nodes for the profile's configured skills, tools, MCP servers, and enabled plugins, then connect the root to each category with the same orthogonal/sketch styling already used in the file. Preserve the diagram as a single-page `.drawio` document and avoid changing unrelated profile configuration.

**Tech Stack:** draw.io XML (`mxGraphModel`), drawio MCP, Hermes profile YAML.

---

## Current context and assumptions

- Target diagram: `docs/hermes-agents.drawio`, page `Page-1` (`uq2qvB4eQwqUj0iV4dqc`).
- The current page contains a hand-drawn `ginb profile` root and category nodes labeled `SKills`, `Tools`, and `Mcps`.
- The current page also contains dangling edges from undefined `profile`/`g1`–`g13` IDs. The implementation should remove or repair these stale edges so the final diagram has no undefined endpoints.
- The scanned profile source is `/Users/gin/.hermes/profiles/ginb/config.yaml`.
- Profile facts to represent:
  - Skill sources: `${HOME}/.agents/skills`, `/home/aioz/personal/gin-harness/skills`, `/Users/gin/dev/gin-harness/skills`.
  - CLI toolsets include browser, clarify, code execution, context engine, cronjob, delegation, file, kanban, codegraph MCP, memory, session search, skills, terminal, todo, and vision.
  - Enabled MCP servers: `codegraph` and `drawio`.
  - Enabled plugins: `english-tutor` and `gin-inference`.
  - Profile timezone: `Asia/Bangkok`; model/provider: `gpt-5.6-luna` / `openai-codex`.
- Do not copy secrets, runtime state, caches, or the full profile contents into the diagram.

## Proposed diagram content

Use concise labels so the diagram remains readable:

- Root: `ginb profile`
- Existing description text: retain, but correct only obvious spelling in the diagram if needed (`planning`, `deployment`).
- Category nodes:
  - `Skills`
  - `Tools`
  - `MCPs`
  - `Plugins`
- Category detail text should summarize, rather than enumerate every inherited skill/tool:
  - Skills: `External skill sources\nGinflow + development workflows`
  - Tools: `CLI toolsets\nTerminal, file, kanban, delegation, memory, vision`
  - MCPs: `codegraph\ndrawio`
  - Plugins: `english-tutor\ngin-inference`
- Optional profile metadata node, only if space permits: `Asia/Bangkok\ngpt-5.6-luna\nopenai-codex`. Prefer omitting it if it makes the diagram crowded; the four category nodes are the required scope.

## Step-by-step implementation

### Task 1: Re-read the authoritative inputs

**Objective:** Confirm the exact current diagram XML and profile configuration before editing.

**Files:**
- Read: `docs/hermes-agents.drawio`
- Read: `/Users/gin/.hermes/profiles/ginb/config.yaml`

**Steps:**
1. Use drawio MCP `list_pages` for `docs/hermes-agents.drawio`.
2. Use drawio MCP `get_page` for `Page-1`.
3. Re-read the `ginb` profile YAML and confirm only non-secret configuration is used.
4. Record the existing node IDs/styles so new nodes match the current `Architects Daughter` sketch format.

**Verification:** The page remains single-page and the profile facts above are confirmed from live tool output.

### Task 2: Design stable node IDs and layout

**Objective:** Define a collision-free, readable layout before changing the XML.

**Files:**
- Modify: `docs/hermes-agents.drawio`

**Steps:**
1. Retain the existing `ginb profile` node and its description node.
2. Reuse or rename the existing category nodes only where safe; normalize visible labels to `Skills` and `MCPs`.
3. Add a `Plugins` category node using the same vertex style, dimensions, and font as the existing category nodes.
4. Place the four category nodes in a row or compact grid below the root, with enough separation for connectors.
5. Add detail nodes only if the existing diagram's visual density supports them; otherwise place the summary in the category node's `value`.
6. Ensure every edge's `source` and `target` points to an actual cell ID. Remove the stale `profile` → `g1`–`g13` edges unless corresponding nodes are intentionally added.

**Verification:** The planned cell graph has one root, four required category nodes, and no dangling edge endpoints.

### Task 3: Apply the diagram update through drawio MCP

**Objective:** Write the updated `Page-1` XML while preserving the `.drawio` container and other pages.

**Steps:**
1. Use drawio MCP `set_page` with the revised `mxGraphModel` XML.
2. Preserve the existing page ID/name and the original hand-drawn style attributes (`sketch=1`, `hachureGap`, `jiggle`, `curveFitting`, and `Architects Daughter`).
3. Do not modify `/Users/gin/.hermes/profiles/ginb/config.yaml` or any runtime profile files.

**Verification:** `set_page` succeeds and reports the target page update without changing page count.

### Task 4: Validate the resulting diagram

**Objective:** Confirm the saved diagram is structurally complete and visually faithful to the requested format.

**Steps:**
1. Use drawio MCP `list_pages` and confirm `Page-1` still exists.
2. Use drawio MCP `get_page` and inspect every vertex and edge.
3. Check that required labels are present: `ginb profile`, `Skills`, `Tools`, `MCPs`, and `Plugins`.
4. Check that `codegraph`, `drawio`, `english-tutor`, and `gin-inference` are represented.
5. Check that no edge references an undefined source or target ID.
6. Use a read-only XML parser or equivalent inspection if needed to validate the cell graph; do not introduce a test artifact into the repository.
7. Review `git diff -- docs/hermes-agents.drawio` and confirm only the diagram changed.

**Expected result:** One readable page, matching hand-drawn formatting, with the ginb profile categories and configured MCP/plugin components represented and no dangling edges.

## Files likely to change

- Modify: `docs/hermes-agents.drawio`
- Do not modify: `/Users/gin/.hermes/profiles/ginb/config.yaml` or any profile runtime/cache files.

## Tests and validation

- Drawio MCP `list_pages` before and after the update.
- Drawio MCP `get_page` after the update.
- XML cell-reference check: every edge `source` and `target` must resolve to a vertex cell.
- `git diff --check -- docs/hermes-agents.drawio`.
- `git status --short` to confirm scope.

No application test suite is expected for this documentation/diagram-only change.

## Risks, tradeoffs, and open questions

- The profile exposes many inherited skills and tools; listing all of them would make the diagram unreadable. Use grouped summaries and name only the configured MCPs/plugins explicitly.
- The existing dangling edges may be remnants of an earlier diagram version. Default is to remove them because they cannot render meaningful relationships; preserve them only if inspection reveals intended nodes elsewhere on the page.
- The exact final placement should follow the existing canvas style and avoid overlapping the description node. If the diagram editor shows overlap, prioritize readable spacing over preserving the current extreme coordinates.
- No user clarification is required under the stated default: add the profile's configured categories and enabled integrations in the same hand-drawn format.
