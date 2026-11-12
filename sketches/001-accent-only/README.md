## Variant: Accent-only

### Design stance
Solarized Osaka untouched; red takes every role blue used to own. This is what `agent-tool-themes/cindy/` ships today.

### Key choices
- Layout: shared 5-tool mock (herdr tabs/panes, nvim + lualine, yazi, starship)
- Color: surfaces stay teal-dark `#002c38`/`#063540`; red on active tab, focus border, normal mode, cwd, prompt `◇`; orange secondary; magenta errors
- Interaction: click panes (focus), tabs, nvim mode buttons, yazi files (click twice = select), shell run buttons

### Trade-offs
- Strong at: identity obvious at a glance; drop-in swap for ginb/gintary (change one hex)
- Weak at: red everywhere reads alarm-ish; errors moved to magenta, needs re-learning

### Best for
- Agent-per-window setups where you must know *which agent* owns the terminal instantly
