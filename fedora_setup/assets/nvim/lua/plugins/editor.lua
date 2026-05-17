return {
  -- Treesitter: syntax, indent, folding
  {
    "nvim-treesitter/nvim-treesitter",
    build = ":TSUpdate",
    event = { "BufReadPost", "BufNewFile" },
    opts = {
      ensure_installed = {
        "bash", "c", "cmake", "cpp", "css", "dockerfile",
        "gitignore", "go", "html", "javascript", "json", "jsonc",
        "lua", "luadoc", "make", "markdown", "markdown_inline",
        "python", "query", "regex", "rust", "toml", "tsx",
        "typescript", "vim", "vimdoc", "yaml",
      },
      highlight            = { enable = true },
      indent               = { enable = true },
      incremental_selection = {
        enable = true,
        keymaps = {
          init_selection  = "<C-space>",
          node_incremental = "<C-space>",
          scope_incremental = false,
          node_decremental  = "<BS>",
        },
      },
    },
    config = function(_, opts)
      require("nvim-treesitter.configs").setup(opts)
    end,
  },

  -- Fuzzy finder
  {
    "nvim-telescope/telescope.nvim",
    cmd          = "Telescope",
    dependencies = {
      "nvim-lua/plenary.nvim",
      { "nvim-telescope/telescope-fzf-native.nvim", build = "make" },
      "nvim-telescope/telescope-ui-select.nvim",
    },
    opts = function()
      local actions = require("telescope.actions")
      return {
        defaults = {
          mappings = {
            i = {
              ["<C-j>"]   = actions.move_selection_next,
              ["<C-k>"]   = actions.move_selection_previous,
              ["<C-q>"]   = actions.send_selected_to_qflist + actions.open_qflist,
              ["<Esc>"]   = actions.close,
            },
          },
          prompt_prefix   = "  ",
          selection_caret = "  ",
          file_ignore_patterns = {
            ".git/", "node_modules/", "__pycache__/", "target/",
          },
        },
        extensions = {
          ["ui-select"] = { require("telescope.themes").get_dropdown() },
        },
      }
    end,
    config = function(_, opts)
      local t = require("telescope")
      t.setup(opts)
      t.load_extension("fzf")
      t.load_extension("ui-select")
    end,
  },

  -- File explorer (VS Code-style sidebar)
  {
    "nvim-neo-tree/neo-tree.nvim",
    branch       = "v3.x",
    cmd          = "Neotree",
    dependencies = {
      "nvim-lua/plenary.nvim",
      "nvim-tree/nvim-web-devicons",
      "MunifTanjim/nui.nvim",
    },
    opts = {
      filesystem = {
        filtered_items       = { visible = false, hide_dotfiles = false, hide_gitignored = true },
        follow_current_file  = { enabled = true },
        use_libuv_file_watcher = true,
      },
      window = { width = 30 },
      default_component_configs = {
        git_status = {
          symbols = {
            added       = "✚", modified  = "",  deleted    = "✖",
            renamed     = "➜", untracked = "★", ignored    = "◌",
            unstaged    = "✗", staged    = "✓", conflict   = "",
          },
        },
      },
    },
  },

  -- Which-key: keybinding cheat sheet popup
  {
    "folke/which-key.nvim",
    event = "VeryLazy",
    opts = {
      spec = {
        { "<leader>f", group = "Find" },
        { "<leader>g", group = "Git" },
        { "<leader>d", group = "Debug" },
        { "<leader>l", group = "LSP" },
        { "<leader>x", group = "Diagnostics" },
        { "<leader>b", group = "Buffer" },
        { "<leader>s", group = "Splits" },
      },
    },
  },

  -- Autopairs
  {
    "windwp/nvim-autopairs",
    event = "InsertEnter",
    opts  = { check_ts = true },
  },

  -- Comments: gcc (line), gc (motion/visual)
  {
    "numToStr/Comment.nvim",
    event = { "BufReadPost", "BufNewFile" },
    opts  = {},
  },

  -- TODO/FIXME/HACK/NOTE highlight and search
  {
    "folke/todo-comments.nvim",
    dependencies = { "nvim-lua/plenary.nvim" },
    event        = { "BufReadPost", "BufNewFile" },
    opts         = {},
    keys = {
      { "]t", function() require("todo-comments").jump_next() end, desc = "Next todo" },
      { "[t", function() require("todo-comments").jump_prev() end, desc = "Prev todo" },
      { "<leader>ft", "<cmd>TodoTelescope<CR>", desc = "Find todos" },
    },
  },

  -- Trouble: diagnostics / references panel
  {
    "folke/trouble.nvim",
    cmd  = "Trouble",
    opts = { use_diagnostic_signs = true },
  },

  -- Surround: ys, cs, ds
  {
    "kylechui/nvim-surround",
    version = "*",
    event   = "VeryLazy",
    opts    = {},
  },

  -- Flash: fast cursor jump (s in normal/visual)
  {
    "folke/flash.nvim",
    event = "VeryLazy",
    opts  = {},
    keys  = {
      { "s", mode = { "n", "x", "o" }, function() require("flash").jump() end,           desc = "Flash jump" },
      { "S", mode = { "n", "x", "o" }, function() require("flash").treesitter() end,     desc = "Flash treesitter" },
    },
  },

  -- Better text objects (cin(, ca", etc.)
  { "echasnovski/mini.ai",    version = "*", event = "VeryLazy", opts = {} },
  -- Highlight matching words under cursor
  { "RRethy/vim-illuminate",  event = { "BufReadPost", "BufNewFile" } },
}
