# agent-d0tfile

Shared setup for Gin's Hermes agents and the desktop workspace they run in.

## Theme

**Theme Registry**:
The single reference an agent reads before giving any tool Gin's look: it holds the Palette, the Variants, the Roles and one worked Target example per existing tool.
_Avoid_: theme folder, colour config

**Palette**:
The fixed set of named Colours that make up the Black & Ruby look (Bearded Black & Ruby plus Cindy's ruby-tinted additions).
_Avoid_: colour scheme, theme

**Colour**:
One named entry in the Palette with a single solid hex value.
_Avoid_: token, swatch

**Variant**:
A named flavour that points some Roles at different Colours (and may add its own Colours) for one agent's identity; it never changes a Colour's hex. `cindy` (ruby) is worn by the desktop and Cindy; `ginb` (turquoise) by Ginb.
_Avoid_: theme, skin

**Role**:
A tool-neutral job a Colour performs, such as focus border, urgent, or inactive text, mapped to exactly one Colour.
_Avoid_: usage, slot

**Target**:
One tool's config (i3, polybar, rofi, xborders, kitty, Neovim, herdr, a Hermes skin, …) written by hand from Roles and Colours.
_Avoid_: theme file, port

**Tint**:
A Palette Colour with transparency added; it counts as that Colour, not a new one.
_Avoid_: shade, alpha colour

**Stray Colour**:
A solid colour in a Target that is not in the Palette; it must be added to the Palette or replaced. Fully transparent is never a Stray Colour.
_Avoid_: custom colour, one-off
