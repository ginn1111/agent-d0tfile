## Variant: Quiet signal

### Design stance
Keep stock Solarized Osaka semantics; red appears in exactly three "who/where am I" spots: focused border, active-tab text, prompt `◇` (plus cursor line number).

### Key choices
- Color: modes, cwd, selection, search back to stock blue/green/yellow; errors stay red (no re-learning)
- Active tab = dark chip with red text, not red fill
- Interaction: same as other variants

### Trade-offs
- Strong at: calm; zero semantic changes; error = red still means error
- Weak at: identity weaker — glance at yazi/lualine alone and you can't tell Cindy from ginb; red focus border vs red error can collide

### Best for
- Long editing sessions where colour noise costs more than agent identity
