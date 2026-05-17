return {
  {
    "mfussenegger/nvim-dap",
    dependencies = {
      -- DAP UI panels
      {
        "rcarriga/nvim-dap-ui",
        dependencies = { "nvim-neotest/nvim-nio" },
        config = function()
          local dap, dapui = require("dap"), require("dapui")
          dapui.setup({
            icons = { expanded = "▾", collapsed = "▸", current_frame = "★" },
            layouts = {
              {
                elements = {
                  { id = "scopes",      size = 0.35 },
                  { id = "breakpoints", size = 0.15 },
                  { id = "stacks",      size = 0.25 },
                  { id = "watches",     size = 0.25 },
                },
                size     = 0.30,
                position = "left",
              },
              {
                elements = {
                  { id = "repl",    size = 0.45 },
                  { id = "console", size = 0.55 },
                },
                size     = 0.27,
                position = "bottom",
              },
            },
          })
          -- Auto open/close UI with debug session
          dap.listeners.after.event_initialized["dapui_config"]  = function() dapui.open() end
          dap.listeners.before.event_terminated["dapui_config"]  = function() dapui.close() end
          dap.listeners.before.event_exited["dapui_config"]      = function() dapui.close() end
        end,
      },

      -- Inline variable values while debugging
      { "theHamsta/nvim-dap-virtual-text", opts = {} },

      -- Mason installs debugpy + codelldb automatically
      {
        "jay-babu/mason-nvim-dap.nvim",
        dependencies = { "williamboman/mason.nvim" },
        opts = {
          ensure_installed = { "debugpy", "codelldb" },
          handlers = {
            -- Default handler: use mason-nvim-dap's built-in setup
            function(config)
              require("mason-nvim-dap").default_setup(config)
            end,
            -- nvim-dap-python owns debugpy; skip mason-nvim-dap's auto-setup
            python = function(_) end,
          },
        },
      },

      -- Python DAP: uses Mason-installed debugpy virtualenv
      {
        "mfussenegger/nvim-dap-python",
        ft = "python",
        config = function()
          local debugpy = vim.fn.stdpath("data") .. "/mason/packages/debugpy/venv/bin/python"
          require("dap-python").setup(debugpy)
          require("dap-python").test_runner = "pytest"
        end,
      },
    },

    config = function()
      local dap = require("dap")

      -- ── C / C++ (codelldb, installed by mason-nvim-dap) ───────────────────
      -- mason-nvim-dap registers the codelldb adapter; we only add configs.
      dap.configurations.cpp = {
        {
          name    = "Launch executable",
          type    = "codelldb",
          request = "launch",
          program = function()
            return vim.fn.input("Executable: ", vim.fn.getcwd() .. "/", "file")
          end,
          cwd           = "${workspaceFolder}",
          stopOnEntry   = false,
          args          = {},
        },
        {
          name    = "Attach to process",
          type    = "codelldb",
          request = "attach",
          pid     = require("dap.utils").pick_process,
          args    = {},
        },
      }
      dap.configurations.c = dap.configurations.cpp

      -- ── Rust (codelldb with LLDB pretty-printers) ─────────────────────────
      dap.configurations.rust = {
        {
          name    = "Launch (Rust)",
          type    = "codelldb",
          request = "launch",
          program = function()
            return vim.fn.input("Executable: ", vim.fn.getcwd() .. "/target/debug/", "file")
          end,
          cwd         = "${workspaceFolder}",
          stopOnEntry = false,
          args        = {},
          initCommands = function()
            -- Load Rust LLDB formatters shipped with rustc
            local sysroot = vim.trim(vim.fn.system("rustc --print sysroot"))
            local script  = sysroot .. "/lib/rustlib/etc/lldb_lookup.py"
            local cmdsfile = sysroot .. "/lib/rustlib/etc/lldb_commands"
            local cmds    = { string.format('command script import "%s"', script) }
            local f = io.open(cmdsfile, "r")
            if f then
              for line in f:lines() do table.insert(cmds, line) end
              f:close()
            end
            return cmds
          end,
        },
      }

      -- Breakpoint signs
      vim.fn.sign_define("DapBreakpoint",          { text = "🔴", texthl = "DapBreakpoint" })
      vim.fn.sign_define("DapBreakpointCondition", { text = "🟡", texthl = "DapBreakpointCondition" })
      vim.fn.sign_define("DapStopped",             { text = "▶",  texthl = "DapStopped",
                                                      linehl = "DapStopped" })
    end,
  },
}
