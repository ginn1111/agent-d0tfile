-- Cindy theme: Bearded Black & Ruby (themes/cindy, installed by `make theme-cindy`).
return {
  "Ferouk/bearded-nvim",
  name = "bearded",
  lazy = false,
  priority = 1000,
  config = function()
    require("bearded").setup({ flavor = "black-&-ruby" })
    vim.cmd.colorscheme("bearded")
  end,
}
