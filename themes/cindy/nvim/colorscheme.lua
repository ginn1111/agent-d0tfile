-- Cindy theme: VS Code Dark Modern via mini.base16 (themes/cindy, installed by `make theme-cindy`).
-- Palette: themes/cindy/vscode-dark-modern.palette. Roles: themes/cindy/REGISTRY.md (Neovim).
return {
  "nvim-mini/mini.nvim",
  lazy = false,
  priority = 1000,
  config = function()
    require("mini.base16").setup({
      palette = {
        base00 = "#1f1f1f", -- bg
        base01 = "#2a2d2e", -- surface (statusline, folds)
        base02 = "#2b2b2b", -- rule (selection)
        base03 = "#6e7681", -- dim
        base04 = "#9d9d9d", -- sub
        base05 = "#cccccc", -- fg
        base06 = "#ffffff", -- fg_bright
        base07 = "#ffffff", -- fg_bright
        base08 = "#f85149", -- err
        base09 = "#cca700", -- warn
        base0A = "#dcdcaa", -- yellow
        base0B = "#2ea043", -- ok
        base0C = "#4ec9b0", -- turquoise
        base0D = "#3794ff", -- info
        base0E = "#c586c0", -- purple
        base0F = "#d16969", -- pink
      },
      use_cterm = true,
    })

    -- VS Code syntax Roles on top of base16 (REGISTRY.md: keyword purple, function yellow,
    -- type turquoise, variable green_alt, string/number/comment syn_*).
    local syntax = {
      Keyword = { fg = "#c586c0" }, -- purple
      Statement = { fg = "#c586c0" },
      Conditional = { fg = "#c586c0" },
      Repeat = { fg = "#c586c0" },
      Exception = { fg = "#c586c0" },
      ["@keyword"] = { fg = "#c586c0" },
      Function = { fg = "#dcdcaa" }, -- yellow
      ["@function"] = { fg = "#dcdcaa" },
      Type = { fg = "#4ec9b0" }, -- turquoise
      ["@type"] = { fg = "#4ec9b0" },
      Identifier = { fg = "#9cdcfe" }, -- green_alt (variables)
      ["@variable"] = { fg = "#9cdcfe" },
      String = { fg = "#ce9178" }, -- syn_string
      ["@string"] = { fg = "#ce9178" },
      Number = { fg = "#b5cea8" }, -- syn_number
      Float = { fg = "#b5cea8" },
      ["@number"] = { fg = "#b5cea8" },
      Comment = { fg = "#6a9955", italic = true }, -- syn_comment
      ["@comment"] = { fg = "#6a9955", italic = true },
    }
    for group, spec in pairs(syntax) do
      vim.api.nvim_set_hl(0, group, spec)
    end
    vim.g.colors_name = "cindy-vscode-dark-modern"
  end,
}
