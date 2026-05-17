return {
  -- Git signs in the gutter (add/change/delete indicators)
  {
    "lewis6991/gitsigns.nvim",
    event = { "BufReadPre", "BufNewFile" },
    opts  = {
      signs = {
        add          = { text = "▎" },
        change       = { text = "▎" },
        delete       = { text = "" },
        topdelete    = { text = "" },
        changedelete = { text = "▎" },
        untracked    = { text = "▎" },
      },
      current_line_blame_opts = { delay = 500 },
      on_attach = function(bufnr)
        local gs  = package.loaded.gitsigns
        local map = function(mode, lhs, rhs, desc)
          vim.keymap.set(mode, lhs, rhs, { buffer = bufnr, desc = desc })
        end

        -- Navigation between hunks
        map("n", "]h", function() gs.next_hunk() end, "Next hunk")
        map("n", "[h", function() gs.prev_hunk() end, "Prev hunk")

        -- Staging / resetting
        map({ "n", "v" }, "<leader>gs", ":Gitsigns stage_hunk<CR>",  "Stage hunk")
        map({ "n", "v" }, "<leader>gr", ":Gitsigns reset_hunk<CR>",  "Reset hunk")
        map("n", "<leader>gS", gs.stage_buffer,       "Stage buffer")
        map("n", "<leader>gu", gs.undo_stage_hunk,    "Undo stage hunk")
        map("n", "<leader>gR", gs.reset_buffer,       "Reset buffer")

        -- Inspect
        map("n", "<leader>gp", gs.preview_hunk,                               "Preview hunk")
        map("n", "<leader>gb", function() gs.blame_line({ full = true }) end,  "Blame line (popup)")
        map("n", "<leader>gB", gs.toggle_current_line_blame,                  "Toggle inline blame")

        -- Text object: ih = inner hunk
        map({ "o", "x" }, "ih", ":<C-U>Gitsigns select_hunk<CR>", "Select hunk")
      end,
    },
  },

  -- Neogit: full interactive SCM panel (like VS Code Source Control)
  {
    "NeogitOrg/neogit",
    cmd          = "Neogit",
    dependencies = {
      "nvim-lua/plenary.nvim",
      "sindrets/diffview.nvim",
      "nvim-telescope/telescope.nvim",
    },
    opts = {
      integrations = { diffview = true, telescope = true },
      graph_style  = "unicode",
    },
  },

  -- Diffview: side-by-side diffs and file history
  {
    "sindrets/diffview.nvim",
    cmd  = { "DiffviewOpen", "DiffviewClose", "DiffviewFileHistory", "DiffviewToggleFiles" },
    opts = {},
  },
}
