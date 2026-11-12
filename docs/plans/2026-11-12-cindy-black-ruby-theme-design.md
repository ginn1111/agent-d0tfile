# Cindy Black & Ruby theme — design

Source: BeardedBear `src/variations/black.ts` `blackAndRuby` (same values in
`Ferouk/bearded-nvim` `palettes/generated.lua`). Chosen look: sketch
`themes/cindy/sketches/004-hybrid` (Bearded syntax + ruby-tinted agent pane/bars).

## Palette (`themes/cindy/black-ruby.palette`, single source of truth)

| Token | Hex | Use |
|---|---|---|
| bg | `#111418` | editor/terminal background |
| bg_alt | `#0c0f11` | tab bars, menus |
| bg_mid | `#0f1215` | floats |
| bg_agent | `#130e11` | Hermes pane, herdr agent pane |
| bar | `#1a0f14` | lualine, Hermes/herdr/yazi status |
| border | `#040506` | splits |
| surface | `#1c2027` | selection, pills |
| rule | `#3a1a26` | Hermes input rule |
| fg | `#bec6d0` | text |
| sub | `#a0acbb` | secondary text |
| dim | `#6b7686` | comments, hints (readable) |
| ghost | `#475262` | blame, line numbers, inactive tabs |
| accent | `#c62f52` | ruby: focus, cursor, prompt, active tab, normal mode |
| err | `#E35535` | errors |
| warn | `#d4770c` | warnings |
| ok | `#00a884` | success, insert mode |
| info | `#11B7D4` | info, functions, paths |
| purple | `#a85ff1` | visual mode, numbers, git branch |
| pink | `#d46ec0` | extra |
| yellow | `#c7910c` | keywords, command mode |
| turquoise | `#38c7bd` | types |
| green_alt | `#3585bb` | extra |

Rule: ruby is UI accent only; errors never use ruby.

## Files (`themes/cindy/`)

```
black-ruby.palette
hermes-skin.yaml      -> ~/.hermes/profiles/cindy/skins/black-ruby-cindy.yaml
kitty.conf            -> ~/.config/kitty/black_ruby.conf (+ include line swap)
nvim/bearded.lua      -> ~/.config/nvim/lua/plugins/bearded.lua (Ferouk/bearded-nvim, flavor "black-&-ruby")
nvim/lualine.lua      -> ~/.config/nvim/lua/plugins/lualine.lua (same pill layout, colors from bearded palette)
yazi-theme.toml       -> ~/.config/yazi/theme.toml
lazygit.yml           -> ~/.config/lazygit/config.yml
herdr.toml            block swapped into ~/.config/herdr/config.toml
starship.toml         palette block swapped into ~/.config/starship.toml (symlink to ~/tools/d0t_file)
```

## Install (`scripts/install-theme-cindy.sh`, `--dry-run`, `--restore`)

Make targets: `theme-cindy`, `theme-cindy-dry-run`, `theme-cindy-restore`.

| Target | Action |
|---|---|
| yazi, lazygit | backup, symlink whole file |
| kitty | symlink `black_ruby.conf`; backup `kitty.conf`; replace active `include *.conf` theme line |
| nvim | symlink `bearded.lua`; `solarized.lua` -> `.bak`; backup + symlink `lualine.lua` |
| Hermes | symlink skin; backup `config.yaml`; set `skin: black-ruby-cindy` |
| herdr, starship | backup; replace content between `# >>> cindy theme` / `# <<< cindy theme` markers (insert on first run, replacing existing theme block) |

- Backup name: `<file>.pre-cindy.<timestamp>`. Starship backup/edit resolves the symlink and edits the d0t_file target.
- Idempotent: re-run with links already correct prints `ok` and changes nothing.
- `--dry-run` prints every link/edit/backup, writes nothing.
- `--restore` puts back the newest `.pre-cindy.*` for each file and removes the created links.
- Tests: Python `unittest` drives the script against a temp `HOME` (dry-run writes nothing; install creates links + backups; second run is a no-op; restore returns original bytes). Picked up by `./init.sh`.

Skipped: generator script, soft variant. Add when a second palette appears.
