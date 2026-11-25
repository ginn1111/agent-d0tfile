---
status: approved
scope: THM-5.3 execution order
owner: Gin
---

# Plan — THM-5.3 Recolour desktop to VS Code Dark Modern

Parent plan: `docs/plans/THM-5.md`.

1. Recolour each desktop file by Role, staging only the theme files in d0t_file.
2. Keep dunst and the shader in sync, and list the `vec3` mapping.
3. In agent-d0tfile, remove these Targets from `PENDING_RECOLOUR` and update the Targets row and Worked Targets.
4. Run the drift test and the full tests. Record the evidence.
