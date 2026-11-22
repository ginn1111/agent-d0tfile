-- Cindy theme: lualine pills on Warm Dusk (themes/cindy, `make theme-cindy`).
return {
  "nvim-lualine/lualine.nvim",
  dependencies = { "nvim-tree/nvim-web-devicons" },
  config = function()
    -- Palette: themes/cindy/warm-dusk.palette (Roles: REGISTRY.md "Neovim")
    local c = {
      bar = "#26211c", -- bar
      dark = "#1d1a17", -- bg: text on filled pills
      fg = "#d6cbb8", -- fg
      dim = "#807663", -- dim
      accent = "#d9a05b", -- accent
      green = "#a3b371", -- ok
      purple = "#b896b8", -- purple
      red = "#cf6b6b", -- err
      yellow = "#d8c37a", -- yellow
      cyan = "#86b8a0", -- turquoise
    }
    local pill = "#2a2520" -- surface
    local cap = { left = "", right = "" } -- rounded pill ends

    local function mode_theme(color)
      return {
        a = { fg = c.dark, bg = color, gui = "bold" },
        b = { fg = c.fg, bg = pill },
        c = { fg = c.fg, bg = c.bar },
      }
    end

    local theme = {
      normal = mode_theme(c.accent),
      insert = mode_theme(c.green),
      visual = mode_theme(c.purple),
      replace = mode_theme(c.red),
      command = mode_theme(c.yellow),
      terminal = mode_theme(c.cyan),
      inactive = {
        a = { fg = c.dim, bg = c.bar },
        b = { fg = c.dim, bg = c.bar },
        c = { fg = c.dim, bg = c.bar },
      },
    }

    local function lsp_name()
      local ft = vim.bo.filetype
      for _, client in ipairs(vim.lsp.get_clients({ bufnr = 0 })) do
        if client.config.filetypes and vim.tbl_contains(client.config.filetypes, ft) then
          return client.name
        end
      end
      return "No LSP"
    end

    require("lualine").setup({
      options = {
        theme = theme,
        component_separators = "",
        section_separators = cap,
        globalstatus = true,
      },
      sections = {
        lualine_a = { { "mode", separator = cap, padding = { left = 1, right = 1 } } },
        lualine_b = {
          { "filename", separator = cap },
          { "branch", icon = "", separator = cap },
        },
        lualine_c = {
          {
            "diff",
            symbols = { added = " ", modified = "󰝤 ", removed = " " },
            diff_color = {
              added = { fg = c.green },
              modified = { fg = c.yellow },
              removed = { fg = c.red },
            },
          },
          "%=",
          {
            "diagnostics",
            sources = { "nvim_diagnostic" },
            symbols = { error = " ", warn = " ", info = " " },
          },
        },
        lualine_x = {
          { lsp_name, icon = " ", color = { fg = c.cyan, gui = "bold" } },
          { "filetype", icon_only = true },
        },
        lualine_y = { { "progress", separator = cap } },
        lualine_z = { { "location", separator = cap } },
      },
      inactive_sections = {
        lualine_c = { "filename" },
        lualine_x = { "location" },
      },
    })
  end,
}
