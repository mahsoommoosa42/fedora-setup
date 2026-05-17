return {
  -- Mason: install and manage LSP servers + formatters
  {
    "williamboman/mason.nvim",
    build = ":MasonUpdate",
    config = function()
      require("mason").setup({ ui = { border = "rounded" } })

      -- Ensure formatters and tools are installed
      local mr = require("mason-registry")
      mr.refresh(function()
        for _, pkg in ipairs({ "stylua", "prettier", "shfmt", "ruff", "black" }) do
          local p = mr.get_package(pkg)
          if not p:is_installed() then p:install() end
        end
      end)
    end,
  },

  -- Bridge Mason ↔ nvim-lspconfig (manages LSP servers only, not system ones)
  {
    "williamboman/mason-lspconfig.nvim",
    dependencies = { "williamboman/mason.nvim" },
    opts = {
      ensure_installed = { "lua_ls", "ts_ls", "jsonls", "yamlls", "taplo", "marksman" },
    },
  },

  -- LSP configuration
  {
    "neovim/nvim-lspconfig",
    event        = { "BufReadPre", "BufNewFile" },
    dependencies = {
      "williamboman/mason.nvim",
      "williamboman/mason-lspconfig.nvim",
      "hrsh7th/cmp-nvim-lsp",
      { "j-hui/fidget.nvim", opts = {} },
    },
    config = function()
      local lspconfig    = require("lspconfig")
      local capabilities = require("cmp_nvim_lsp").default_capabilities()

      -- Diagnostic appearance (VS Code-style)
      vim.diagnostic.config({
        virtual_text  = { prefix = "●" },
        severity_sort = true,
        float         = { border = "rounded", source = "always" },
        signs         = {
          text = {
            [vim.diagnostic.severity.ERROR] = " ",
            [vim.diagnostic.severity.WARN]  = " ",
            [vim.diagnostic.severity.HINT]  = " ",
            [vim.diagnostic.severity.INFO]  = " ",
          },
        },
      })

      -- Buffer-local LSP keymaps (applied on every LSP attach)
      local on_attach = function(_, bufnr)
        local b = function(keys, func, desc)
          vim.keymap.set("n", keys, func, { buffer = bufnr, desc = "LSP: " .. desc })
        end
        local tel = require("telescope.builtin")
        b("gd",          vim.lsp.buf.definition,      "Go to definition")
        b("gD",          vim.lsp.buf.declaration,      "Go to declaration")
        b("gr",          tel.lsp_references,           "Find references")
        b("gi",          vim.lsp.buf.implementation,   "Go to implementation")
        b("gt",          vim.lsp.buf.type_definition,  "Go to type definition")
        b("K",           vim.lsp.buf.hover,            "Hover documentation")
        b("<C-k>",       vim.lsp.buf.signature_help,   "Signature help")
        b("<leader>rn",  vim.lsp.buf.rename,           "Rename symbol")
        b("<leader>ca",  vim.lsp.buf.code_action,      "Code action")
        b("<leader>ls",  tel.lsp_document_symbols,     "Document symbols")
        b("<leader>lS",  tel.lsp_workspace_symbols,    "Workspace symbols")
        b("<F2>",          vim.lsp.buf.rename,           "Rename symbol")
        b("<F12>",       vim.lsp.buf.definition,       "Go to definition")
        b("<S-F12>",     tel.lsp_references,           "Find all references")
      end

      -- ── System-installed LSPs (not managed by Mason) ──────────────────────
      -- clangd: installed via dnf (clang-tools-extra)
      lspconfig.clangd.setup({
        capabilities = capabilities,
        on_attach    = on_attach,
        cmd          = { "clangd", "--background-index", "--clang-tidy", "--header-insertion=iwyu" },
      })

      -- rust-analyzer: installed via rustup component
      lspconfig.rust_analyzer.setup({
        capabilities = capabilities,
        on_attach    = on_attach,
        settings     = {
          ["rust-analyzer"] = {
            checkOnSave  = { command = "clippy" },
            cargo        = { features = "all" },
            inlayHints   = { enable = true },
            procMacro    = { enable = true },
          },
        },
      })

      -- pyright: installed via uv tool install pyright
      lspconfig.pyright.setup({
        capabilities = capabilities,
        on_attach    = on_attach,
        settings     = {
          pyright = { autoImportCompletion = true },
          python  = {
            analysis = {
              autoSearchPaths    = true,
              diagnosticMode     = "openFilesOnly",
              useLibraryCodeForTypes = true,
            },
          },
        },
      })

      -- ── Mason-managed LSPs ────────────────────────────────────────────────
      require("mason-lspconfig").setup({
        handlers = {
          -- Default: auto-configure all Mason-managed servers
          function(server_name)
            lspconfig[server_name].setup({
              capabilities = capabilities,
              on_attach    = on_attach,
            })
          end,
          -- lua_ls needs extra workspace config for Neovim API
          ["lua_ls"] = function()
            lspconfig.lua_ls.setup({
              capabilities = capabilities,
              on_attach    = on_attach,
              settings     = {
                Lua = {
                  runtime     = { version = "LuaJIT" },
                  workspace   = {
                    checkThirdParty = false,
                    library         = { vim.env.VIMRUNTIME, "${3rd}/luv/library" },
                  },
                  diagnostics = { globals = { "vim" } },
                  telemetry   = { enable = false },
                  format      = { enable = false },
                },
              },
            })
          end,
        },
      })
    end,
  },

  -- Completion engine
  {
    "hrsh7th/nvim-cmp",
    event        = "InsertEnter",
    dependencies = {
      "hrsh7th/cmp-nvim-lsp",
      "hrsh7th/cmp-buffer",
      "hrsh7th/cmp-path",
      "L3MON4D3/LuaSnip",
      "saadparwaiz1/cmp_luasnip",
      "rafamadriz/friendly-snippets",
    },
    config = function()
      local cmp     = require("cmp")
      local luasnip = require("luasnip")
      require("luasnip.loaders.from_vscode").lazy_load()

      local kind_icons = {
        Text = "", Method = "󰆧", Function = "󰊕", Constructor = "",
        Field = "󰇽", Variable = "󰂡", Class = "󰠱", Interface = "",
        Module = "", Property = "󰜢", Unit = "", Value = "󰎠",
        Enum = "", Keyword = "󰌋", Snippet = "", Color = "󰏘",
        File = "󰈙", Reference = "", Folder = "󰉋", EnumMember = "",
        Constant = "󰏿", Struct = "", Event = "", Operator = "󰆕",
        TypeParameter = "󰅲",
      }

      cmp.setup({
        snippet = { expand = function(args) luasnip.lsp_expand(args.body) end },
        window  = {
          completion    = cmp.config.window.bordered(),
          documentation = cmp.config.window.bordered(),
        },
        mapping = cmp.mapping.preset.insert({
          ["<C-b>"]     = cmp.mapping.scroll_docs(-4),
          ["<C-f>"]     = cmp.mapping.scroll_docs(4),
          ["<C-Space>"] = cmp.mapping.complete(),
          ["<C-e>"]     = cmp.mapping.abort(),
          ["<CR>"]      = cmp.mapping.confirm({ select = false }),
          ["<Tab>"]     = cmp.mapping(function(fallback)
            if cmp.visible() then
              cmp.select_next_item()
            elseif luasnip.expand_or_jumpable() then
              luasnip.expand_or_jump()
            else
              fallback()
            end
          end, { "i", "s" }),
          ["<S-Tab>"] = cmp.mapping(function(fallback)
            if cmp.visible() then
              cmp.select_prev_item()
            elseif luasnip.jumpable(-1) then
              luasnip.jump(-1)
            else
              fallback()
            end
          end, { "i", "s" }),
        }),
        sources = cmp.config.sources({
          { name = "nvim_lsp" },
          { name = "luasnip" },
          { name = "path" },
        }, {
          { name = "buffer" },
        }),
        formatting = {
          format = function(entry, item)
            item.kind = string.format("%s %s", kind_icons[item.kind] or "", item.kind)
            item.menu = ({
              nvim_lsp = "[LSP]", luasnip = "[Snip]",
              buffer   = "[Buf]", path    = "[Path]",
            })[entry.source.name]
            return item
          end,
        },
      })
    end,
  },

  -- Auto-formatter (runs on save)
  {
    "stevearc/conform.nvim",
    event = { "BufWritePre" },
    cmd   = { "ConformInfo" },
    opts  = {
      formatters_by_ft = {
        lua        = { "stylua" },
        python     = { "ruff_format", stop_after_first = true },
        rust       = { "rustfmt" },
        c          = { "clang_format" },
        cpp        = { "clang_format" },
        javascript = { "prettier" },
        typescript = { "prettier" },
        json       = { "prettier" },
        yaml       = { "prettier" },
        markdown   = { "prettier" },
        sh         = { "shfmt" },
      },
      format_on_save = { timeout_ms = 500, lsp_fallback = true },
    },
    keys = {
      {
        "<leader>lf",
        function() require("conform").format({ async = true, lsp_fallback = true }) end,
        desc = "Format document",
      },
    },
  },
}
