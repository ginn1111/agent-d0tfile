-- Cindy theme: Warm Dusk via mini.base16 (themes/cindy, installed by `make theme-cindy`).
-- Palette: themes/cindy/warm-dusk.palette. Roles: themes/cindy/REGISTRY.md (Neovim).
return {
  "nvim-mini/mini.nvim",
  lazy = false,
  priority = 1000,
  config = function()
    require("mini.base16").setup({
      palette = {
        base00 = "#1d1a17", -- bg
        base01 = "#2a2520", -- surface (statusline, folds)
        base02 = "#3b332a", -- rule (selection)
        base03 = "#807663", -- dim (comments)
        base04 = "#b3a894", -- sub
        base05 = "#d6cbb8", -- fg
        base06 = "#ebe2d2", -- fg_bright
        base07 = "#ebe2d2", -- fg_bright
        base08 = "#cf6b6b", -- err
        base09 = "#e3876a", -- warn
        base0A = "#d8c37a", -- yellow
        base0B = "#a3b371", -- ok (strings)
        base0C = "#86b8a0", -- turquoise
        base0D = "#8fb3b0", -- info (functions)
        base0E = "#b896b8", -- purple (keywords; accent stays focus-only)
        base0F = "#d39aa6", -- pink
      },
      use_cterm = true,
    })
    vim.g.colors_name = "cindy-warm-dusk"
  end,
}
