-- Cindy theme: lualine pills on VS Code Dark Modern (themes/cindy, `make theme-cindy`).
return {
  "nvim-lualine/lualine.nvim",
  dependencies = { "nvim-tree/nvim-web-devicons" },
  config = function()
    -- Palette: themes/cindy/vscode-dark-modern.palette (Roles: REGISTRY.md "Neovim")
    local c = {
      bar = "#181818", -- bar
      white = "#ffffff", -- fg_bright: text on filled pills
      fg = "#cccccc", -- fg
      dim = "#6e7681", -- dim
      accent = "#0078d4", -- accent (normal mode fill)
      insert = "#16825d", -- mode_insert
      visual = "#68217a", -- mode_visual
      replace = "#c72e0f", -- mode_replace
      command = "#cc6633", -- mode_command
      terminal = "#0e639c", -- mode_terminal
      green = "#2ea043", -- ok
      yellow = "#dcdcaa", -- yellow
      red = "#f85149", -- err
      cyan = "#4ec9b0", -- turquoise
    }
    local pill = "#2a2d2e" -- surface
    local cap = { left = "", right = "" } -- rounded pill ends

    local function mode_theme(color)
      return {
        a = { fg = c.white, bg = color, gui = "bold" },
        b = { fg = c.fg, bg = pill },
        c = { fg = c.fg, bg = c.bar },
      }
    end

    local theme = {
      normal = mode_theme(c.accent),
      insert = mode_theme(c.insert),
      visual = mode_theme(c.visual),
      replace = mode_theme(c.replace),
      command = mode_theme(c.command),
      terminal = mode_theme(c.terminal),
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
