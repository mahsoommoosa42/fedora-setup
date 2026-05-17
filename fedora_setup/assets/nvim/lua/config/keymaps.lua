local map = vim.keymap.set

-- ── Window navigation (Ctrl+hjkl, same as tmux/Zellij pane nav) ──────────────
map("n", "<C-h>", "<C-w>h", { desc = "Move to left split" })
map("n", "<C-j>", "<C-w>j", { desc = "Move to split below" })
map("n", "<C-k>", "<C-w>k", { desc = "Move to split above" })
map("n", "<C-l>", "<C-w>l", { desc = "Move to right split" })

-- ── Splits ────────────────────────────────────────────────────────────────────
map("n", "<leader>sv", "<cmd>vsplit<CR>",  { desc = "Split vertical" })
map("n", "<leader>sh", "<cmd>split<CR>",   { desc = "Split horizontal" })
map("n", "<leader>se", "<C-w>=",           { desc = "Equal split sizes" })
map("n", "<leader>sx", "<cmd>close<CR>",   { desc = "Close split" })

-- ── Buffer navigation (Shift+h/l, like VS Code tab switching) ────────────────
map("n", "<S-h>", "<cmd>bprevious<CR>", { desc = "Prev buffer" })
map("n", "<S-l>", "<cmd>bnext<CR>",     { desc = "Next buffer" })
map("n", "<leader>bd", "<cmd>bdelete<CR>", { desc = "Close buffer" })

-- ── Better j/k on wrapped lines ───────────────────────────────────────────────
map({ "n", "x" }, "j", "v:count == 0 ? 'gj' : 'j'", { expr = true, silent = true })
map({ "n", "x" }, "k", "v:count == 0 ? 'gk' : 'k'", { expr = true, silent = true })

-- ── Move selected lines up/down ───────────────────────────────────────────────
map("v", "<A-j>", ":m '>+1<CR>gv=gv", { desc = "Move selection down" })
map("v", "<A-k>", ":m '<-2<CR>gv=gv", { desc = "Move selection up" })

-- ── Indentation (stay in visual mode) ────────────────────────────────────────
map("v", "<", "<gv", { desc = "Dedent" })
map("v", ">", ">gv", { desc = "Indent" })

-- ── Clear search highlight ────────────────────────────────────────────────────
map("n", "<Esc>", "<cmd>nohlsearch<CR>")

-- ── Save (Ctrl+S — works with stty -ixon set in shell init) ──────────────────
map({ "n", "i", "v" }, "<C-s>", "<cmd>w<CR><Esc>", { desc = "Save" })

-- ── Find files (Ctrl+P — universally safe through SSH) ───────────────────────
map("n", "<C-p>", "<cmd>Telescope find_files<CR>", { desc = "Find files" })

-- ── Toggle comment (Ctrl+/ — terminal sends <C-_>) ───────────────────────────
map("n", "<C-_>", "gcc", { remap = true, desc = "Toggle comment" })
map("x", "<C-_>", "gc",  { remap = true, desc = "Toggle comment" })

-- ── Files & search ───────────────────────────────────────────────────────────
map("n", "<leader>ff", "<cmd>Telescope find_files<CR>",                    { desc = "Find files" })
map("n", "<leader>fr", "<cmd>Telescope oldfiles<CR>",                      { desc = "Recent files" })
map("n", "<leader>fb", "<cmd>Telescope buffers<CR>",                       { desc = "Buffers" })
map("n", "<leader>fg", "<cmd>Telescope live_grep<CR>",                     { desc = "Live grep" })
map("n", "<leader>fw", "<cmd>Telescope grep_string<CR>",                   { desc = "Grep word under cursor" })
map("n", "<leader>fh", "<cmd>Telescope help_tags<CR>",                     { desc = "Help tags" })
map("n", "<leader>fk", "<cmd>Telescope keymaps<CR>",                       { desc = "Keymaps" })
map("n", "<leader>fc", "<cmd>Telescope commands<CR>",                      { desc = "Commands" })
map("n", "<leader>fd", "<cmd>Telescope diagnostics<CR>",                   { desc = "Diagnostics" })

-- ── File explorer ─────────────────────────────────────────────────────────────
map("n", "<leader>e",  "<cmd>Neotree toggle<CR>",  { desc = "Toggle explorer" })
map("n", "<leader>o",  "<cmd>Neotree reveal<CR>",  { desc = "Reveal file in explorer" })

-- ── LSP (set globally; buffer-local overrides added in lsp.lua on_attach) ────
map("n", "[d", vim.diagnostic.goto_prev, { desc = "Prev diagnostic" })
map("n", "]d", vim.diagnostic.goto_next, { desc = "Next diagnostic" })
map("n", "<leader>ld", vim.diagnostic.open_float, { desc = "Line diagnostics" })

-- ── Git / SCM ─────────────────────────────────────────────────────────────────
map("n", "<leader>gg", "<cmd>Neogit<CR>",                        { desc = "Neogit (SCM)" })
map("n", "<leader>gd", "<cmd>DiffviewOpen<CR>",                  { desc = "Diff view" })
map("n", "<leader>gh", "<cmd>DiffviewFileHistory %<CR>",         { desc = "File history" })
map("n", "<leader>gH", "<cmd>DiffviewFileHistory<CR>",           { desc = "Branch history" })

-- ── Diagnostics panel (Trouble) ───────────────────────────────────────────────
map("n", "<leader>xx", "<cmd>Trouble diagnostics toggle<CR>",           { desc = "Diagnostics panel" })
map("n", "<leader>xl", "<cmd>Trouble lsp toggle<CR>",                   { desc = "LSP refs/defs panel" })
map("n", "<leader>xq", "<cmd>Trouble qflist toggle<CR>",                { desc = "Quickfix panel" })

-- ── DAP (function keys = VS Code parity, reliable through all layers) ────────
map("n", "<F5>",      "<cmd>lua require('dap').continue()<CR>",           { desc = "Debug: Start/Continue" })
map("n", "<F9>",      "<cmd>lua require('dap').toggle_breakpoint()<CR>",  { desc = "Debug: Toggle breakpoint" })
map("n", "<F10>",     "<cmd>lua require('dap').step_over()<CR>",          { desc = "Debug: Step over" })
map("n", "<F11>",     "<cmd>lua require('dap').step_into()<CR>",          { desc = "Debug: Step into" })
map("n", "<S-F11>",   "<cmd>lua require('dap').step_out()<CR>",           { desc = "Debug: Step out" })
map("n", "<leader>db","<cmd>lua require('dap').toggle_breakpoint()<CR>",  { desc = "Toggle breakpoint" })
map("n", "<leader>dB","<cmd>lua require('dap').set_breakpoint(vim.fn.input('Condition: '))<CR>", { desc = "Conditional breakpoint" })
map("n", "<leader>dc","<cmd>lua require('dap').continue()<CR>",           { desc = "Continue" })
map("n", "<leader>do","<cmd>lua require('dap').step_over()<CR>",          { desc = "Step over" })
map("n", "<leader>di","<cmd>lua require('dap').step_into()<CR>",          { desc = "Step into" })
map("n", "<leader>dO","<cmd>lua require('dap').step_out()<CR>",           { desc = "Step out" })
map("n", "<leader>dt","<cmd>lua require('dap').terminate()<CR>",          { desc = "Terminate" })
map("n", "<leader>du","<cmd>lua require('dapui').toggle()<CR>",           { desc = "Toggle DAP UI" })
map("n", "<leader>dr","<cmd>lua require('dap').repl.open()<CR>",          { desc = "DAP REPL" })
