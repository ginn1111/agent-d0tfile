## Variant: Tinted chrome

### Design stance
Clone the Hermes skin: chrome surfaces (tab bar, status bars, borders, selection, cursorline) shift to red-tinted darks so the whole window *feels* Cindy, not just its highlights.

### Key choices
- Color: `#1f0a0a` bars, `#3a0d0c` borders/selection, `#8a1f1d` active tab with light text, `#5a1413` focus glow — exact Hermes skin darks
- Code bg stays `#001419` so syntax colours keep contrast
- Interaction: same as other variants

### Trade-offs
- Strong at: strongest identity; matches Hermes TUI 1:1; red accent less shouty because surroundings carry it
- Weak at: needs 4 new hexes outside `solarized-osaka.palette` (breaks palette rule unless added as `cindy_*`); tinted selection lowers contrast in yazi

### Best for
- Running Hermes TUI next to the tools and wanting one continuous surface
