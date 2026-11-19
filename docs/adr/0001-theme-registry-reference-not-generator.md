# Theme Registry is a reference with a drift test, not a generator

`themes/cindy/` is the Theme Registry for every Target (i3, polybar, rofi, xborders, dunst, kitty, Neovim, herdr, Hermes skins, …), including Targets that live in `~/tools/d0t_file`. Agents read the Registry and write each Target config by hand. A test in this repo fails when any listed Target contains a Stray Colour. Comments count; Tints and fully transparent do not. Targets that are missing on the machine are skipped. We chose this over generating configs from templates. Each tool has its own syntax and needs one-off layout choices. A generator would need a template engine and a template for every tool, and it would stop hand edits. The drift test keeps the colours honest at a much lower cost.

## Consequences

- Cross-repo coupling: the Registry lists absolute Target paths in `~/tools/d0t_file`. Moving a Target means updating the Registry.
- Variants only re-point Roles. A Colour's hex is the same in every Variant, so one Palette can check all Targets.
